<p align="center">
  <img src="assets/logo.png" alt="OpenDivination" width="180">
</p>

<h1 align="center">OpenDivination</h1>

<p align="center">
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

The product surface is intentionally small. Selection mode is the default. Resonance mode is a single opinionated text-first path built from the latest local QCicada experiments.

## For Agents

If you are an agent or you are pointing an agent at this repo, the intended bootstrap flow is:

1. install the CLI
2. install the `divination` skill bundle
3. run `opendivination setup`
4. ask the user which source path they want:
   - regular computer RNG
   - remote QRNG
   - local hardware QRNG

Recommended agent flow:

```bash
pipx install opendivination
opendivination setup
opendivination sources --json
```

If the user wants remote QRNG:

- ask whether they want `anu` or `outshift`
- if required, ask for the API key
- save it through `opendivination setup`

If the user wants local hardware:

- prefer `qcicada`
- if `qcicada` is not available, keep `csprng` and explain that the hardware path is not ready yet
- do not silently switch users onto the mixed `openentropy` aggregate unless they explicitly want that

Important default:

- `openentropy` is **not** the default source
- `csprng` is the default source until the user explicitly changes it
- `openentropy` is only used when the user explicitly selects local hardware

Use `opendivination setup --json` if the agent wants a structured result.

## Install

```bash
# Easiest CLI install
pipx install opendivination

# Python SDK install
pip install opendivination
```

The default install requires no QRNG device and no embedding model. Out of the box, draws use the
computer RNG source `csprng`.

QCicada hardware support is currently verified on Python 3.13. The base package works on Python
3.14, but the `openentropy` dependency does not build there yet.

## Guided Setup

The simplest onboarding path is:

```bash
opendivination setup
```

That guided command writes `~/.config/opendivination/config.json` and can:

- keep the default `csprng` path
- switch to a remote QRNG provider like `anu` or `outshift`
- store remote QRNG API keys in the config file
- pick a detected local hardware source such as `qcicada`

The config file is written with owner-only permissions when possible.

Non-interactive examples:

```bash
opendivination setup --source-profile computer
opendivination setup --source-profile remote_quantum --qrng-provider anu --api-key YOUR_KEY
opendivination setup --source-profile local_hardware --hardware-source qcicada
```

## Core Commands

```bash
opendivination draw tarot --json
opendivination draw iching --method yarrow --json
opendivination sources --json
```

Those default to your configured source, or `csprng` if you have not run setup yet.

## Source Modes

OpenDivination has three practical source paths:

- `csprng`: regular computer RNG, available by default, no extra setup
- network QRNG: sources like `anu` or `outshift`
- hardware QRNG: sources like `qcicada` via `openentropy`

If you want the closest thing to explicit non-classical entropy, the opinionated order is:

- `qcicada?conditioning=raw&mode=raw`: best local quantum path, raw device output
- `anu`: remote quantum API
- `outshift`: remote quantum-origin API with provider-side post-processing
- `openentropy`: mixed local physical entropy pool, useful but not a pure quantum source

Check what is available on the current machine:

```bash
opendivination sources --json
```

To save a preferred source for future draws:

```bash
opendivination setup
```

If you care about trust or randomness provenance, always inspect:

- `provenance.source_id`
- `provenance.is_quantum`

## Tarot

```python
from opendivination.oracles.tarot import draw_tarot_sync

result = draw_tarot_sync(source="csprng")
print(result.card.name, result.orientation.value)
print(result.provenance.source_id, result.provenance.is_quantum)
```

The default source is your configured source, or `csprng` if unset. To opt into QRNG for one draw,
pass an explicit source such as `source="anu"` or `source="qcicada"`.

## QRNG

Network QRNG examples:

```bash
opendivination draw tarot --source anu --json
opendivination draw iching --source anu --json
```

If you want future draws to use ANU by default:

```bash
opendivination setup --source-profile remote_quantum --qrng-provider anu --api-key YOUR_KEY
```

Hardware QRNG with QCicada requires the optional hardware dependency and a working OpenEntropy /
QCicada setup:

```bash
python3.13 -m pip install "opendivination[hardware]"
opendivination sources --json
opendivination draw tarot --source qcicada --json
```

If `qcicada` does not show up in `sources --json`, the hardware path is not ready yet.
If you are using Python 3.14, install the hardware path with Python 3.13 until `openentropy`
supports 3.14.

After the hardware stack is ready, you can save it as the default:

```bash
opendivination setup --source-profile local_hardware --hardware-source qcicada
```

## Tarot Resonance

Resonance is now one stable text-only algorithm:

1. sample raw entropy
2. choose a small uniform shortlist from the deck
3. render each shortlisted card as text
4. render the entropy as `bare_hex_spaced`
5. embed both with the chosen text embedding model
6. pick the closest card inside the shortlist

Stable defaults:

- tarot card text: `descriptive`
- entropy text: `bare_hex_spaced`
- entropy bytes: `256`
- shortlist size: `3`
- entropy source default: `csprng`
- local provider: `local`
- local model: Ollama `nomic-embed-text`

```python
from opendivination.embeddings.providers import create_embedding_provider
from opendivination.oracles.tarot import draw_tarot_by_resonance_sync

provider = create_embedding_provider("local", model="nomic-embed-text")
result = draw_tarot_by_resonance_sync(
    provider=provider,
    source="csprng",
)
print(result.card.name, result.score)
print(result.provenance.source_id, result.provenance.is_quantum)
```

Resonance is opt-in. Standard tarot and I Ching draws do not need embeddings.
Do not treat resonance as a base-install command; it requires a working embedding runtime.

After embedding setup, CLI:

```bash
opendivination draw tarot \
  --mode resonance \
  --embed-provider local \
  --embed-model nomic-embed-text \
  --json
```

For a QRNG-backed resonance draw, add an explicit source:

```bash
opendivination draw tarot \
  --mode resonance \
  --embed-provider local \
  --embed-model nomic-embed-text \
  --source qcicada \
  --json
```

Supported stable embedding runtimes:

- `local`
- `ollama`
- `sentence_transformers`
- `openai`
- `openai_compatible`
- `gemini`
- `deterministic` for tests

The simplest local embedding path is:

1. install Ollama
2. run `ollama pull nomic-embed-text`
3. run `opendivination draw tarot --mode resonance --embed-provider local --embed-model nomic-embed-text --json`

If Ollama is not running, `--embed-provider local` will fail unless you separately install
`sentence-transformers` and use `--embed-provider sentence_transformers`.

## Coherence Scoring

Pass a question with `--question` / `-q` to get a coherence score — how semantically similar your
question is to the drawn symbol's meaning. Works with both tarot and I Ching:

```bash
opendivination draw tarot -q "What should I focus on?" --embed-provider local --json
opendivination draw iching -q "How should I approach this conflict?" --embed-provider local --json
```

Python SDK:

```python
from opendivination.embeddings.providers import create_embedding_provider
from opendivination.oracles.tarot import draw_tarot_sync

provider = create_embedding_provider("local")
result = draw_tarot_sync(source="csprng", question="What awaits?", provider=provider)
if result.coherence:
    print(f"Coherence: {result.coherence.score:.4f}")
```

Coherence uses embedding cosine similarity — no LLM required. The question text is never stored;
only a SHA-256 hash appears in the result. Coherence is fully optional: omit `--question` and
draws work exactly as before.

## JSON Card Text Config

Tarot card text can be customized with JSON.

Default path:

```text
~/.config/opendivination/config.json
```

You can also pass `--config /path/to/config.json`.

Example:

```json
{
  "tarot": {
    "card_text": {
      "profiles": {
        "descriptive": {
          "template": "Tarot card: {name}. Arcana: {arcana}. Suit: {suit}. Keywords: {keywords}.",
          "overrides": {
            "Death": "Tarot card: Death. Transformation, ending, and renewal."
          }
        }
      }
    }
  }
}
```

A copyable example also lives at `skills/divination/examples/config.json`.

## Provenance

When randomness or trust matters, use:

- `provenance.source_id`
- `provenance.is_quantum`

OpenDivination keeps interpretation separate from entropy facts. If the source is `csprng`, it is reported honestly as software entropy.

## Sources

Named sources include:

- `qcicada`
- `openentropy:qcicada`
- `anu`
- `outshift`
- `csprng`

Inspect availability with:

```bash
opendivination sources --json
```

## Skill

The OpenClaw skill bundle is in `skills/divination/SKILL.md` and installs as the `divination`
skill.

For the skill, the easiest setup is:

1. install the CLI with `pipx install opendivination`
2. install the `divination` skill bundle into your OpenClaw skills directory
3. use QRNG or resonance only when you intentionally opt in to them

For QCicada hardware support through `pipx`, use Python 3.13 explicitly:

```bash
pipx install --python python3.13 'opendivination[hardware]'
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests skills/divination/scripts
mypy src
python3 skills/divination/scripts/run_opendivination.py --check
```
