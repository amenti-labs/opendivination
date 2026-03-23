from __future__ import annotations

from pathlib import Path

from opendivination.config import (
    OpenDivinationConfig,
    configured_default_source,
    configured_remote_source_api_key,
    load_config,
    save_config,
)
from opendivination.sources.anu import ANUSource
from opendivination.sources.outshift import OutshiftSource


def test_save_and_load_config_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "opendivination.json"
    config = OpenDivinationConfig.model_validate(
        {
            "sources": {
                "default": "anu",
                "anu": {"api_key": "anu-test-key"},
                "outshift": {"api_key": "outshift-test-key"},
            },
            "defaults": {
                "resonance": {
                    "provider": "local",
                    "model": "nomic-embed-text",
                }
            },
        }
    )

    written_path = save_config(config, config_path)
    loaded = load_config(written_path, allow_missing=False)

    assert written_path == config_path
    assert loaded.sources.default == "anu"
    assert loaded.sources.anu.api_key == "anu-test-key"
    assert loaded.sources.outshift.api_key == "outshift-test-key"
    assert loaded.defaults.resonance.model == "nomic-embed-text"


def test_config_helpers_read_default_source_and_keys(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "opendivination.json"
    save_config(
        OpenDivinationConfig.model_validate(
            {
                "sources": {
                    "default": "outshift",
                    "anu": {"api_key": "anu-key"},
                    "outshift": {"api_key": "outshift-key"},
                }
            }
        ),
        config_path,
    )
    monkeypatch.setenv("OPENDIVINE_CONFIG", str(config_path))

    assert configured_default_source() == "outshift"
    assert configured_remote_source_api_key("anu") == "anu-key"
    assert configured_remote_source_api_key("outshift") == "outshift-key"


def test_anu_source_reads_api_key_from_config(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "opendivination.json"
    save_config(
        OpenDivinationConfig.model_validate({"sources": {"anu": {"api_key": "anu-from-config"}}}),
        config_path,
    )
    monkeypatch.setenv("OPENDIVINE_CONFIG", str(config_path))
    monkeypatch.delenv("ANU_API_KEY", raising=False)

    source = ANUSource()

    assert source._api_key == "anu-from-config"


def test_outshift_source_reads_api_key_from_config(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "opendivination.json"
    save_config(
        OpenDivinationConfig.model_validate(
            {"sources": {"outshift": {"api_key": "outshift-from-config"}}}
        ),
        config_path,
    )
    monkeypatch.setenv("OPENDIVINE_CONFIG", str(config_path))
    monkeypatch.delenv("OUTSHIFT_API_KEY", raising=False)

    source = OutshiftSource()

    assert source._api_key == "outshift-from-config"
