# OpenDivination CLI Reference

## Defaults

- default entropy source: `csprng`
- default tarot mode: `selection`
- resonance is opt-in and requires an embedding provider

## Core Commands

```bash
python3 scripts/run_opendivination.py draw tarot --json
python3 scripts/run_opendivination.py draw tarot --mode resonance --json
python3 scripts/run_opendivination.py draw iching --method yarrow --json
python3 scripts/run_opendivination.py sources --json
python3 scripts/run_opendivination.py version
```

## Tarot

Standard selection:

```bash
python3 scripts/run_opendivination.py draw tarot --json
```

Stable resonance:

```bash
python3 scripts/run_opendivination.py draw tarot \
  --mode resonance \
  --embed-provider local \
  --embed-model nomic-embed-text \
  --json
```

QRNG selection:

```bash
python3 scripts/run_opendivination.py draw tarot --source qcicada --json
python3 scripts/run_opendivination.py draw tarot --source anu --json
```

Important fields:

- `card.name`
- `provenance.source_id`
- `provenance.is_quantum`

## I Ching

```bash
python3 scripts/run_opendivination.py draw iching --method yarrow --json
python3 scripts/run_opendivination.py draw iching --method three_coin --json
python3 scripts/run_opendivination.py draw iching --method uniform --json
```

## Sources

```bash
python3 scripts/run_opendivination.py sources --json
```

Useful fields:

- `name`
- `type`
- `is_quantum`
- `available`

## Config

Resonance card text can be overridden with:

- `~/.config/opendivination/config.json`
- `--config /path/to/config.json`

Example file:

```text
skills/divination/examples/config.json
```

## QRNG Setup

Network QRNG:

- `anu` works without extra package installation
- `qbert` and `outshift` may require provider credentials

Hardware QRNG:

```bash
python3.13 -m pip install 'opendivination[hardware]'
python3 scripts/run_opendivination.py sources --json
python3 scripts/run_opendivination.py draw tarot --source qcicada --json
```

If `qcicada` is not listed in `sources --json`, the local hardware stack is not ready yet.
The QCicada / `openentropy` path is currently verified on Python 3.13 rather than Python 3.14.

## Resonance Setup

Simplest local embedding path:

```bash
ollama pull nomic-embed-text
python3 scripts/run_opendivination.py draw tarot \
  --mode resonance \
  --embed-provider local \
  --embed-model nomic-embed-text \
  --json
```

QRNG-backed resonance:

```bash
python3 scripts/run_opendivination.py draw tarot \
  --mode resonance \
  --embed-provider local \
  --embed-model nomic-embed-text \
  --source qcicada \
  --json
```

## Install

```bash
python3 -m pip install pipx
python3 -m pipx install opendivination
python3 -m pipx install --python python3.13 'opendivination[hardware]'  # optional QCicada support
```

Local repo:

```bash
python3 -m pip install -e ".[dev]"
```
