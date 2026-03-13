# OpenDivine

**The first open-source oracle SDK powered by genuine quantum entropy**

[![PyPI version](https://img.shields.io/pypi/v/opendivine)](https://pypi.org/project/opendivine/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/amentilabs/opendivine/actions/workflows/ci.yml/badge.svg)](https://github.com/amentilabs/opendivine/actions)

---

There are 222 tarot repositories on GitHub. None of them use real quantum random number generation. They all call `random.choice()` or `Math.random()` and call it a day. OpenDivine is different.

OpenDivine replaces pseudorandom number generation with hardware quantum entropy: photon vacuum fluctuations, quantum tunneling events, and other physical processes that are genuinely non-deterministic. Every draw is backed by a provenance receipt that records exactly which entropy source was used, whether it was quantum, and the raw hex bytes that drove the selection. You can audit every result.

This is not a magic app. It's a rigorous, auditable system for structured reflection. The quantum entropy is real. The interpretive meaning is yours to construct. OpenDivine gives you the infrastructure to build divination software that's honest about what it is and transparent about how it works.

---

## Install

```bash
pip install opendivine

# With hardware QRNG support (requires Rust toolchain):
pip install opendivine[hardware]
```

---

## Quick Start

### Tarot

```python
from opendivine.oracles.tarot import draw_tarot_sync

result = draw_tarot_sync(source="csprng")
print(f"{result.card.name} ({result.orientation.value})")
print(f"Source: {result.provenance.source_id} (quantum: {result.provenance.is_quantum})")
```

### I Ching

```python
from opendivine.oracles.iching import draw_iching_sync

from opendivine.types import ICMethod

result = draw_iching_sync(method=ICMethod.YARROW, source="csprng")
print(f"#{result.primary.number}: {result.primary.name}")
if result.secondary:
    print(f"-> #{result.secondary.number}: {result.secondary.name}")
```

Pass `source="auto"` (or omit it entirely) to let the registry pick the best available quantum source automatically. Use `source="csprng"` for offline use or testing.

---

## Entropy Sources

| Source | ID | Type | Quantum | Notes |
|--------|----|------|---------|-------|
| openentropy | `openentropy` | Hardware | Yes | 60+ local hardware sources (optional, requires `[hardware]` extra) |
| ANU QRNG | `anu` | Network | Yes | Photon vacuum fluctuation |
| Qbert | `qbert` | Network | Yes | Quantum tunneling, raw (requires `QBERT_API_KEY`) |
| Outshift | `outshift` | Network | Yes | Cisco QRNG, DRBG post-processed (requires `OUTSHIFT_API_KEY`) |
| CSPRNG | `csprng` | Software | No | `os.urandom` fallback, always available |

Sources are tried in priority order. If a quantum source is unavailable, the system falls back automatically and records the actual source used in the provenance receipt. You always know what you got.

---

## CLI

```bash
opendivine draw tarot --source auto
opendivine draw iching --method yarrow
opendivine sources
opendivine version
```
---

## MCP Server

OpenDivine ships an MCP server for use with LLM agents (Claude, etc.). Start it with:

```bash
python3 -m opendivine.mcp
```

Add it to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "opendivine": {
      "command": "python3",
      "args": ["-m", "opendivine.mcp"]
    }
  }
}
```

Available tools: `draw_tarot`, `draw_iching`, `entropy_status`.

---

## Examples

The `examples/` directory has runnable scripts:

- `basic_draw.py` — tarot and I Ching draw with CSPRNG fallback
- `iching_changing_lines.py` — yarrow vs three-coin, changing lines, secondary hexagram
- `custom_source.py` — implement a custom `EntropySource`, register it, draw with it
- `provenance_audit.py` — draw tarot, print full provenance receipt as JSON

```bash
python3 examples/basic_draw.py
python3 examples/provenance_audit.py
```

---

## Architecture

```
Entropy Sources
  openentropy (hardware)
  ANU QRNG (network)
  Qbert (network)
  Outshift (network)
  CSPRNG (software fallback)
        |
        v
  Source Registry
  (auto-detect, priority chain, health checks)
        |
        v
  Oracle Engine
  (rejection sampling for unbiased selection)
        |
        v
  Provenance Receipt
  (source_id, is_quantum, raw_hex, timestamp, method)
        |
        v
  Result
  (card/hexagram + orientation + provenance)
```

The rejection sampling step is important. Naive modulo bias would skew results when the entropy range doesn't divide evenly into the symbol count. OpenDivine discards out-of-range bytes and resamples, ensuring every symbol has exactly equal probability.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and the PR process.

---

## License

MIT. See [LICENSE](LICENSE).
