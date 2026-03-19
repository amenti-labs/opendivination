# OpenDivination

OpenDivination is a lightweight oracle SDK and CLI for:

- tarot draws
- I Ching casts
- auditable entropy provenance
- one stable text-only tarot resonance mode
- coherence scoring (semantic similarity between question and drawn symbol)

The product surface is intentionally small. Selection mode is the default. Resonance mode is a single opinionated text-first path built from the latest local QCicada experiments.

## Install

```bash
# Easiest CLI install
pipx install opendivination

# Python SDK install
pip install opendivination

# Hardware QRNG support
pip install "opendivination[hardware]"
```

The default install requires no QRNG device and no embedding model. Out of the box, draws use the
computer RNG source `csprng`.

QCicada hardware support is currently verified on Python 3.13. The base package works on Python
3.14, but the `openentropy` dependency does not build there yet.

## Core Commands

```bash
opendivination draw tarot --json
opendivination draw tarot --mode resonance --json
opendivination draw iching --method yarrow --json
opendivination sources --json
```

Those default to `--source csprng` unless you explicitly choose another source.

## Source Modes

OpenDivination has three practical source paths:

- `csprng`: regular computer RNG, available by default, no extra setup
- network QRNG: sources like `anu`, `qbert`, or `outshift`
- hardware QRNG: sources like `qcicada` via `openentropy`

Check what is available on the current machine:

```bash
opendivination sources --json
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

The default source is `csprng`. To opt into QRNG, pass an explicit source such as `source="anu"` or
`source="qcicada"`.

## QRNG

Network QRNG examples:

```bash
opendivination draw tarot --source anu --json
opendivination draw iching --source anu --json
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

CLI:

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
- `qbert`
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
