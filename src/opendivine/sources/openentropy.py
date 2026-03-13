"""OpenEntropy hardware QRNG source for OpenDivine.

Wraps the ``openentropy.EntropyPool`` API to provide hardware-sourced
entropy from any platform-available source (camera noise, audio noise,
sensor jitter, etc.).  The ``openentropy`` package is optional — this
module degrades gracefully when it is not installed.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, cast

from opendivine.types import SourceHealth

logger = logging.getLogger("opendivine")

# ---------------------------------------------------------------------------
# Import guard — no crash when openentropy is not installed
# ---------------------------------------------------------------------------

EntropyPool: Any

try:
    # pyright: ignore[reportMissingImports]
    from openentropy import EntropyPool as _EntropyPool  # type: ignore[import-not-found]

    EntropyPool = _EntropyPool

    _OPENENTROPY_AVAILABLE = True
except ImportError:
    EntropyPool = None
    _OPENENTROPY_AVAILABLE = False


class OpenEntropySource:
    """Hardware entropy via the ``openentropy`` library.

    Uses ``EntropyPool.auto()`` to auto-discover platform-available entropy
    sources (camera noise, audio noise, sensor jitter, etc.) and exposes
    them through the standard ``EntropySource`` interface.

    The ``openentropy`` package must be installed separately::

        pip install openentropy
    """

    name: str = "openentropy"
    source_type: str = "hardware"
    is_quantum: bool = True
    description: str = "openentropy hardware QRNG (60+ sources via PyO3 bindings)"

    def __init__(self, conditioning: str = "sha256") -> None:
        """Initialize the OpenEntropy source.

        Args:
            conditioning: Conditioning mode for raw entropy.
                One of ``"raw"``, ``"vonneumann"``, or ``"sha256"`` (default).
        """
        self._conditioning = conditioning
        self._pool = None
        if _OPENENTROPY_AVAILABLE:
            with contextlib.suppress(Exception):
                self._pool = EntropyPool.auto()

    async def get_bytes(self, n: int) -> bytes:
        """Return exactly *n* random bytes from OpenEntropy hardware sources.

        Collects entropy from all available sources in parallel, then
        draws *n* bytes with the configured conditioning mode.

        Raises:
            RuntimeError: If openentropy is not installed, no pool is
                available, or collection yields 0 bytes.
        """
        if not _OPENENTROPY_AVAILABLE or self._pool is None:
            raise RuntimeError(
                "openentropy is not available — install with: pip install openentropy"
            )

        try:
            self._pool.collect_all(parallel=True, timeout=2.0)
            raw = self._pool.get_bytes(n, conditioning=self._conditioning)
            if raw is None or len(raw) == 0:
                raise RuntimeError(
                    "openentropy collect_all() returned 0 bytes — "
                    "no hardware entropy sources produced data"
                )
            return bytes(raw)
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"openentropy entropy collection failed: {e}") from e

    async def is_available(self) -> bool:
        """Whether OpenEntropy has at least one working source.

        Returns ``False`` immediately when the ``openentropy`` package is
        not installed.  Otherwise probes ``EntropyPool.auto()`` with a
        2-second timeout.
        """
        if not _OPENENTROPY_AVAILABLE:
            return False
        try:
            pool = await asyncio.wait_for(asyncio.to_thread(EntropyPool.auto), timeout=2.0)
            return cast(int, pool.source_count) > 0
        except (asyncio.TimeoutError, Exception):
            return False

    async def health_check(self) -> SourceHealth:
        """Return health status for this source.

        Returns ``SourceHealth(available=False, quality_score=0.0)`` when
        the ``openentropy`` package is not installed.
        """
        if not _OPENENTROPY_AVAILABLE:
            return SourceHealth(
                available=False,
                quality_score=0.0,
                last_error="openentropy package not installed",
            )
        try:
            available = await self.is_available()
            return SourceHealth(
                available=available,
                quality_score=0.95 if available else 0.0,
                last_error=None if available else "no entropy sources detected",
            )
        except Exception as e:
            return SourceHealth(
                available=False,
                quality_score=0.0,
                last_error=str(e),
            )
