"""Outshift QRNG entropy source — Cisco quantum random numbers (DRBG post-processed)."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx

from opendivination.config import configured_remote_source_api_key
from opendivination.types import SourceHealth

# ── Error hierarchy (ported from outshift-qrng-sdk/src/errors.ts) ─────


class OutshiftError(Exception):
    """Base error for all Outshift QRNG API errors."""

    def __init__(self, message: str, status_code: int = 0, detail: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class AuthError(OutshiftError):
    """401 — invalid or missing API key."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or "Unauthorized: invalid or missing API key", 401, detail)


class ForbiddenError(OutshiftError):
    """403 — expired API key."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or "Forbidden: API key expired", 403, detail)


class ValidationError(OutshiftError):
    """422 — validation error in request."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or "Validation error", 422, detail)


class RateLimitError(OutshiftError):
    """429 — rate limited."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or "Rate limit exceeded", 429, detail)


class ServerError(OutshiftError):
    """500+ — server error."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or "Internal server error", 500, detail)


# ── Constants ─────────────────────────────────────────────────────────

_BASE_URL = "https://api.qrng.outshift.com"
_ENDPOINT = "/api/v1/random_numbers"
_MAX_RETRIES = 3
_CONFIG_PATH = Path.home() / ".config" / "qrng" / "outshift.json"
_CACHE_FETCH_SIZE = 1024  # bytes to prefetch per API call


# ── Source ────────────────────────────────────────────────────────────


class OutshiftSource:
    """Outshift QRNG — Cisco quantum random numbers (DRBG post-processed).

    Network entropy source using the Outshift QRNG REST API.
    API key is resolved from (in order):

      1. Constructor argument
      2. ``OUTSHIFT_API_KEY`` environment variable
      3. ``~/.config/qrng/outshift.json`` config file
    """

    name: str = "outshift"
    source_type: str = "network"
    is_quantum: bool = True
    description: str = "Outshift QRNG \u2014 Cisco quantum random numbers (DRBG post-processed)"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key: str | None = (
            api_key
            or os.environ.get("OUTSHIFT_API_KEY")
            or configured_remote_source_api_key("outshift")
            or self._read_config()
        )
        self._cache: bytes = b""
        self._bytes_served: int = 0
        self._last_error: str | None = None

    # ── EntropySource protocol ────────────────────────────────────

    async def get_bytes(self, n: int) -> bytes:
        """Return *n* quantum-random bytes from the Outshift API."""
        if self._api_key is None:
            raise AuthError("No API key available")

        while len(self._cache) < n:
            needed = max(n - len(self._cache), _CACHE_FETCH_SIZE)
            self._cache += await self._fetch_bytes(needed)

        result = self._cache[:n]
        self._cache = self._cache[n:]
        self._bytes_served += n
        return result

    async def is_available(self) -> bool:
        """Check if API key is configured and service is reachable.

        Must complete well within the 2-second registry timeout.
        """
        if self._api_key is None:
            return False
        try:
            # Minimal request: 1 sample of 8 bits
            await self._request(
                {"number_of_bits": 8, "number_of_samples": 1},
                timeout=1.5,
            )
            return True
        except Exception:  # noqa: BLE001
            return False

    async def health_check(self) -> SourceHealth:
        """Detailed health probe."""
        if self._api_key is None:
            return SourceHealth(
                available=False,
                quality_score=0.0,
                last_error="No API key configured",
                bytes_served=self._bytes_served,
            )
        try:
            available = await self.is_available()
            return SourceHealth(
                available=available,
                quality_score=0.85 if available else 0.0,  # DRBG post-processed
                last_error=self._last_error,
                bytes_served=self._bytes_served,
            )
        except Exception as exc:  # noqa: BLE001
            self._last_error = str(exc)
            return SourceHealth(
                available=False,
                quality_score=0.0,
                last_error=self._last_error,
                bytes_served=self._bytes_served,
            )

    # ── Internals ─────────────────────────────────────────────────

    async def _fetch_bytes(self, n: int) -> bytes:
        """Fetch *n* bytes from the API and return raw bytes."""
        body = {"number_of_bits": n * 8, "number_of_samples": 1}
        resp = await self._request(body)
        return self._parse_bytes(resp, n)

    async def _request(
        self,
        body: dict[str, Any],
        *,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        """POST to the QRNG API with exponential backoff retry.

        Ported from ``outshift-qrng-sdk/src/client.ts`` ``request()`` method.
        Retries on network errors, 429 (rate limit), and 5xx (server errors).
        Non-retryable errors (400, 401, 403, 422) raise immediately.
        """
        last_error: Exception | None = None
        url = f"{_BASE_URL}{_ENDPOINT}"
        assert self._api_key is not None

        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(_MAX_RETRIES + 1):
                # Exponential backoff: 1 s, 2 s, 4 s (capped at 10 s)
                if attempt > 0:
                    delay = min(1.0 * (2 ** (attempt - 1)), 10.0)
                    await asyncio.sleep(delay)

                try:
                    resp = await client.post(
                        url,
                        json=body,
                        headers={
                            "Content-Type": "application/json",
                            "x-id-api-key": self._api_key,
                        },
                    )
                except httpx.HTTPError as exc:
                    last_error = OutshiftError(f"Network error: {exc}")
                    self._last_error = str(last_error)
                    continue  # retry on network error

                # Success
                if resp.is_success:
                    self._last_error = None
                    return resp.json()  # type: ignore[no-any-return]

                # Parse error detail
                try:
                    error_body = resp.json()
                except Exception:  # noqa: BLE001
                    error_body = {}
                detail = (
                    error_body.get("detail")
                    or error_body.get("message")
                    or resp.reason_phrase
                    or f"HTTP {resp.status_code}"
                )

                # Retryable: 429 or 5xx
                if resp.status_code == 429 or resp.status_code >= 500:
                    last_error = (
                        RateLimitError(detail) if resp.status_code == 429 else ServerError(detail)
                    )
                    self._last_error = str(last_error)
                    continue

                # Non-retryable: raise immediately
                self._last_error = detail
                self._throw_for_status(resp.status_code, detail)

        raise last_error or ServerError("Request failed after retries")

    @staticmethod
    def _throw_for_status(status: int, detail: str) -> None:
        """Map HTTP status code to the specific exception type."""
        if status == 400:
            raise OutshiftError(detail, 400, detail)
        if status == 401:
            raise AuthError(detail)
        if status == 403:
            raise ForbiddenError(detail)
        if status == 422:
            raise ValidationError(detail)
        if status == 429:
            raise RateLimitError(detail)
        raise OutshiftError(detail, status, detail)

    @staticmethod
    def _parse_bytes(resp: dict[str, Any], n: int) -> bytes:
        """Extract byte data from the API JSON response."""
        numbers = resp.get("random_numbers", [])
        if not numbers:
            raise OutshiftError("Empty response from API")

        # Collect bytes: each entry may have decimal or hexadecimal fields
        raw = bytearray()
        for entry in numbers:
            hex_val = entry.get("hexadecimal")
            dec_val = entry.get("decimal")
            if hex_val:
                raw.extend(bytes.fromhex(hex_val))
            elif dec_val is not None:
                value = int(dec_val)
                byte_len = max(1, (value.bit_length() + 7) // 8)
                raw.extend(value.to_bytes(byte_len, "big"))

        if len(raw) < n:
            raise OutshiftError(f"Insufficient data: requested {n} bytes, got {len(raw)}")
        return bytes(raw[:n])

    @staticmethod
    def _read_config() -> str | None:
        """Read API key from ``~/.config/qrng/outshift.json``."""
        try:
            data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            return data.get("apiKey") or data.get("api_key") or None
        except (OSError, json.JSONDecodeError, KeyError):
            return None
