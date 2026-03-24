from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from opendivination import __version__

SKILL_RUNNERS = (
    Path("skills/divination/scripts/run_opendivination.py"),
    Path("skills/divination-setup/scripts/run_opendivination.py"),
)


def _runner_override() -> str:
    installed = shutil.which("opendivination")
    if installed is not None:
        return installed
    return shlex.join([sys.executable, "-m", "opendivination.cli.main"])


@pytest.mark.parametrize("skill_runner", SKILL_RUNNERS)
def test_skill_runner_check_with_override(skill_runner: Path) -> None:
    env = os.environ.copy()
    env["OPENDIVINATION_RUNNER"] = _runner_override()

    proc = subprocess.run(
        ["python3", str(skill_runner), "--check"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["runner_name"] == "env-override"
    assert payload["runner"] == shlex.split(_runner_override())


@pytest.mark.parametrize("skill_runner", SKILL_RUNNERS)
def test_skill_runner_version_with_override(skill_runner: Path) -> None:
    env = os.environ.copy()
    env["OPENDIVINATION_RUNNER"] = _runner_override()

    proc = subprocess.run(
        ["python3", str(skill_runner), "version"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert proc.returncode == 0, proc.stderr
    assert f"OpenDivination {__version__}" in proc.stdout
