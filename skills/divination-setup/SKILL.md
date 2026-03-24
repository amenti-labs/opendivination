---
name: divination-setup
description: Installs or updates OpenDivination, verifies the CLI, and runs first-run source setup including QRNG credentials and QCicada selection. Use when the user wants to set up OpenDivination, bootstrap the divination skill, save a persistent source, or prepare hardware entropy.
license: MIT
allowed-tools: Bash, Read
metadata: {"openclaw":{"skillKey":"divination-setup","homepage":"https://github.com/amenti-labs/opendivination","requires":{"bins":["python3"]}}}
---

# Divination Setup

Install and configure OpenDivination.

Prefer the bundled helper after the CLI is available:

```bash
python3 scripts/run_opendivination.py --check
```

## Use When

- the user wants to install or update OpenDivination
- the user wants to set up the divination skill bundle for first use
- the user wants to run `opendivination setup`
- the user wants a persistent default source
- the user wants to save an ANU or Outshift API key
- the user wants to prepare QCicada or another local hardware source
- the user wants to verify whether QRNG, hardware, or resonance prerequisites are ready

Use `divination` instead when the CLI is already ready and the user just wants a draw, cast, or
source inspection.

## Working Style

- keep going unless a real user choice is required
- prefer fixing environment issues directly over telling the user to do it
- keep `csprng` as the default unless the user explicitly chooses QRNG or local hardware
- prefer `qcicada` over `openentropy` when the user wants the strongest explicit local quantum path
- never imply quantum entropy when the configured source is still `csprng`

## Setup Flow

1. Preflight

```bash
python3 --version
which opendivination || true
```

If OpenDivination is already installed, verify it:

```bash
opendivination version
python3 scripts/run_opendivination.py --check
```

2. Install or update the CLI

Published CLI:

```bash
python3 -m pip install pipx
python3 -m pipx install opendivination
python3 -m pipx upgrade opendivination
```

GitHub fallback:

```bash
python3 -m pipx install git+https://github.com/amenti-labs/opendivination.git
```

Local repo:

```bash
python3 -m pip install -e ".[dev]"
```

If `pipx` is unavailable and a regular Python install is acceptable:

```bash
python3 -m pip install opendivination
```

Optional QCicada hardware path:

```bash
python3.13 -m pipx install --python python3.13 'opendivination[hardware]'
```

3. Install the portable skills when needed

```bash
npx skills add amenti-labs/opendivination --skill divination-setup --skill divination
```

4. Choose the source path

Interactive setup:

```bash
python3 scripts/run_opendivination.py setup
```

Structured setup:

```bash
python3 scripts/run_opendivination.py setup --json
python3 scripts/run_opendivination.py setup --source-profile computer --json
python3 scripts/run_opendivination.py setup --source-profile remote_quantum --qrng-provider anu --api-key YOUR_KEY --json
python3 scripts/run_opendivination.py setup --source-profile local_hardware --hardware-source qcicada --json
```

Ask the user which path they want:

- regular computer RNG
- remote QRNG
- local hardware QRNG

For remote QRNG:

- ask whether they want `anu` or `outshift`
- ask for the API key when required
- store it through `setup`

For local hardware:

- check availability with `python3 scripts/run_opendivination.py sources --json`
- prefer `qcicada` when present
- if no hardware source is detected, keep `csprng` and explain why

5. Verify

```bash
python3 scripts/run_opendivination.py version
python3 scripts/run_opendivination.py sources --json
python3 scripts/run_opendivination.py draw tarot --json
```

When provenance or trust matters, always report:

- `provenance.source_id`
- `provenance.is_quantum`

## Reference

After setup is complete, use the `divination` skill for actual readings and symbolic interpretation.
