<p align="center">
  <img src="assets/logo.png" alt="OpenDivination" width="180">
</p>

<h1 align="center">OpenDivination</h1>

<p align="center">
  <a href="https://pypi.org/project/opendivination/">
    <img src="https://img.shields.io/pypi/v/opendivination" alt="PyPI">
  </a>
  <a href="https://github.com/amenti-labs/opendivination/actions/workflows/ci.yml">
    <img src="https://github.com/amenti-labs/opendivination/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://github.com/amenti-labs/opendivination/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/amenti-labs/opendivination" alt="License">
  </a>
  <img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue" alt="Python versions">
</p>

<p align="center">
  <img src="assets/hero.gif" alt="OpenDivination terminal demo" width="900">
</p>

OpenDivination is a lightweight oracle SDK and CLI for:

- tarot draws
- I Ching casts
- auditable entropy provenance
- one stable text-only tarot resonance mode
- coherence scoring (semantic similarity between question and drawn symbol)

The product surface is intentionally small:

- selection mode by default
- `csprng` by default
- QRNG and resonance are opt-in

## Quickstart

```bash
pipx install opendivination
opendivination setup
opendivination draw tarot --json
opendivination draw iching --method yarrow --json
opendivination sources --json
```

GitHub fallback:

```bash
pipx install git+https://github.com/amenti-labs/opendivination.git
```

Python SDK:

```bash
pip install opendivination
```

`opendivination setup` writes `~/.config/opendivination/config.json` and can keep the default
`csprng` path, save remote QRNG credentials, or select detected local hardware.

## Sources

OpenDivination supports three practical source paths:

- `csprng`: default software RNG
- remote QRNG: `anu` or `outshift`
- local hardware: `qcicada` via `openentropy`

If trust or randomness provenance matters, inspect:

- `provenance.source_id`
- `provenance.is_quantum`

Important defaults:

- `csprng` remains the default until the user explicitly changes it
- `openentropy` is not a default
- prefer `qcicada` over the aggregate `openentropy` source when the user wants the strongest local quantum path

QCicada hardware support is currently verified on Python 3.13. The base package works on Python
3.14, but the `openentropy` dependency does not build there yet.

## Resonance

Resonance is a single stable text-only tarot path. It is opt-in and requires an embedding runtime.

```bash
opendivination draw tarot \
  --mode resonance \
  --embed-provider local \
  --embed-model nomic-embed-text \
  --json
```

Coherence scoring is also opt-in:

```bash
opendivination draw tarot -q "What should I focus on?" --embed-provider local --json
opendivination draw iching -q "How should I proceed?" --embed-provider local --json
```

## Skills

OpenDivination ships two portable skills:

```bash
npx skills add amenti-labs/opendivination --skill divination-setup --skill divination
```

- `divination-setup` installs or updates OpenDivination and handles first-run source setup
- `divination` performs tarot draws, I Ching casts, source inspection, and provenance-aware result handling

Detailed docs:

- `skills/AGENTS.md` for the portable skill index
- `skills/divination-setup/SKILL.md` for setup and persistent source configuration
- `skills/divination/SKILL.md` for runtime behavior and result handling
- `skills/divination/references/cli.md` for CLI examples and QRNG/resonance notes

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests skills/divination/scripts skills/divination-setup/scripts
mypy src
python3 skills/divination-setup/scripts/run_opendivination.py --check
python3 skills/divination/scripts/run_opendivination.py --check
```
