from __future__ import annotations

import asyncio
import os

from opendivination.core.registry import SourceRegistry
from opendivination.sources import openentropy as openentropy_module
from opendivination.sources.csprng import CSPRNGSource


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


def test_openentropy_aggregate_is_not_claimed_quantum() -> None:
    source = openentropy_module.OpenEntropySource()
    assert source.name == "openentropy"
    assert source.is_quantum is False


def test_openentropy_named_selector_alias_resolution(monkeypatch) -> None:
    class FakePool:
        source_count = 1

        @classmethod
        def auto(cls):
            assert os.environ.get("QCICADA_MODE") == "raw"
            return cls()

        def get_source_raw_bytes(self, source: str, n: int) -> bytes:
            assert source == "qcicada"
            return bytes([0xAB]) * n

        def get_source_bytes(self, source: str, n: int, conditioning: str = "sha256") -> bytes:
            raise AssertionError("qcicada alias should default to raw source bytes")

        def get_bytes(self, n: int, conditioning: str = "sha256") -> bytes:
            return bytes([0xCD]) * n

        def collect_all(self, parallel: bool = True, timeout: float = 2.0) -> None:
            return None

    monkeypatch.setattr(openentropy_module, "_OPENENTROPY_AVAILABLE", True)
    monkeypatch.setattr(openentropy_module, "EntropyPool", FakePool)
    monkeypatch.setattr(
        openentropy_module,
        "detect_available_sources",
        lambda: [
            {
                "name": "qcicada",
                "description": "Crypta Labs QCicada USB QRNG",
            }
        ],
    )

    registry = SourceRegistry()
    entropy, source_info = asyncio.run(registry.get_bytes(8, source="qcicada"))
    assert entropy == bytes([0xAB]) * 8
    assert source_info.name == "openentropy:qcicada?conditioning=raw&mode=raw"
    assert source_info.backend == "openentropy"
    assert source_info.selector == "qcicada"
    assert source_info.selection_mode == "named_source"
    assert source_info.conditioning == "raw"
    assert source_info.device_mode == "raw"
    assert source_info.is_quantum is True


def test_openentropy_named_selector_defaults_to_raw_raw(monkeypatch) -> None:
    class FakePool:
        source_count = 1

        @classmethod
        def auto(cls):
            assert os.environ.get("QCICADA_MODE") == "raw"
            return cls()

        def get_source_raw_bytes(self, source: str, n: int) -> bytes:
            assert source == "qcicada"
            return bytes([0xAC]) * n

        def get_source_bytes(self, source: str, n: int, conditioning: str = "sha256") -> bytes:
            raise AssertionError("bare openentropy:qcicada should default to raw source bytes")

        def get_bytes(self, n: int, conditioning: str = "sha256") -> bytes:
            raise AssertionError("named source query should not use aggregate path")

        def collect_all(self, parallel: bool = True, timeout: float = 2.0) -> None:
            return None

    monkeypatch.setattr(openentropy_module, "_OPENENTROPY_AVAILABLE", True)
    monkeypatch.setattr(openentropy_module, "EntropyPool", FakePool)
    monkeypatch.setattr(
        openentropy_module,
        "detect_available_sources",
        lambda: [
            {
                "name": "qcicada",
                "description": "Crypta Labs QCicada USB QRNG",
            }
        ],
    )

    registry = SourceRegistry()
    entropy, source_info = asyncio.run(registry.get_bytes(8, source="openentropy:qcicada"))
    assert entropy == bytes([0xAC]) * 8
    assert source_info.name == "openentropy:qcicada?conditioning=raw&mode=raw"
    assert source_info.backend == "openentropy"
    assert source_info.selector == "qcicada"
    assert source_info.selection_mode == "named_source"
    assert source_info.conditioning == "raw"
    assert source_info.device_mode == "raw"
    assert source_info.is_quantum is True


def test_openentropy_discover_named_sources(monkeypatch) -> None:
    monkeypatch.setattr(openentropy_module, "_OPENENTROPY_AVAILABLE", True)
    monkeypatch.setattr(
        openentropy_module,
        "detect_available_sources",
        lambda: [
            {
                "name": "qcicada",
                "description": "Crypta Labs QCicada USB QRNG",
            },
            {
                "name": "clock_jitter",
                "description": "Clock timing jitter",
            },
        ],
    )

    infos = openentropy_module.discover_openentropy_source_infos()
    names = {info.name for info in infos}
    assert "openentropy:qcicada" in names
    assert "openentropy:clock_jitter" in names
    qcicada = next(info for info in infos if info.selector == "qcicada")
    assert qcicada.is_quantum is True
    assert qcicada.selection_mode == "named_source"
    assert qcicada.backend == "openentropy"


def test_openentropy_named_selector_raw_query_uses_raw_bytes_and_records_mode(
    monkeypatch,
) -> None:
    class FakePool:
        source_count = 1

        @classmethod
        def auto(cls):
            assert os.environ.get("QCICADA_MODE") == "raw"
            return cls()

        def get_source_raw_bytes(self, source: str, n: int) -> bytes:
            assert source == "qcicada"
            return bytes([0xEF]) * n

        def get_source_bytes(self, source: str, n: int, conditioning: str = "sha256") -> bytes:
            raise AssertionError("raw query should use get_source_raw_bytes")

        def get_bytes(self, n: int, conditioning: str = "sha256") -> bytes:
            raise AssertionError("named source query should not use aggregate path")

        def collect_all(self, parallel: bool = True, timeout: float = 2.0) -> None:
            return None

    monkeypatch.setattr(openentropy_module, "_OPENENTROPY_AVAILABLE", True)
    monkeypatch.setattr(openentropy_module, "EntropyPool", FakePool)
    monkeypatch.setattr(
        openentropy_module,
        "detect_available_sources",
        lambda: [
            {
                "name": "qcicada",
                "description": "Crypta Labs QCicada USB QRNG",
            }
        ],
    )

    registry = SourceRegistry()
    entropy, source_info = asyncio.run(
        registry.get_bytes(8, source="qcicada?conditioning=raw&mode=raw")
    )
    assert entropy == bytes([0xEF]) * 8
    assert source_info.name == "openentropy:qcicada?conditioning=raw&mode=raw"
    assert source_info.backend == "openentropy"
    assert source_info.selector == "qcicada"
    assert source_info.selection_mode == "named_source"
    assert source_info.conditioning == "raw"
    assert source_info.device_mode == "raw"
    assert source_info.is_quantum is True


def test_registry_auto_detect_has_csprng() -> None:
    registry = SourceRegistry()
    detected = asyncio.run(registry.auto_detect())
    names = {source.name for source in detected}
    assert "csprng" in names


def test_registry_only_registers_supported_builtin_sources() -> None:
    registry = SourceRegistry()
    listed = registry.list_sources()
    names = {source.name for source in listed}
    assert names <= {"anu", "outshift", "openentropy", "csprng"}
