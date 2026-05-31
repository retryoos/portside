"""Single egress adapter for the legal subsystem.

Every outbound HTTP call (EUR-Lex today; BAILII later) goes through
``OutboundClient.get`` so we have one place that logs, rate-limits, caches,
and respects ``settings.legal_*_live`` flags. Tests never touch the network:
when the corresponding ``_live`` flag is off, the adapter raises
``LiveCallDisabled`` instead of attempting a request.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger("portside_api.legal.outbound")


class LiveCallDisabled(RuntimeError):
    """Raised when a live tool is invoked while the corresponding settings flag
    is off. The caller treats this as a soft miss (return empty results) so the
    surrounding agent loop is unaffected."""


@dataclass(frozen=True)
class CacheEntry:
    body: bytes
    fetched_at: float
    status_code: int


class OutboundClient:
    """Per-process, asyncio-safe HTTP client wrapper.

    Constructed lazily; one instance per integration (one for EUR-Lex, one for
    BAILII later). Implements:

    - A simple token-bucket rate limit (``min_interval_s`` between requests).
    - A bounded LRU response cache keyed by (method, URL). 30-day default TTL
      is appropriate for case law and EU regulations, which do not change in-
      place.
    - One sentinel mechanism for "live disabled": construct with ``live=False``
      to make every ``get`` raise ``LiveCallDisabled``.
    """

    def __init__(
        self,
        base_url: str,
        *,
        live: bool,
        min_interval_s: float = 0.2,
        cache_ttl_s: float = 60 * 60 * 24 * 30,
        cache_size: int = 256,
        timeout_s: float = 8.0,
        user_agent: str = "Laytimely/1.0 (+legal-subsystem)",
    ) -> None:
        self._base_url = base_url
        self._live = live
        self._min_interval_s = min_interval_s
        self._cache_ttl_s = cache_ttl_s
        self._cache_size = cache_size
        self._timeout_s = timeout_s
        self._user_agent = user_agent

        self._cache: dict[tuple[str, str], CacheEntry] = {}
        self._last_request_at: float = 0.0
        self._lock = asyncio.Lock()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def live(self) -> bool:
        return self._live

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get(self, url: str, **params: object) -> tuple[int, bytes]:
        """Issue a GET against ``url``. Returns (status, body).

        Raises ``LiveCallDisabled`` when ``live=False``. Caches successful
        responses for ``cache_ttl_s``; on cache hit, no request is sent.
        """
        if not self._live:
            raise LiveCallDisabled(
                f"outbound GET to {url} blocked: live flag is off"
            )

        # Normalise the cache key including the sorted params so different
        # query orderings hash to the same entry.
        key_url = httpx.URL(url).copy_merge_params(params)
        cache_key = ("GET", str(key_url))

        async with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None and (time.monotonic() - cached.fetched_at) < self._cache_ttl_s:
                logger.debug("outbound cache hit: %s", key_url)
                return cached.status_code, cached.body

            elapsed = time.monotonic() - self._last_request_at
            if elapsed < self._min_interval_s:
                await asyncio.sleep(self._min_interval_s - elapsed)

            if self._client is None:
                self._client = httpx.AsyncClient(
                    base_url=self._base_url,
                    headers={"User-Agent": self._user_agent},
                    timeout=self._timeout_s,
                )
            response = await self._client.get(str(key_url))
            self._last_request_at = time.monotonic()
            logger.info(
                "outbound GET %s -> %s (%d bytes)",
                key_url,
                response.status_code,
                len(response.content),
            )

            if response.status_code < 400:
                if len(self._cache) >= self._cache_size:
                    # Evict the oldest entry. Stable across orderings because
                    # CPython dicts preserve insertion order.
                    self._cache.pop(next(iter(self._cache)))
                self._cache[cache_key] = CacheEntry(
                    body=response.content,
                    fetched_at=time.monotonic(),
                    status_code=response.status_code,
                )
            return response.status_code, response.content
