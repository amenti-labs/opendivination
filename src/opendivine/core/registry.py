from __future__ import annotations

import asyncio
from collections.abc import Iterable
from importlib import import_module
from typing import Any, cast

from opendivine.sources.csprng import CSPRNGSource
from opendivine.types import EntropySource, SourceInfo


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
                raise SourceNotFoundError(f"Source not registered: {source}")

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

    def list_sources(self) -> list[SourceInfo]:
        """Return all registered sources with their info."""
        return [
            self._build_source_info(source, available=False) for source in self._ordered_sources()
        ]

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
        return SourceInfo(
            name=source.name,
            source_type=source.source_type,
            is_quantum=source.is_quantum,
            description=source.description,
            available=available,
            quality_score=0.5 if source.name == "csprng" else 0.0,
        )

    def _register_default_sources(self) -> None:
        self._try_register_optional_source(
            name="openentropy",
            module_path="opendivine.sources.openentropy",
            class_names=("OpenEntropySource",),
            priority=10,
        )
        self._try_register_optional_source(
            name="anu",
            module_path="opendivine.sources.anu",
            class_names=("ANUSource", "AnuSource"),
            priority=20,
        )
        self._try_register_optional_source(
            name="qbert",
            module_path="opendivine.sources.qbert",
            class_names=("QbertSource",),
            priority=30,
        )
        self._try_register_optional_source(
            name="outshift",
            module_path="opendivine.sources.outshift",
            class_names=("OutshiftSource",),
            priority=40,
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

    def _get_source_class(
        self, module: Any, class_names: Iterable[str]
    ) -> type[EntropySource] | None:
        for class_name in class_names:
            source_class = getattr(module, class_name, None)
            if isinstance(source_class, type):
                return cast(type[EntropySource], source_class)
        return None


__all__ = ["SourceRegistry", "SourceNotFoundError", "NoSourceAvailableError"]
