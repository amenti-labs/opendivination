"""CSPRNG entropy source using os.urandom — always-available fallback."""

from __future__ import annotations

import os

from opendivine.types import SourceHealth


class CSPRNGSource:
    """Cryptographically secure PRNG using os.urandom.

    This is the always-available fallback source. It is NOT quantum —
    quality_score is 0.5 to reflect this honestly.
    """

    name: str = "csprng"
    source_type: str = "software"
    is_quantum: bool = False
    description: str = "OS cryptographic PRNG (os.urandom) — software fallback, not quantum"

    async def get_bytes(self, n: int) -> bytes:
        """Return n cryptographically random bytes from os.urandom."""
        return os.urandom(n)

    async def is_available(self) -> bool:
        """CSPRNG is always available."""
        return True

    async def health_check(self) -> SourceHealth:
        """CSPRNG is always healthy."""
        return SourceHealth(
            available=True,
            quality_score=0.5,  # Honest: not quantum
            last_error=None,
            bytes_served=0,
        )
