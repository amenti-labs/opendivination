from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def _cli_command() -> list[str]:
    installed = shutil.which("opendivination")
    if installed is not None:
        return [installed]
    return [sys.executable, "-m", "opendivination.cli.main"]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*_cli_command(), *args],
        capture_output=True,
        text=True,
    )


def test_cli_draw_tarot_json() -> None:
    proc = _run_cli("draw", "tarot", "--source", "csprng", "--json")

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["provenance"]["source_id"] == "csprng"
    assert data["provenance"]["is_quantum"] is False


def test_cli_draw_tarot_json_defaults_to_csprng() -> None:
    proc = _run_cli("draw", "tarot", "--json")

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["provenance"]["source_id"] == "csprng"
    assert data["provenance"]["is_quantum"] is False


def test_cli_draw_tarot_resonance_json() -> None:
    proc = _run_cli(
        "draw",
        "tarot",
        "--mode",
        "resonance",
        "--embed-provider",
        "deterministic",
        "--source",
        "csprng",
        "--json",
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["provider"] == "deterministic"
    assert data["entropy_bytes"] == 256
    assert data["shortlist_size"] == 3
    assert data["asset_text_profile"] == "descriptive"
    assert data["entropy_text_profile"] == "bare_hex_spaced"
    assert data["provenance"]["source_id"] == "csprng"


def test_cli_draw_tarot_resonance_uses_json_config(tmp_path: Path) -> None:
    config_path = tmp_path / "opendivination.json"
    config_path.write_text(
        json.dumps(
            {
                "tarot": {
                    "card_text": {
                        "profiles": {
                            "descriptive": {
                                "template": (
                                    "Configured {name}. Arcana {arcana}. "
                                    "Suit {suit}. Keywords {keywords}."
                                )
                            }
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    proc = _run_cli(
        "draw",
        "tarot",
        "--mode",
        "resonance",
        "--embed-provider",
        "deterministic",
        "--config",
        str(config_path),
        "--json",
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    details = data["provenance"]["details"]
    assert details["asset_text_profile_configured"] is True
    assert details["asset_text_configured_profiles"] == ["descriptive"]


def test_cli_draw_tarot_resonance_missing_config_fails(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"

    proc = _run_cli(
        "draw",
        "tarot",
        "--mode",
        "resonance",
        "--embed-provider",
        "deterministic",
        "--config",
        str(missing_path),
    )

    assert proc.returncode != 0
    assert "OpenDivination config not found" in proc.stderr


def test_cli_cache_tarot_json() -> None:
    proc = _run_cli("cache", "tarot", "--embed-provider", "deterministic", "--json")

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["provider"] == "deterministic"
    assert data["prepared_cards"] == 78
    assert data["asset_text_profile"] == "descriptive"


def test_cli_draw_iching_json() -> None:
    proc = _run_cli(
        "draw",
        "iching",
        "--method",
        "uniform",
        "--source",
        "csprng",
        "--json",
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["method"] == "uniform"
    assert data["provenance"]["source_id"] == "csprng"


def test_cli_draw_iching_json_defaults_to_csprng() -> None:
    proc = _run_cli("draw", "iching", "--json")

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["provenance"]["source_id"] == "csprng"
    assert data["provenance"]["is_quantum"] is False


def test_cli_sources_json() -> None:
    proc = _run_cli("sources", "--json")

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert isinstance(data, list)
    assert any(item["name"] == "csprng" for item in data)
