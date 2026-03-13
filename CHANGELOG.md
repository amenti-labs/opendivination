# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-12

### Added
- Entropy source registry with ordered fallback chain
- openentropy hardware adapter (optional, requires `[hardware]` extra)
- ANU QRNG network adapter (photon vacuum fluctuation)
- Qbert QRNG network adapter (quantum tunneling, requires `QBERT_API_KEY`)
- Outshift QRNG network adapter (Cisco QRNG, requires `OUTSHIFT_API_KEY`)
- CSPRNG software fallback (always available)
- Tarot corpus: 78 cards (22 major arcana + 56 minor arcana) with images
- I Ching corpus: 64 hexagrams with SVG diagrams and 8 trigrams
- Tarot selection oracle with rejection sampling (unbiased, no modulo bias)
- I Ching oracle with changing lines (yarrow stalk, three-coin, and uniform methods)
- Provenance receipt on every draw (source, quantum status, raw entropy hex, timestamp)
- CLI: `opendivine draw tarot`, `opendivine draw iching`, `opendivine sources`, `opendivine version`
- MCP server: `draw_tarot`, `draw_iching`, `entropy_status` tools (stdio transport)
- Full type annotations and mypy strict compliance
- Examples: `basic_draw.py`, `iching_changing_lines.py`, `custom_source.py`, `provenance_audit.py`

[0.1.0]: https://github.com/amentilabs/opendivine/releases/tag/v0.1.0
