from __future__ import annotations

import asyncio

from opendivine.core.registry import SourceRegistry
from opendivine.sources import openentropy as openentropy_module
from opendivine.sources.csprng import CSPRNGSource


def test_csprng_source_always_available() -> None:
    source = CSPRNGSource()
    assert asyncio.run(source.is_available()) is True

    health = asyncio.run(source.health_check())
    assert health.available is True
    assert health.quality_score == 0.5

    entropy = asyncio.run(source.get_bytes(32))
    assert len(entropy) == 32


def test_openentropy_import_guard_graceful(monkeypatch) -> None:
    source = openentropy_module.OpenEntropySource()
    monkeypatch.setattr(openentropy_module, "_OPENENTROPY_AVAILABLE", False)
    source._pool = None

    assert asyncio.run(source.is_available()) is False
    health = asyncio.run(source.health_check())
    assert health.available is False
    assert health.quality_score == 0.0
    assert health.last_error is not None


def test_registry_auto_detect_has_csprng() -> None:
    registry = SourceRegistry()
    detected = asyncio.run(registry.auto_detect())
    names = {source.name for source in detected}
    assert "csprng" in names
