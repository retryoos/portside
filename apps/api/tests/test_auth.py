"""Tests for A2 auth: the dev-auth bypass, the missing-token 401, the /me
endpoint, and owner-scoping at the store level.

The real Cognito JWKS path is only reachable with a provisioned pool, so it is
not exercised here; we cover the dev path, the 401 guard, and owner isolation.
"""

from __future__ import annotations

import asyncio
import types
from pathlib import Path
from typing import Iterator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from laytimely_api import auth, main as main_mod
from laytimely_api.auth import DEV_USER_ID, Principal, get_current_user
from laytimely_api.db.engine import create_all, make_engine, make_sessionmaker
from laytimely_api.fixtures import demo_voyage_fixture
from laytimely_api.storage import InMemoryStore, SqlVoyageStore


def test_dev_auth_returns_fixed_dev_user() -> None:
    """With dev_auth on (the default with no Cognito configured), the dependency
    returns the dev principal without inspecting any header."""
    user = asyncio.run(get_current_user(authorization=None))
    assert isinstance(user, Principal)
    assert user.id == DEV_USER_ID


def test_missing_bearer_is_401_when_auth_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        auth,
        "settings",
        types.SimpleNamespace(
            dev_auth=False,
            cognito_jwks_url=None,
            cognito_issuer=None,
            cognito_client_id=None,
        ),
    )
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(authorization=None))
    assert exc.value.status_code == 401


@pytest.fixture
def client() -> Iterator[TestClient]:
    # InMemoryStore + dev auth: endpoints resolve to the dev user with no token.
    store = InMemoryStore()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(main_mod, "store", store)
        with TestClient(main_mod.app) as c:
            yield c


def test_me_endpoint_returns_dev_user(client: TestClient) -> None:
    resp = client.get("/me")
    assert resp.status_code == 200
    assert resp.json()["id"] == DEV_USER_ID


def test_delete_then_404(client: TestClient) -> None:
    # Seeded demo voyages exist (owned by the dev user); delete one, then 404.
    listing = client.get("/voyages").json()
    assert listing, "expected seeded voyages"
    vid = listing[0]["id"]
    assert client.delete(f"/voyages/{vid}").status_code == 204
    assert client.get(f"/voyages/{vid}").status_code == 404


def _url(tmp_path: Path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'auth.db'}"


def test_owner_scoping_in_sql_store(tmp_path: Path) -> None:
    async def go() -> tuple[list, object, bool, bool]:
        engine = make_engine(_url(tmp_path))
        await create_all(engine)
        store = SqlVoyageStore(make_sessionmaker(engine))
        await store.ensure_user("user-a")
        await store.ensure_user("user-b")
        await store.save(demo_voyage_fixture("v_a"), owner_user_id="user-a")
        await store.save(demo_voyage_fixture("v_b"), owner_user_id="user-b")

        a_list = await store.list("user-a")
        cross_load = await store.load("v_b", "user-a")  # not user-a's -> None
        del_wrong = await store.delete("v_b", "user-a")  # wrong owner -> False
        del_right = await store.delete("v_b", "user-b")  # owner -> True
        await engine.dispose()
        return a_list, cross_load, del_wrong, del_right

    a_list, cross_load, del_wrong, del_right = asyncio.run(go())
    assert [s.id for s in a_list] == ["v_a"]
    assert cross_load is None
    assert del_wrong is False
    assert del_right is True
