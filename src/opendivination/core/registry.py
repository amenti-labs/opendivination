from __future__ import annotations

import asyncio
from collections.abc import Iterable
from importlib import import_module
from typing import Any, cast

from opendivination.sources.csprng import CSPRNGSource
from opendivination.types import EntropySource, SourceInfo


class SourceNotFoundError(Exception):
    pass


class NoSourceAvailableError(Exception):
    pass


class SourceRegistry:
    _AVAILABILITY_TIMEOUT_SECONDS: float = 2.0

    def __init__(self) -> None:
        self._sources: dict[str, tuple[int, EntropySource]] = {}
        self._register_default_sources()

    def register(self, source: EntropySource, priority: int) -> None:
        """Register an entropy source with given priority (lower = higher priority)."""
        self._sources[source.name] = (priority, source)

    async def auto_detect(self) -> list[SourceInfo]:
        """Check which sources are available. Returns list of available SourceInfo."""
        detected: list[SourceInfo] = []
        for source in self._ordered_sources():
            if await self._is_source_available(source):
                detected.append(self._build_source_info(source, available=True))
        return detected

    async def get_bytes(self, n: int, source: str | None = None) -> tuple[bytes, SourceInfo]:
        """Get n entropy bytes from specified source or first available in fallback order.

        Raises:
            SourceNotFoundError: If specified source name not registered
            NoSourceAvailableError: If no source is available
        """
        if n < 1:
            raise ValueError("n must be >= 1")

        if source is not None:
            source_entry = self._sources.get(source)
            if source_entry is None:
                dynamic_source = self._resolve_dynamic_source(source)
                if dynamic_source is None:
                    raise SourceNotFoundError(f"Source not registered: {source}")
                source_entry = (10, dynamic_source)

            selected_source = source_entry[1]
            if not await self._is_source_available(selected_source):
                raise NoSourceAvailableError(f"Requested source is unavailable: {source}")

            entropy = await selected_source.get_bytes(n)
            return entropy, self._build_source_info(selected_source, available=True)

        for selected_source in self._ordered_sources():
            if not await self._is_source_available(selected_source):
                continue

            try:
                entropy = await selected_source.get_bytes(n)
            except Exception:
                continue

            return entropy, self._build_source_info(selected_source, available=True)

        raise NoSourceAvailableError("No registered entropy source is currently available")

    def list_sources(self, *, expand_openentropy: bool = False) -> list[SourceInfo]:
        """Return all registered sources with their info."""
        listed = [
            self._build_source_info(source, available=False) for source in self._ordered_sources()
        ]
        if expand_openentropy:
            listed.extend(self._discover_openentropy_named_sources())
        return listed

    def _ordered_sources(self) -> list[EntropySource]:
        ordered_entries = sorted(
            self._sources.values(), key=lambda entry: (entry[0], entry[1].name)
        )
        return [source for _, source in ordered_entries]

    async def _is_source_available(self, source: EntropySource) -> bool:
        try:
            return await asyncio.wait_for(
                source.is_available(),
                timeout=self._AVAILABILITY_TIMEOUT_SECONDS,
            )
        except (TimeoutError, asyncio.TimeoutError, Exception):
            return False

    def _build_source_info(self, source: EntropySource, available: bool) -> SourceInfo:
        selector = getattr(source, "selector", None)
        conditioning = getattr(source, "conditioning", None)
        device_mode = getattr(source, "device_mode", None)
        backend = "openentropy" if source.name.startswith("openentropy") else None
        selection_mode = None
        if backend == "openentropy" and selector is None:
            selection_mode = "aggregate"
        if backend == "openentropy" and selector is not None:
            selection_mode = "named_source"
        if source.name == "csprng":
            quality_score = 0.5
        elif backend == "openentropy" and selector is not None and source.is_quantum:
            quality_score = 0.95
        elif backend == "openentropy":
            quality_score = 0.8
        elif source.is_quantum:
            quality_score = 0.9
        else:
            quality_score = 0.0
        return SourceInfo(
            name=source.name,
            source_type=source.source_type,
            is_quantum=source.is_quantum,
            description=source.description,
            backend=backend,
            selector=selector,
            selection_mode=selection_mode,
            conditioning=conditioning,
            device_mode=device_mode,
            available=available,
            quality_score=quality_score,
        )

    def _discover_openentropy_named_sources(self) -> list[SourceInfo]:
        try:
            module = import_module("opendivination.sources.openentropy")
        except ImportError:
            return []
        discover = getattr(module, "discover_openentropy_source_infos", None)
        if not callable(discover):
            return []
        try:
            return cast(list[SourceInfo], discover())
        except Exception:
            return []

    def _register_default_sources(self) -> None:
        self._try_register_optional_source(
            name="openentropy",
            module_path="opendivination.sources.openentropy",
            class_names=("OpenEntropySource",),
            priority=80,
        )
        self._try_register_optional_source(
            name="anu",
            module_path="opendivination.sources.anu",
            class_names=("ANUSource", "AnuSource"),
            priority=20,
        )
        self._try_register_optional_source(
            name="outshift",
            module_path="opendivination.sources.outshift",
            class_names=("OutshiftSource",),
            priority=30,
        )

        self.register(CSPRNGSource(), priority=99)

    def _try_register_optional_source(
        self,
        *,
        name: str,
        module_path: str,
        class_names: Iterable[str],
        priority: int,
    ) -> None:
        try:
            module = import_module(module_path)
        except ImportError:
            return

        source_class = self._get_source_class(module, class_names)
        if source_class is None:
            return

        try:
            source_instance = source_class()
        except Exception:
            return

        if getattr(source_instance, "name", None) != name:
            return

        self.register(source_instance, priority=priority)

    def _resolve_dynamic_source(self, requested: str) -> EntropySource | None:
        try:
            module = import_module("opendivination.sources.openentropy")
        except ImportError:
            return None
        resolver = getattr(module, "resolve_openentropy_source_candidates", None)
        if not callable(resolver):
            return None
        try:
            for candidate in cast(Iterable[EntropySource], resolver(requested)):
                return candidate
        except Exception:
            return None
        return None

    def _get_source_class(
        self, module: Any, class_names: Iterable[str]
    ) -> type[EntropySource] | None:
        for class_name in class_names:
            source_class = getattr(module, class_name, None)
            if isinstance(source_class, type):
                return cast(type[EntropySource], source_class)
        return None


__all__ = ["SourceRegistry", "SourceNotFoundError", "NoSourceAvailableError"]
