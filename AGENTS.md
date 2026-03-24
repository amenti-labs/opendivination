# OpenDivination Agent Guide

## Canonical Agent Surfaces

- Python SDK in `src/opendivination/`
- CLI via `opendivination ...`
- Portable skill bundles in `skills/`
- Repository-level instructions in `AGENTS.md`

The MCP server was intentionally removed. Do not reintroduce MCP as the primary integration
surface unless there is an explicit product decision to do so.

## Read These First

1. `README.md`
2. `skills/AGENTS.md`
3. `skills/divination-setup/SKILL.md`
4. `skills/divination/SKILL.md`
5. `src/opendivination/types.py`
6. `src/opendivination/cli/main.py`
7. `tests/test_cli.py`

## Core Commands

Development setup:

```bash
pip install -e ".[dev]"
```

Quality checks:

```bash
pytest
ruff check src tests skills/divination/scripts skills/divination-setup/scripts
mypy src
```

Canonical agent commands:

```bash
opendivination setup --json
opendivination draw tarot --json
opendivination draw tarot --question "What should I focus on?" --embed-provider local --json
opendivination draw iching --method yarrow --json
opendivination draw iching --question "How do I proceed?" --embed-provider local --json
opendivination sources --json
```

Source defaults:

- `csprng` is the default source unless the user has explicitly changed it with `setup`
- `openentropy` is not a default; treat it as an opt-in local hardware path
- prefer `qcicada` over the aggregate `openentropy` source when the user wants the strongest explicit quantum path

Skill helper:

```bash
python3 skills/divination-setup/scripts/run_opendivination.py --check
python3 skills/divination/scripts/run_opendivination.py --check
```

## Result Handling Rules

- Prefer JSON CLI output when an agent needs structured data.
- When the user asks about randomness, provenance, or trust, always include
  `provenance.source_id` and `provenance.is_quantum`.
- Never imply quantum entropy when the actual source is `csprng`.
- Keep interpretation separate from entropy/provenance facts.
- If you change output structure, update the README, the skill bundle, and tests together.

## Before Shipping Changes

- Run `pytest`
- Run `ruff check src tests skills/divination/scripts skills/divination-setup/scripts`
- Run `mypy src`
- If a skill changed, verify both `skills/divination-setup/SKILL.md` and
  `skills/divination/SKILL.md` still validate and that the helper runners still work
- Keep `README.md`, `AGENTS.md`, and `skills/` aligned
