"""Qbert QRNG entropy source — quantum tunneling via Crypta Labs Firefly hardware."""

from __future__ import annotations

import asyncio
import os

import httpx

from opendivination.types import SourceHealth

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_QBERT_BASE = "https://qbert.cipherstone.co"
_QBERT_RANDOM_URL = f"{_QBERT_BASE}/api/v1/random"
_QBERT_HEALTH_URL = f"{_QBERT_BASE}/health"
_CACHE_SIZE = 1024  # bytes to prefetch on first request
_MAX_RETRIES = 5
_INITIAL_BACKOFF_S = 1.0  # doubles each retry


class QbertSource:
    """Qbert QRNG — quantum tunneling via Crypta Labs Firefly hardware (invite-only).

    Implements the ``EntropySource`` protocol.  Entropy is fetched over HTTPS
    from the Cipherstone Qbert API and served from a local byte cache that is
    lazily filled on the first ``get_bytes`` call (cache-on-connect pattern).

    The source is only available when a valid ``QBERT_API_KEY`` environment
    variable (or constructor argument) is set **and** the remote health-check
    endpoint responds successfully.
    """

    name: str = "qbert"
    source_type: str = "network"
    is_quantum: bool = True
    description: str = (
        "Qbert QRNG — quantum tunneling via Crypta Labs Firefly hardware (invite-only)"
    )

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key: str | None = api_key or os.environ.get("QBERT_API_KEY")
        self._cache: bytes = b""
        self._bytes_served: int = 0
        self._last_error: str | None = None
        self._last_device: str = ""

    # ------------------------------------------------------------------
    # EntropySource protocol
    # ------------------------------------------------------------------

    async def get_bytes(self, n: int) -> bytes:
        """Return *n* quantum-random bytes, refilling the cache as needed."""
        if self._api_key is None:
            raise RuntimeError("QBERT_API_KEY is not set")

        # Lazy cache-on-connect: fill on first request
        if len(self._cache) < n:
            needed = max(n, _CACHE_SIZE)
            self._cache += await self._fetch_bytes(needed)

        result = self._cache[:n]
        self._cache = self._cache[n:]
        self._bytes_served += n
        return result

    async def is_available(self) -> bool:
        """Return True only if an API key is configured and the remote is healthy.

        Must complete well within the 2-second registry timeout.
        """
        if self._api_key is None:
            return False

        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                resp = await client.get(
                    _QBERT_HEALTH_URL,
                    headers={"X-API-Key": self._api_key},
                )
                return bool(resp.status_code == 200)
        except (httpx.HTTPError, OSError):
            return False

    async def health_check(self) -> SourceHealth:
        """Detailed health probe with device metadata."""
        if self._api_key is None:
            return SourceHealth(
                available=False,
                quality_score=0.0,
                last_error="QBERT_API_KEY not set",
                bytes_served=self._bytes_served,
            )

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(
                    _QBERT_HEALTH_URL,
                    headers={"X-API-Key": self._api_key},
                )
                if resp.status_code == 200:
                    self._last_error = None
                    return SourceHealth(
                        available=True,
                        quality_score=1.0,  # raw quantum, no conditioning
                        last_error=None,
                        bytes_served=self._bytes_served,
                    )
                self._last_error = f"HTTP {resp.status_code}"
        except (httpx.HTTPError, OSError) as exc:
            self._last_error = str(exc)

        return SourceHealth(
            available=False,
            quality_score=0.0,
            last_error=self._last_error,
            bytes_served=self._bytes_served,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_bytes(self, length: int) -> bytes:
        """Fetch *length* uint8 values from the Qbert API with retry + backoff."""
        assert self._api_key is not None

        last_exc: BaseException | None = None
        backoff = _INITIAL_BACKOFF_S

        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(_MAX_RETRIES):
                try:
                    resp = await client.get(
                        _QBERT_RANDOM_URL,
                        params={"type": "uint8", "length": length},
                        headers={"X-API-Key": self._api_key},
                    )

                    # --- Rate-limit handling (429) ---
                    if resp.status_code == 429:
                        retry_after = resp.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after is not None else backoff
                        backoff = min(backoff * 2, 60.0)
                        if attempt < _MAX_RETRIES - 1:
                            await asyncio.sleep(delay)
                            continue
                        raise httpx.HTTPStatusError(
                            "Rate limited (429) after retries",
                            request=resp.request,
                            response=resp,
                        )

                    resp.raise_for_status()

                    # --- Track device header ---
                    device = resp.headers.get("X-QRNG-Device", "")
                    if device:
                        self._last_device = device

                    # --- Parse JSON array of uint8 values ---
                    payload = resp.json()
                    data = payload.get("data", payload) if isinstance(payload, dict) else payload

                    return bytes(data)

                except (httpx.HTTPError, OSError, ValueError, TypeError) as exc:
                    last_exc = exc
                    self._last_error = str(exc)
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * 2, 60.0)

        raise RuntimeError(f"Qbert API request failed after {_MAX_RETRIES} retries: {last_exc}")

    @property
    def last_device(self) -> str:
        """The ``X-QRNG-Device`` header value from the most recent fetch."""
        return self._last_device
