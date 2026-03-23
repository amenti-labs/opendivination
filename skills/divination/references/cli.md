# OpenDivination CLI Reference

## Defaults

- default entropy source: `csprng`
- default tarot mode: `selection`
- resonance is opt-in and requires an embedding provider

## Core Commands

```bash
python3 scripts/run_opendivination.py setup
python3 scripts/run_opendivination.py draw tarot --json
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
Only after embedding setup:

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

Guided setup:

```bash
python3 scripts/run_opendivination.py setup
```

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
- `outshift` may require provider credentials

Persistent remote QRNG config:

```bash
python3 scripts/run_opendivination.py setup \
  --source-profile remote_quantum \
  --qrng-provider anu \
  --api-key YOUR_KEY
```

Hardware QRNG:

```bash
python3.13 -m pip install 'opendivination[hardware]'
python3 scripts/run_opendivination.py sources --json
python3 scripts/run_opendivination.py draw tarot --source qcicada --json
```

If `qcicada` is not listed in `sources --json`, the local hardware stack is not ready yet.
The QCicada / `openentropy` path is currently verified on Python 3.13 rather than Python 3.14.

Persistent hardware default:

```bash
python3 scripts/run_opendivination.py setup \
  --source-profile local_hardware \
  --hardware-source qcicada
```

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

If Ollama is unavailable, `--embed-provider local` falls back to `sentence-transformers`, which
must be installed separately.

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

GitHub fallback:

```bash
python3 -m pipx install git+https://github.com/amenti-labs/opendivination.git
```

Local repo:

```bash
python3 -m pip install -e ".[dev]"
```
