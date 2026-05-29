"""Object storage for uploaded voyage PDFs (A3).

The uploaded CP/NOR/SoF PDFs are persisted to durable blob storage so they
survive a restart and can be re-fetched/audited later. Production uses S3;
local dev/tests use a filesystem-backed store, so the feature works with no AWS
(non-blocking) and going live is a config swap (set S3_BUCKET).

The *bytes* live in object storage; the per-voyage *metadata* (role, key,
content-type, size) is recorded relationally via the VoyageStore (see
``db/models.VoyageDocumentRow``). ``StoredDocument`` is the internal record;
``VoyageDocumentInfo`` is the client-facing projection (no raw key).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from .settings import settings


class StoredDocument(BaseModel):
    role: str  # "cp" | "nor" | "sof"
    object_key: str
    content_type: str
    size_bytes: int


class VoyageDocumentInfo(BaseModel):
    role: str
    content_type: str
    size_bytes: int


def build_key(voyage_id: str, role: str, prefix: str = "") -> str:
    parts = [p for p in (prefix.strip("/"), "voyages", voyage_id, f"{role}.pdf") if p]
    return "/".join(parts)


@runtime_checkable
class ObjectStore(Protocol):
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    async def get(self, key: str) -> bytes | None: ...


class LocalObjectStore:
    """Filesystem-backed store for dev/tests (no AWS needed)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def _path(self, key: str) -> Path:
        return self._root / key

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(_write)

    async def get(self, key: str) -> bytes | None:
        path = self._path(key)

        def _read() -> bytes | None:
            return path.read_bytes() if path.exists() else None

        return await asyncio.to_thread(_read)


class S3ObjectStore:
    """S3-backed store. boto3 is imported lazily so dev/tests don't load it."""

    def __init__(self, bucket: str, region: str | None) -> None:
        self._bucket = bucket
        self._region = region
        self._client = None

    def _get_client(self):  # noqa: ANN202
        if self._client is None:
            import boto3

            self._client = boto3.client("s3", region_name=self._region)
        return self._client

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        client = self._get_client()
        await asyncio.to_thread(
            client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    async def get(self, key: str) -> bytes | None:
        client = self._get_client()

        def _read() -> bytes | None:
            try:
                resp = client.get_object(Bucket=self._bucket, Key=key)
            except client.exceptions.NoSuchKey:
                return None
            return resp["Body"].read()

        return await asyncio.to_thread(_read)


def make_object_store() -> ObjectStore:
    """S3 when a bucket is configured, otherwise the local filesystem store."""
    if settings.s3_bucket:
        return S3ObjectStore(settings.s3_bucket, settings.s3_region)
    return LocalObjectStore(settings.objects_dir)
