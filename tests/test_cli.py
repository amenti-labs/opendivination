from __future__ import annotations

import json
import subprocess


def test_cli_draw_tarot_json() -> None:
    proc = subprocess.run(
        ["opendivine", "draw", "tarot", "--source", "csprng", "--json"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert "card" in data
    assert "provenance" in data
    assert data["provenance"]["source_id"] == "csprng"


def test_cli_draw_iching_json() -> None:
    proc = subprocess.run(
        [
            "opendivine",
            "draw",
            "iching",
            "--method",
            "uniform",
            "--source",
            "csprng",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert "primary" in data
    assert "lines" in data
    assert data["method"] == "uniform"
    assert data["provenance"]["source_id"] == "csprng"


def test_cli_sources_json() -> None:
    proc = subprocess.run(
        ["opendivine", "sources", "--json"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert isinstance(data, list)
    names = {item["name"] for item in data}
    assert "csprng" in names
