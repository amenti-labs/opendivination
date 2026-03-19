from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from opendivination import __version__

SKILL_RUNNER = Path("skills/divination/scripts/run_opendivination.py")


def _runner_override() -> str:
    installed = shutil.which("opendivination")
    if installed is not None:
        return installed
    return shlex.join([sys.executable, "-m", "opendivination.cli.main"])


def test_skill_runner_check_with_override() -> None:
    env = os.environ.copy()
    env["OPENDIVINATION_RUNNER"] = _runner_override()

    proc = subprocess.run(
        ["python3", str(SKILL_RUNNER), "--check"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["runner_name"] == "env-override"
    assert payload["runner"] == shlex.split(_runner_override())


def test_skill_runner_version_with_override() -> None:
    env = os.environ.copy()
    env["OPENDIVINATION_RUNNER"] = _runner_override()

    proc = subprocess.run(
        ["python3", str(SKILL_RUNNER), "version"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert proc.returncode == 0, proc.stderr
    assert f"OpenDivination {__version__}" in proc.stdout
