# OpenDivination Launch Copy

Use this as the human-facing copy pack for launch week.

Current working install path:

```bash
pipx install opendivination
npx skills add amenti-labs/opendivination --skill divination
opendivination setup
```

GitHub fallback:

```bash
pipx install git+https://github.com/amenti-labs/opendivination.git
```

## Show HN

### Title options

- `Show HN: OpenDivination – open-source tarot and I Ching with auditable entropy`
- `Show HN: OpenDivination – tarot and I Ching CLI with QRNG provenance`
- `Show HN: OpenDivination – a Python SDK for tarot and I Ching with entropy receipts`

### Post body

I built an open-source Python SDK and CLI for tarot and I Ching called OpenDivination.

The core thing I wanted was honesty about randomness. Most divination software just uses the default pseudorandom generator and never tells you where the draw came from. OpenDivination always returns a provenance receipt with the source id and whether the entropy was actually quantum or not.

It supports:

- normal computer RNG
- remote QRNG providers like ANU
- local hardware sources like QCicada when available
- a guided setup flow so you can choose the source once and keep using it

It also ships as an installable agent skill, so an autonomous coding agent can use it for tarot or I Ching sessions instead of only as a Python library.

I’m not claiming a QRNG makes divination scientifically true. I just think if you care about randomness, it should be inspectable.

Repo:
https://github.com/amenti-labs/opendivination

Quick start:

```bash
pipx install opendivination
npx skills add amenti-labs/opendivination --skill divination
opendivination setup
opendivination draw iching --method yarrow --json
```

### First comment

I’ve practiced I Ching for a long time, and one thing that always bothered me was that almost every digital oracle quietly falls back to ordinary app randomness and never tells you anything about the source.

OpenDivination is my attempt to make that layer explicit. Every draw returns provenance including `source_id` and whether the entropy is actually quantum. If you use regular computer RNG, it says that. If you use ANU or QCicada, it says that too.

It supports both tarot and I Ching, works as a Python SDK and CLI, and also ships as an agent skill. There’s an optional embedding-based resonance mode too, but I kept the default path simple: standard selection with a clear randomness receipt.

The goal isn’t to “prove” divination. It’s to make the mechanism inspectable instead of mystical hand-waving.

## Reddit

### r/Python

I built an open-source Python SDK for tarot and I Ching called OpenDivination.

The main idea is that every draw returns an entropy provenance receipt. So instead of just getting a card or hexagram, you also get the actual source path used for the draw, including whether it was ordinary computer RNG or a quantum source like ANU / QCicada.

It has:

- CLI + Python SDK
- guided source setup
- tarot and I Ching support
- optional QRNG / hardware entropy paths
- agent skill bundle for Claude Code / OpenClaw style environments

I’m not claiming randomness makes divination “scientific.” I just wanted the randomness layer to be explicit and auditable instead of hidden.

Repo: https://github.com/amenti-labs/opendivination

Skill install:

```bash
npx skills add amenti-labs/opendivination --skill divination
```

Install:

```bash
pipx install git+https://github.com/amenti-labs/opendivination.git
opendivination setup
```

### r/ClaudeAI

I made a Claude-compatible divination skill called OpenDivination.

It gives an agent a clean way to do tarot or I Ching sessions through a real CLI, with provenance for the entropy source used in the draw. So if the source is just local computer RNG, that’s explicit. If it’s ANU or QCicada, that’s explicit too.

It’s meant for symbolic guidance, journaling, reflection, and creative use, not factual advice.

Repo: https://github.com/amenti-labs/opendivination

Skill install:

```bash
npx skills add amenti-labs/opendivination --skill divination
```

### r/tarot

I built a small open-source tarot / I Ching tool called OpenDivination.

The thing I cared about most was not “AI interpretation,” but being honest about the draw mechanism. Every pull includes provenance for the randomness source, so you can tell whether the draw came from ordinary computer RNG or from a QRNG source.

I know that won’t matter to everyone, but it mattered to me enough to build it.

If anyone here uses digital decks or computer-assisted readings, I’d be curious whether that provenance layer feels meaningful or irrelevant to you.

Repo: https://github.com/amenti-labs/opendivination

### r/iching

I’ve been working on an open-source I Ching CLI / SDK called OpenDivination.

It supports yarrow, three-coin, and uniform casting, and every cast includes provenance for the entropy source. So you can see whether the result came from standard computer RNG or from a quantum source like ANU / QCicada.

I’m not arguing that a QRNG makes the oracle more valid. I just wanted the casting mechanism to be explicit and inspectable.

Repo: https://github.com/amenti-labs/opendivination

## X / Twitter thread

### Tweet 1

I built an open-source tarot + I Ching SDK called OpenDivination.

The basic idea: if a digital oracle is going to use randomness, it should tell you where that randomness actually came from.

Repo: https://github.com/amenti-labs/opendivination

### Tweet 2

Every draw returns provenance:

- source id
- whether the entropy is quantum
- clear separation between the symbolic result and the randomness facts

So if a draw came from normal computer RNG, it says that. If it came from ANU or QCicada, it says that too.

### Tweet 3

It supports:

- tarot
- I Ching
- guided setup
- remote QRNG
- local hardware entropy
- agent skill install

The default is still simple and honest: regular computer RNG unless you opt into something else.

### Tweet 4

I’m not claiming quantum randomness “proves” divination.

I just think the entropy layer should be inspectable instead of hidden behind `Math.random()`-style hand-waving.

### Tweet 5

Quick start:

```bash
pipx install opendivination
npx skills add amenti-labs/opendivination --skill divination
opendivination setup
opendivination draw tarot --json
```

## Anthropic Discord / project-sharing

Built a public skill + SDK called OpenDivination:

- tarot and I Ching
- agent-installable skill bundle
- auditable entropy provenance
- optional QRNG / QCicada support

Main idea is simple: if an agent or app is going to do divination digitally, the randomness layer should be explicit instead of hidden.

Repo: https://github.com/amenti-labs/opendivination

## Product Hunt

### Name

OpenDivination

### Tagline

Tarot and I Ching SDK with auditable entropy provenance

### Description

OpenDivination is an open-source CLI, Python SDK, and installable agent skill for tarot and I Ching. It supports standard computer RNG, remote QRNG providers, and local hardware entropy sources, and every draw includes a provenance receipt showing where the entropy came from and whether it was quantum.

### Maker comment

I built this because almost every digital divination tool hides the randomness layer completely.

OpenDivination does the opposite: it makes entropy provenance explicit. If you use normal computer RNG, it says that. If you use a quantum source, it says that too.

The point is not to overclaim what divination “is.” The point is to make the mechanism inspectable.
