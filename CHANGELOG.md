# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Coherence scoring: optional `--question` / `-q` flag on `draw tarot` and `draw iching` computes
  semantic similarity (0.0–1.0) between the user's question and the drawn symbol's text description
- `CoherenceResult` type with score, question hash (SHA-256, privacy-safe), provider, and model
- `compute_coherence()` function in `core/coherence.py` — corpus-agnostic, works with any embedding provider
- I Ching text builder (`oracles/iching_text.py`) for rendering hexagram data into embeddable text
- Unicode hexagram symbols (U+4DC0–U+4DFF) via `Hexagram.symbol` property, auto-computed from King Wen number
- Corpus NOTICE files documenting public domain status of tarot images and I Ching data
- Python 3.13 and 3.14 classifiers
- Enriched tarot corpus: description, reversed keywords, element, and astrological correspondence for all 78 cards
- Enriched I Ching corpus: image text (Da Xiang), expanded description, and changing line texts for all 64 hexagrams
- Warning emitted when `question` is provided without an embedding `provider`

### Changed
- Removed the MCP server package and `mcp` runtime dependency
- Added a portable `skills/divination/` bundle for Claude Code, Agent SDK-compatible agents, skills.sh, and OpenClaw/ClawHub
- Added a bundled helper runner so the skill resolves the best available CLI path deterministically
- Made the CLI plus skill bundle the canonical agent integration surface

## [0.1.0] - 2026-03-12

### Added
- Entropy source registry with ordered fallback chain
- openentropy hardware adapter (optional, requires `[hardware]` extra)
- ANU QRNG network adapter (photon vacuum fluctuation)
- Outshift QRNG network adapter (Cisco QRNG, requires `OUTSHIFT_API_KEY`)
- CSPRNG software fallback (always available)
- Tarot corpus: 78 cards (22 major arcana + 56 minor arcana) with images
- I Ching corpus: 64 hexagrams with SVG diagrams and 8 trigrams
- Tarot selection oracle with rejection sampling (unbiased, no modulo bias)
- I Ching oracle with changing lines (yarrow stalk, three-coin, and uniform methods)
- Provenance receipt on every draw (source, quantum status, raw entropy hex, timestamp)
- CLI: `opendivination draw tarot`, `opendivination draw iching`, `opendivination sources`, `opendivination version`
- Full type annotations and mypy strict compliance
- Examples: `basic_draw.py`, `iching_changing_lines.py`, `custom_source.py`, `provenance_audit.py`

[0.1.0]: https://github.com/amentilabs/opendivination/releases/tag/v0.1.0
