"""OpenEntropy-backed entropy sources for OpenDivination.

OpenDivination treats ``openentropy`` as a namespace:

- ``openentropy`` means the pooled OpenEntropy collector
- ``openentropy:<name>`` means a specific named OpenEntropy source

This keeps provenance honest. The aggregate pool is not inherently quantum,
while some named OpenEntropy sources, such as ``qcicada``, are.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import parse_qsl, urlencode

from opendivination.types import SourceHealth, SourceInfo

logger = logging.getLogger("opendivination")

EntropyPool: Any
detect_available_sources: Any

try:
    import openentropy as _openentropy

    EntropyPool = _openentropy.EntropyPool
    detect_available_sources = _openentropy.detect_available_sources
    _OPENENTROPY_AVAILABLE = True
except ImportError:
    EntropyPool = None
    detect_available_sources = None
    _OPENENTROPY_AVAILABLE = False


_OPENENTROPY_NAMESPACE = "openentropy"
_OPENENTROPY_QUANTUM_SELECTORS = frozenset({"qcicada"})
_OPENENTROPY_ALLOWED_CONDITIONING = frozenset({"raw", "vonneumann", "vn", "von_neumann", "sha256"})
_QCICADA_ALLOWED_MODES = frozenset({"raw", "sha256", "samples"})
_SELECTOR_AVAILABILITY_RETRIES = 3
_SELECTOR_AVAILABILITY_RETRY_DELAY_SECONDS = 0.35
_QCICADA_ENV_LOCK = threading.Lock()


@dataclass(frozen=True)
class OpenEntropySourceSpec:
    selector: str | None
    conditioning: str
    device_mode: str | None
    canonical_name: str


def _canonical_name(selector: str | None) -> str:
    if selector is None:
        return _OPENENTROPY_NAMESPACE
    return f"{_OPENENTROPY_NAMESPACE}:{selector}"


def _default_conditioning(selector: str | None) -> str:
    # OpenDivination treats QCicada as a direct quantum-noise source, so the
    # convenience selector defaults to raw pool conditioning unless overridden.
    if selector == "qcicada":
        return "raw"
    return "sha256"


def _default_device_mode(selector: str | None) -> str | None:
    if selector == "qcicada":
        return "raw"
    return None


def _normalize_conditioning(conditioning: str) -> str:
    normalized = conditioning.strip().lower()
    if normalized not in _OPENENTROPY_ALLOWED_CONDITIONING:
        raise ValueError(
            "invalid openentropy conditioning "
            f"'{conditioning}'; expected raw|vonneumann|vn|von_neumann|sha256"
        )
    if normalized in {"vn", "von_neumann"}:
        return "vonneumann"
    return normalized


def _normalize_qcicada_mode(mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in _QCICADA_ALLOWED_MODES:
        raise ValueError(
            f"invalid qcicada mode '{mode}'; expected raw|sha256|samples"
        )
    return normalized


def _requested_name_with_query(base_name: str, parameters: list[tuple[str, str]]) -> str:
    if not parameters:
        return base_name
    return f"{base_name}?{urlencode(parameters)}"


def _canonical_parameters(
    selector: str | None,
    *,
    conditioning: str,
    device_mode: str | None,
) -> list[tuple[str, str]]:
    if selector == "qcicada":
        return [
            ("conditioning", conditioning),
            ("mode", device_mode or "raw"),
        ]

    ordered_params: list[tuple[str, str]] = []
    if conditioning != "sha256":
        ordered_params.append(("conditioning", conditioning))
    if device_mode is not None:
        ordered_params.append(("mode", device_mode))
    return ordered_params


def parse_openentropy_source_spec(requested: str) -> OpenEntropySourceSpec | None:
    base_name, _, query = requested.partition("?")
    selector: str | None
    if base_name == _OPENENTROPY_NAMESPACE:
        selector = None
    elif base_name.startswith(f"{_OPENENTROPY_NAMESPACE}:"):
        selector = base_name.split(":", 1)[1] or None
    elif base_name in _OPENENTROPY_QUANTUM_SELECTORS:
        selector = base_name
    else:
        return None

    query_items = parse_qsl(query, keep_blank_values=False)
    if not query_items:
        conditioning = _default_conditioning(selector)
        device_mode = _default_device_mode(selector)
        return OpenEntropySourceSpec(
            selector=selector,
            conditioning=conditioning,
            device_mode=device_mode,
            canonical_name=_requested_name_with_query(
                _canonical_name(selector),
                _canonical_parameters(
                    selector,
                    conditioning=conditioning,
                    device_mode=device_mode,
                ),
            ),
        )

    params = dict(query_items)
    unknown = sorted(set(params) - {"conditioning", "mode"})
    if unknown:
        raise ValueError(
            "unsupported openentropy source parameters: "
            + ", ".join(unknown)
        )

    conditioning = _normalize_conditioning(
        params.get("conditioning", _default_conditioning(selector))
    )
    device_mode = params.get("mode")
    if device_mode is not None:
        if selector != "qcicada":
            raise ValueError("source parameter 'mode' is only supported for qcicada")
        device_mode = _normalize_qcicada_mode(device_mode)
    elif selector == "qcicada":
        device_mode = "raw"

    ordered_params = _canonical_parameters(
        selector,
        conditioning=conditioning,
        device_mode=device_mode,
    )

    return OpenEntropySourceSpec(
        selector=selector,
        conditioning=conditioning,
        device_mode=device_mode,
        canonical_name=_requested_name_with_query(
            _canonical_name(selector),
            ordered_params,
        ),
    )


def _selector_is_quantum(selector: str | None) -> bool:
    return selector in _OPENENTROPY_QUANTUM_SELECTORS


def _selector_description(selector: str | None, detected: dict[str, Any] | None = None) -> str:
    if selector is None:
        return (
            "openentropy pooled hardware entropy (mixed host/device sources; "
            "may include quantum sources if attached)"
        )
    if detected is not None and detected.get("description"):
        return (
            f"openentropy named source '{selector}' — "
            f"{cast(str, detected['description'])}"
        )
    return f"openentropy named source '{selector}'"


def _safe_detect_available_sources() -> list[dict[str, Any]]:
    if not _OPENENTROPY_AVAILABLE or detect_available_sources is None:
        return []
    try:
        detected = detect_available_sources()
    except Exception:
        return []
    if not isinstance(detected, list):
        return []
    normalized: list[dict[str, Any]] = []
    for entry in detected:
        if isinstance(entry, dict):
            normalized.append(entry)
    return normalized


def _detected_source_map() -> dict[str, dict[str, Any]]:
    detected = _safe_detect_available_sources()
    mapping: dict[str, dict[str, Any]] = {}
    for entry in detected:
        name = entry.get("name")
        if isinstance(name, str) and name:
            mapping[name] = entry
    return mapping


@contextlib.contextmanager
def _temporary_qcicada_mode(mode: str | None) -> Iterator[None]:
    if mode is None:
        yield
        return
    with _QCICADA_ENV_LOCK:
        had_value = "QCICADA_MODE" in os.environ
        previous = os.environ.get("QCICADA_MODE")
        os.environ["QCICADA_MODE"] = mode
        try:
            yield
        finally:
            if had_value and previous is not None:
                os.environ["QCICADA_MODE"] = previous
            else:
                os.environ.pop("QCICADA_MODE", None)


def discover_openentropy_source_infos() -> list[SourceInfo]:
    """Return currently detected named OpenEntropy sources."""
    detected = _detected_source_map()
    infos: list[SourceInfo] = []
    for selector in sorted(detected):
        entry = detected[selector]
        infos.append(
            SourceInfo(
                name=_canonical_name(selector),
                source_type="hardware",
                is_quantum=_selector_is_quantum(selector),
                description=_selector_description(selector, detected=entry),
                backend=_OPENENTROPY_NAMESPACE,
                selector=selector,
                selection_mode="named_source",
                available=True,
                quality_score=0.95 if _selector_is_quantum(selector) else 0.8,
            )
        )
    return infos


class OpenEntropySource:
    """Entropy source backed by the optional ``openentropy`` package."""

    source_type: str = "hardware"

    def __init__(
        self,
        conditioning: str = "sha256",
        *,
        selector: str | None = None,
        device_mode: str | None = None,
        requested_name: str | None = None,
    ) -> None:
        self._conditioning = _normalize_conditioning(conditioning)
        self._selector = selector
        if device_mode is not None and selector != "qcicada":
            raise ValueError("device_mode is only supported for the qcicada selector")
        self._device_mode = (
            _normalize_qcicada_mode(device_mode) if device_mode is not None else None
        )
        self.name: str = requested_name or _canonical_name(selector)
        self.is_quantum: bool = _selector_is_quantum(selector)
        self.description: str = _selector_description(
            selector,
            detected=_detected_source_map().get(selector) if selector is not None else None,
        )
        self._pool = None
        if _OPENENTROPY_AVAILABLE:
            with contextlib.suppress(Exception), _temporary_qcicada_mode(self._device_mode):
                self._pool = EntropyPool.auto()

    @property
    def selector(self) -> str | None:
        return self._selector

    @property
    def conditioning(self) -> str:
        return self._conditioning

    @property
    def device_mode(self) -> str | None:
        return self._device_mode

    @classmethod
    def from_selector(
        cls,
        selector: str,
        *,
        conditioning: str = "sha256",
        device_mode: str | None = None,
        requested_name: str | None = None,
    ) -> OpenEntropySource:
        return cls(
            conditioning=conditioning,
            selector=selector,
            device_mode=device_mode,
            requested_name=requested_name,
        )

    async def get_bytes(self, n: int) -> bytes:
        """Return exactly *n* entropy bytes from OpenEntropy."""
        if not _OPENENTROPY_AVAILABLE or self._pool is None:
            raise RuntimeError(
                "openentropy is not available — install with: pip install openentropy"
            )

        try:
            if self._selector is None:
                self._pool.collect_all(parallel=True, timeout=2.0)
                if self._conditioning == "raw" and hasattr(self._pool, "get_raw_bytes"):
                    raw = self._pool.get_raw_bytes(n)
                else:
                    raw = self._pool.get_bytes(n, conditioning=self._conditioning)
            else:
                if self._conditioning == "raw" and hasattr(self._pool, "get_source_raw_bytes"):
                    raw = self._pool.get_source_raw_bytes(self._selector, n)
                else:
                    raw = self._pool.get_source_bytes(
                        self._selector,
                        n,
                        conditioning=self._conditioning,
                    )
            if raw is None or len(raw) == 0:
                raise RuntimeError(
                    "openentropy returned 0 bytes — "
                    "no entropy sources produced data"
                )
            return bytes(raw)
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"openentropy entropy collection failed: {exc}") from exc

    async def is_available(self) -> bool:
        """Whether this OpenEntropy selector is currently available."""
        if not _OPENENTROPY_AVAILABLE:
            return False
        try:
            if self._selector is None:
                for attempt in range(_SELECTOR_AVAILABILITY_RETRIES):
                    pool = await asyncio.wait_for(
                        asyncio.to_thread(EntropyPool.auto),
                        timeout=2.0,
                    )
                    if cast(int, pool.source_count) > 0:
                        return True
                    if attempt < (_SELECTOR_AVAILABILITY_RETRIES - 1):
                        await asyncio.sleep(_SELECTOR_AVAILABILITY_RETRY_DELAY_SECONDS)
                return False
            for attempt in range(_SELECTOR_AVAILABILITY_RETRIES):
                detected = await asyncio.wait_for(
                    asyncio.to_thread(_detected_source_map),
                    timeout=2.0,
                )
                if self._selector in detected:
                    return True
                if attempt < (_SELECTOR_AVAILABILITY_RETRIES - 1):
                    await asyncio.sleep(_SELECTOR_AVAILABILITY_RETRY_DELAY_SECONDS)
            return False
        except (asyncio.TimeoutError, Exception):
            return False

    async def health_check(self) -> SourceHealth:
        """Return health status for this source."""
        if not _OPENENTROPY_AVAILABLE:
            return SourceHealth(
                available=False,
                quality_score=0.0,
                last_error="openentropy package not installed",
            )
        try:
            available = await self.is_available()
            if self._selector is None:
                quality_score = 0.8 if available else 0.0
            else:
                quality_score = 0.95 if self.is_quantum and available else 0.8 if available else 0.0
            return SourceHealth(
                available=available,
                quality_score=quality_score,
                last_error=None if available else "requested openentropy selector unavailable",
            )
        except Exception as exc:
            return SourceHealth(
                available=False,
                quality_score=0.0,
                last_error=str(exc),
            )


def resolve_openentropy_source_candidates(requested: str) -> Iterator[OpenEntropySource]:
    """Yield plausible OpenEntropy source adapters for a requested name."""
    spec = parse_openentropy_source_spec(requested)
    if spec is None:
        return
    if spec.selector is None:
        yield OpenEntropySource(
            conditioning=spec.conditioning,
            requested_name=spec.canonical_name,
        )
        return
    yield OpenEntropySource.from_selector(
        spec.selector,
        conditioning=spec.conditioning,
        device_mode=spec.device_mode,
        requested_name=spec.canonical_name,
    )


__all__ = [
    "OpenEntropySource",
    "OpenEntropySourceSpec",
    "discover_openentropy_source_infos",
    "parse_openentropy_source_spec",
    "resolve_openentropy_source_candidates",
]
