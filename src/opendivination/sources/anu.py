"""ANU QRNG entropy source — photon vacuum fluctuation via quantum.anu.edu.au."""

from __future__ import annotations

import os
import time

import httpx

from opendivination.types import SourceHealth

# ANU QRNG API endpoint — returns uint8 arrays of quantum random bytes
_ANU_ENDPOINT = "https://qrng.anu.edu.au/API/jsonI.php"

# Fetch this many bytes per API call, serve from cache until depleted
_CACHE_FETCH_SIZE = 1024


class ANUSource:
    """ANU Quantum Random Number Generator.

    Uses photon vacuum fluctuation to generate true quantum random numbers.
    The ANU API returns uint8 arrays sourced from measurements of quantum
    vacuum fluctuations. Note: ANU applies post-processing (hash-based
    conditioning) to the raw measurements.

    Bytes are fetched in bulk (_CACHE_FETCH_SIZE at a time) and served from
    an internal cache to minimise API calls.
    """

    name: str = "anu"
    source_type: str = "network"
    is_quantum: bool = True
    description: str = "ANU QRNG \u2014 photon vacuum fluctuation (quantum.anu.edu.au)"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ANU_API_KEY")
        self._cache: bytes = b""
        self._bytes_served: int = 0
        self._last_success: float | None = None
        self._last_error: str | None = None
        self._rate_limited: bool = False

    # ── core protocol ────────────────────────────────────────────

    async def get_bytes(self, n: int) -> bytes:
        """Return *n* quantum random bytes, refilling the cache as needed."""
        while len(self._cache) < n:
            await self._refill_cache()

        result = self._cache[:n]
        self._cache = self._cache[n:]
        self._bytes_served += n
        return result

    async def is_available(self) -> bool:
        """Probe the ANU API (2 s timeout). Returns False on any error."""
        if self._rate_limited:
            # Optimistic reset — try again on next call after returning False once
            self._rate_limited = False
            return False

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(
                    _ANU_ENDPOINT,
                    params={"length": 1, "type": "uint8"},
                    headers=self._auth_headers(),
                )
                if resp.status_code == 429:
                    self._rate_limited = True
                    self._last_error = "rate limited (429)"
                    return False
                resp.raise_for_status()
                data = resp.json()
                return bool(data.get("success"))
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            return False

    async def health_check(self) -> SourceHealth:
        """Report current health state."""
        available = await self.is_available()
        return SourceHealth(
            available=available,
            quality_score=0.9 if available else 0.0,
            last_error=self._last_error,
            bytes_served=self._bytes_served,
        )

    # ── internals ────────────────────────────────────────────────

    async def _refill_cache(self) -> None:
        """Fetch a fresh batch of bytes from the ANU API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    _ANU_ENDPOINT,
                    params={"length": _CACHE_FETCH_SIZE, "type": "uint8"},
                    headers=self._auth_headers(),
                )
                if resp.status_code == 429:
                    self._rate_limited = True
                    self._last_error = "rate limited (429)"
                    raise RuntimeError("ANU API rate limited (429)")
                resp.raise_for_status()

                payload = resp.json()
                if not payload.get("success") or "data" not in payload:
                    msg = "ANU API returned unsuccessful response"
                    self._last_error = msg
                    raise RuntimeError(msg)

                self._cache += bytes(payload["data"])
                self._last_success = time.monotonic()
                self._last_error = None
                self._rate_limited = False

        except httpx.HTTPStatusError as exc:
            self._last_error = f"HTTP {exc.response.status_code}"
            raise
        except httpx.HTTPError as exc:
            self._last_error = str(exc)
            raise

    def _auth_headers(self) -> dict[str, str]:
        """Return auth headers if an API key is configured."""
        if self._api_key:
            return {"x-api-key": self._api_key}
        return {}
