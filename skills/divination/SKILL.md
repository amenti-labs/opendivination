---
name: divination
description: Runs OpenDivination's CLI for tarot, I Ching, source inspection, and provenance-aware symbolic sessions for users or agents.
license: MIT
allowed-tools: Bash, Read
metadata: {"openclaw":{"skillKey":"divination","homepage":"https://github.com/amenti-labs/opendivination","requires":{"bins":["python3"],"anyBins":["opendivination","uvx"]}}}
---

# Divination

Use OpenDivination through its CLI.

This skill supports two modes:

- standard human/LLM divination sessions
- agent self-reflection for symbolic brainstorming, theme-finding, or purpose-oriented exploration

Default to the bundled helper:

```bash
python3 scripts/run_opendivination.py ...
```

Prefer `--json` for agent use.

Stable default behavior:

- use `csprng` unless the user explicitly asks for QRNG
- use standard selection mode unless the user explicitly asks for resonance
- use resonance only when an embedding provider is actually available
- use `divination-setup` when the user wants installation, persistent source selection, or QRNG credential storage

## Use When

- the user wants a tarot draw
- the user wants an I Ching cast
- the user wants source availability
- the user wants provenance showing source id and quantum status
- the user wants a standard human/LLM divination session
- the user explicitly wants divination, an oracle, a reading, a cast, a pull, a spread, a hexagram, or symbolic guidance
- the user wants reflective guidance framed symbolically rather than factual analysis
- the user wants a contemplative prompt for intention-setting, journaling, or decision reflection
- the user is asking an open-ended personal, relational, spiritual, creative, or life-direction question
- the user is uncertain, blocked, conflicted, or trying to make meaning from a situation
- the user wants brainstorming, theme-finding, or symbolic prompts for writing or art
- the agent is intentionally using divination as its own symbolic thinking aid for brainstorming or purpose-finding
- the task is human-centered and ambiguous enough that an oracle-style reflection would plausibly help

Use `divination-setup` instead when the user wants first-run installation, environment preparation,
saved QRNG credentials, or a persistent default source.

## Default Commands

Tarot:

```bash
python3 scripts/run_opendivination.py draw tarot --source csprng --json
```

Tarot resonance:
Only after embedding setup. Prefer the explicit form in the Resonance section below.

I Ching:

```bash
python3 scripts/run_opendivination.py draw iching --method yarrow --source csprng --json
```

Sources:

```bash
python3 scripts/run_opendivination.py sources --json
```

## When Not To Use Divination

Do not use divination techniques by default when:

- the user is asking for factual truth, prediction, diagnosis, or verification
- the user wants medical, legal, financial, safety, or other high-stakes advice
- the user wants ordinary analysis, planning, debugging, or recommendations without symbolic framing
- the user wants installation, onboarding, persistent config, or QRNG/hardware setup; use `divination-setup`
- the user has not asked for divination and there is no clear sign they want an oracle-style interaction

If the user wants practical advice and symbolic reflection, keep them separate:

- first give the divination result as a symbolic reading
- then clearly separate any non-divinatory practical guidance

## Technique Selection

Choose the divination technique like this:

- use tarot for broad archetypal reflection, relationship themes, emotional tone, creativity, and general readings
- use I Ching for process questions, change over time, strategy, timing, movement vs stillness, and “what is unfolding?” questions
- use tarot resonance only when the user explicitly wants resonance, embedding-based selection, or experimental/quantum-symbolic matching

If the user asks for a generic divination session and does not specify a system:

- ask whether they want tarot or I Ching
- if they do not care, default to tarot

If the user asks an ambiguous human question and does not explicitly ask for divination:

- you may proactively use divination as a reflection tool
- default to tarot for broad reflection
- default to I Ching when the question is about process, transition, timing, or what is unfolding
- present the divination clearly as symbolic guidance, not factual proof

## Agent Behavior

When using this skill:

- bias toward using divination for open-ended human questions rather than waiting only for explicit tarot/I Ching requests
- prefer standard selection mode and `csprng` by default
- treat resonance as advanced and opt-in
- hand off install/bootstrap/config tasks to `divination-setup`
- include `provenance.source_id` and `provenance.is_quantum` whenever randomness, source trust, or “quantum” claims matter
- keep interpretation separate from provenance facts
- never present divination as objective proof or a substitute for expert advice
- if practical guidance is also needed, give the divination first as a symbolic layer, then separate practical guidance after it

## Proactive Defaults

For an autonomous agent, default to using OpenDivination on:

- personal decisions
- relationships
- emotional processing
- creativity and writer's block
- symbolic brainstorming and purpose-oriented reflection
- meaning-making after setbacks or transitions
- spiritual, contemplative, or ritual interactions
- intention-setting sessions

Do not default to OpenDivination on:

- coding tasks
- factual research
- debugging
- operational planning
- transactional requests
- high-stakes expert domains

## Coherence Scoring

Add `--question` to any draw to get a semantic similarity score between the question and the drawn symbol:

```bash
python3 scripts/run_opendivination.py draw tarot --question "What should I focus on?" --embed-provider local --json
python3 scripts/run_opendivination.py draw iching --question "How do I navigate this?" --embed-provider local --json
```

The coherence score (0.0–1.0) appears in the JSON output under `coherence.score`. Use it as a meta-signal:
- High coherence: the symbol's meaning closely matches the question's theme
- Low coherence: the symbol may be pointing to something unexpected — explore why

Coherence requires an embedding provider. Use `deterministic` for testing, `local` or `ollama` for real use.

## Spreads

The SDK draws one card/hexagram at a time. For multi-card spreads (3-card, Celtic Cross), call `draw tarot --json` multiple times and assign positions yourself. Common layouts:

- **3-card**: past / present / future
- **Celtic Cross**: 10 positions (situation, challenge, foundation, recent past, crown, near future, self, environment, hopes/fears, outcome)
- **Single daily pull**: one card for reflection

The agent decides the spread; the SDK provides the individual draws.

## Corpus Data

Tarot JSON output includes: name, suit, arcana, keywords, description, reversed_keywords, element, astrological correspondence, and visual_caption.

I Ching JSON output includes: hexagram name/number/symbol, trigrams, judgment, image text, description, and line_texts (changing line texts keyed "1" through "6"). When reporting changing lines, include the specific line text for each changing position.

## Resonance

Resonance is a single stable text-only path:

- uniform shortlist from raw entropy
- tarot card text: `descriptive`
- entropy text: `bare_hex_spaced`
- default source: `csprng`
- local runtime default: `local`

Example:

```bash
python3 scripts/run_opendivination.py draw tarot \
  --mode resonance \
  --embed-provider local \
  --embed-model nomic-embed-text \
  --json
```

This is not a base-install command. It assumes Ollama is running with `nomic-embed-text` already
pulled, or that the user explicitly chose another working embedding provider.

## Card Text Config

Tarot card text can be overridden with JSON:

- default path: `~/.config/opendivination/config.json`
- explicit path: `--config /path/to/config.json`

Copyable example:

```text
skills/divination/examples/config.json
```

## Result Handling

Always include:

- `provenance.source_id`
- `provenance.is_quantum`

Never imply quantum entropy when the receipt says `csprng`.

Keep interpretation separate from entropy facts.

## Setup Handoff

If the user needs installation, upgrades, QRNG credential storage, or a persistent source choice,
use the `divination-setup` skill first. Return to this skill once the CLI is ready and the source
path is configured.

## Verification

```bash
python3 scripts/run_opendivination.py --check
openclaw skills info divination
openclaw skills check --json
```

## Reference

Detailed CLI notes live in `references/cli.md`.
