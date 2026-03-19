#!/usr/bin/env python3
"""Resolve and run the best available OpenDivination command."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence


def _module_importable(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _candidate_runners() -> list[tuple[str, list[str]]]:
    override = os.environ.get("OPENDIVINATION_RUNNER")
    if override:
        return [("env-override", shlex.split(override))]

    candidates: list[tuple[str, list[str]]] = []

    if shutil.which("opendivination"):
        candidates.append(("installed-cli", ["opendivination"]))

    if shutil.which("python3") and _module_importable("opendivination.cli.main"):
        candidates.append(("python-module", ["python3", "-m", "opendivination.cli.main"]))

    if shutil.which("uvx"):
        candidates.append(("uvx-package", ["uvx", "--from", "opendivination", "opendivination"]))

    return candidates


def _resolve_runner() -> tuple[str, list[str]]:
    candidates = _candidate_runners()
    if not candidates:
        raise RuntimeError(
            "No OpenDivination runner found. Install `opendivination`, make the module importable, "
            "or install `uv` so `uvx --from opendivination opendivination` is available."
        )
    return candidates[0]


def _run(command: Sequence[str]) -> int:
    process = subprocess.run(command)
    return process.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve and run the best available OpenDivination command."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print the resolved runner as JSON and exit.",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to OpenDivination.",
    )
    namespace = parser.parse_args()

    try:
        runner_name, runner = _resolve_runner()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if namespace.check:
        print(json.dumps({"runner": runner, "runner_name": runner_name}, indent=2))
        return 0

    forwarded_args = list(namespace.args)
    if forwarded_args and forwarded_args[0] == "--":
        forwarded_args = forwarded_args[1:]
    if not forwarded_args:
        parser.error("no OpenDivination arguments provided")

    command = [*runner, *forwarded_args]
    print(
        f"[opendivination-skill] using {runner_name}: {' '.join(command)}",
        file=sys.stderr,
    )
    return _run(command)


if __name__ == "__main__":
    raise SystemExit(main())
