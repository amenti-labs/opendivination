# OpenDivine v0.1 — Foundation Work Plan

## TL;DR

> **Quick Summary**: Build OpenDivine v0.1 — a Python oracle SDK that replaces PRNG with genuine quantum entropy for divination systems. Ships with Tarot (78 cards + Rider-Waite images + reversed), I Ching (64 hexagrams + changing lines with traditional probability models + SVG diagrams), four QRNG source adapters, a CLI, and an MCP server.
> 
> **Deliverables**:
> - `pip install opendivine` — Python package on PyPI
> - 4 QRNG sources: openentropy (optional hardware), ANU, Qbert, Outshift + CSPRNG fallback
> - Mode 1: Selection Oracle with rejection sampling, provenance receipts
> - Tarot: 78 cards × 2 orientations (156 states) with card images
> - I Ching: 64 hexagrams with full changing lines (yarrow stalk + three-coin methods)
> - CLI: `opendivine draw tarot`, `opendivine draw iching`, `opendivine sources`
> - MCP server: `draw_tarot`, `draw_iching`, `entropy_status` tools
> - Full OSS scaffolding: README, LICENSE, CI/CD, PyPI publishing
> 
> **Estimated Effort**: Large
> **Parallel Execution**: YES — 5 waves
> **Critical Path**: T1 → T2 → T8 → T14/T15 → T16/T17 → T18 → FINAL

---

## Context

### Original Request
Build an open-source oracle SDK called OpenDivine that applies genuine quantum entropy to divination systems. The first developer toolkit to replace PRNG with real QRNG in symbol-draw systems. v0.1 targets the foundation: entropy layer, two corpora (Tarot + I Ching with images), Selection Oracle mode, CLI, and MCP server.

### Interview Summary
**Key Discussions**:
- **Language**: Python (not TypeScript as originally in PLAN.md). openentropy provides Rust-speed entropy via PyO3 bindings. Python enables native embedding/LLM integration in future versions.
- **Architecture**: Fresh build referencing patterns from qrng-oracle predecessor (TypeScript). Don't fork/evolve.
- **openentropy bridge**: Use as pip dependency (optional extra `[hardware]`), not HTTP bridge.
- **Corpus images**: Ship actual Rider-Waite card art (public domain PNGs) and generated I Ching hexagram SVGs.
- **I Ching**: Full changing line mechanics with BOTH yarrow stalk and three-coin probability models.
- **Tarot**: Include upright/reversed orientation (156 total states).
- **MCP**: Ships from day one via Python FastMCP SDK.
- **Tests**: After implementation.

**Research Findings**:
- **openentropy** v0.12.3: 60+ hardware sources, EntropyPool.auto(), 3 conditioning modes (Raw/VonNeumann/Sha256), full Python bindings via PyO3, published on PyPI
- **qrng-oracle** predecessor: TypeScript patterns for BaseProvider, ProviderManager, oracle dispatch. Has ANU, Qbert, local providers. Code is reference, not reuse.
- **outshift-qrng-sdk**: Clean 196-line TypeScript client — port to Python
- **qbert**: REST API, invite-only, raw quantum tunneling, Crypta Labs Firefly hardware
- **ANU QRNG**: GET jsonI.php endpoint, photon vacuum fluctuation
- **openentropy-embed**: Full embedding pipeline (Qwen3-0.6B) — NOT in v0.1 scope
- **Existing adapters**: Quantum-random-vLLM-sampler has a 165-line Python openentropy wrapper with graceful import guard — follow this pattern

### Metis Review
**Identified Gaps** (all addressed):
- **Modulo bias**: `byte % 78` is NOT uniform (33% relative bias). → Rejection sampling for ALL draws.
- **collect_all() latency**: 1-10+ seconds kills CLI UX. → Short timeout (2s) + single fast source fallback.
- **openentropy platform coverage**: PyO3 wheels may not exist for all platforms. → Optional dependency with `[hardware]` extra.
- **I Ching probability model**: Traditional methods have non-uniform distributions. → Support both yarrow stalk and three-coin.
- **Tarot reversed**: Doubles state space. → Included in v0.1 per user decision.
- **Qbert API keys**: Can't ship in OSS. → Env var only (`QBERT_API_KEY`).
- **Image licensing**: Rider-Waite originals (Pamela Colman Smith, 1909) are public domain (pre-1923 US copyright). → Source verified PD set.
- **Package size**: ~8MB with images is acceptable (matplotlib ships ~40MB).

---

## Work Objectives

### Core Objective
Build the first production-quality Python SDK for quantum-entropy-powered divination, with two complete corpora, a CLI, and MCP server integration.

### Concrete Deliverables
- `opendivine` Python package on PyPI (v0.1.0)
- 4 QRNG source adapters + CSPRNG fallback
- Source registry with auto-detect and ordered fallback chain
- Tarot corpus: 78 cards with Rider-Waite card art, upright/reversed
- I Ching corpus: 64 hexagrams with SVG diagrams, yarrow/three-coin/uniform methods
- Provenance receipt on every draw
- CLI via Typer
- MCP server via FastMCP (stdio transport)
- GitHub repo with full OSS scaffolding + CI/CD

### Definition of Done
- [x] `pip install opendivine` succeeds in clean venv → prints version 0.1.0
- [x] `opendivine draw tarot` returns valid card + orientation + provenance in <3s
- [x] `opendivine draw iching` returns hexagram + changing lines + secondary hexagram
- [x] `opendivine draw iching --method yarrow` uses traditional yarrow stalk ratios
- [x] `opendivine sources` lists available entropy sources
- [x] MCP server responds to initialize + tool calls
- [x] 10,000 CSPRNG draws are approximately uniform (max/min ratio <1.5)
- [x] All tests pass with CSPRNG-only mode (no hardware, no network)
- [x] `ruff check` and `mypy` report zero errors

### Must Have
- Rejection sampling for ALL corpus draws (NEVER `value % N`)
- Every draw returns a ProvenanceReceipt (source, type, is_quantum, raw_hex, timestamp, quality)
- Graceful degradation: draws succeed even with no network and no hardware entropy
- openentropy optional import guard (`_OPENENTROPY_AVAILABLE` flag)
- API keys via environment variables only (QBERT_API_KEY, ANU_API_KEY, OUTSHIFT_API_KEY)
- I Ching changing lines: 0 changing lines (valid, no secondary) through 6 (valid, full complement)
- Tarot: both upright and reversed orientations
- CLI completes draws in <3 seconds (short timeout on source collection)

### Must NOT Have (Guardrails)
- ❌ Modes 2-8 (Resonance, Morphology, Waveform, Timing, Sigil, Convergence, ARV) — not even stubs
- ❌ Pre-computed embeddings or ANY ML/embedding infrastructure (no torch, transformers, numpy)
- ❌ LLM adapters or card interpretation/meaning generation
- ❌ REST API server
- ❌ Additional corpora (Runes, Lenormand, Ogham, Geomancy, Numerology)
- ❌ Research layer, Jupyter notebooks, experiment infrastructure
- ❌ EntropyFeatures extraction (FFT, moments, autocorrelation)
- ❌ Spread layouts or multi-card reading logic
- ❌ Hardcoded API keys for any QRNG service
- ❌ Interactive TUI, animated output, or web server from CLI
- ❌ `value % N` for card selection (modulo bias)
- ❌ Card interpretation text, reading logic, or AI-generated meanings
- ❌ Blockchain entropy source
- ❌ Website, docs site, or consumer app

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (greenfield)
- **Automated tests**: Tests after implementation
- **Framework**: pytest
- **Setup included**: Task T18 sets up pytest + conftest

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI**: Use Bash — run commands, assert JSON output fields, check exit codes
- **Python API**: Use Bash (python3 -c "...") — import, call functions, assert results
- **MCP**: Use Bash — pipe JSON-RPC to stdin, parse stdout response
- **Source adapters**: Use Bash (python3) — instantiate, call get_bytes(), verify length

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation, 6 parallel):
├── T1:  Project scaffolding (pyproject.toml, src layout, tooling) [quick]
├── T2:  Core type definitions (all dataclasses + protocols) [quick]
├── T3:  CSPRNG source adapter (os.urandom fallback) [quick]
├── T4:  Tarot corpus data + Rider-Waite images [unspecified-high]
├── T5:  I Ching corpus data + hexagram SVGs [unspecified-high]
└── T6:  OSS scaffolding (README, LICENSE, CONTRIBUTING, templates) [writing]

Wave 2 (After Wave 1 — core engine, 7 parallel):
├── T7:  Rejection sampling utility (depends: T2) [deep]
├── T8:  Source registry + fallback chain (depends: T2, T3) [deep]
├── T9:  openentropy adapter (depends: T2) [unspecified-high]
├── T10: ANU QRNG adapter (depends: T2) [unspecified-high]
├── T11: Qbert QRNG adapter (depends: T2) [unspecified-high]
├── T12: Outshift QRNG adapter (depends: T2) [unspecified-high]
└── T13: Provenance receipt system (depends: T2) [quick]

Wave 3 (After Wave 2 — oracles, 2 parallel):
├── T14: Tarot selection oracle (depends: T4, T7, T8, T13) [deep]
└── T15: I Ching selection oracle + changing lines (depends: T5, T7, T8, T13) [deep]

Wave 4 (After Wave 3 — interfaces, 3 parallel):
├── T16: CLI via Typer (depends: T14, T15) [unspecified-high]
├── T17: MCP server via FastMCP (depends: T14, T15) [unspecified-high]
└── T18: Test suite + pytest setup (depends: T14, T15, T16, T17) [deep]

Wave 5 (After Wave 4 — CI + polish, 2 parallel):
├── T19: GitHub Actions CI/CD (depends: T18) [quick]
└── T20: Examples directory + README finalization (depends: T16, T17) [writing]

Wave FINAL (After ALL — independent review, 4 parallel):
├── F1: Plan compliance audit (oracle)
├── F2: Code quality review (unspecified-high)
├── F3: Real QA — run all acceptance criteria (unspecified-high)
└── F4: Scope fidelity check (deep)

Critical Path: T1 → T2 → T8 → T14 → T16 → T18 → T19 → FINAL
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 7 (Wave 2)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| T1 | — | T2-T20 (scaffolding) | 1 |
| T2 | T1 | T7-T15 | 1 |
| T3 | T1 | T8 | 1 |
| T4 | T1 | T14 | 1 |
| T5 | T1 | T15 | 1 |
| T6 | T1 | T20 | 1 |
| T7 | T2 | T14, T15 | 2 |
| T8 | T2, T3 | T14, T15 | 2 |
| T9 | T2 | T8 (registers into) | 2 |
| T10 | T2 | T8 (registers into) | 2 |
| T11 | T2 | T8 (registers into) | 2 |
| T12 | T2 | T8 (registers into) | 2 |
| T13 | T2 | T14, T15 | 2 |
| T14 | T4, T7, T8, T13 | T16, T17, T18 | 3 |
| T15 | T5, T7, T8, T13 | T16, T17, T18 | 3 |
| T16 | T14, T15 | T18, T20 | 4 |
| T17 | T14, T15 | T18, T20 | 4 |
| T18 | T14-T17 | T19 | 4 |
| T19 | T18 | FINAL | 5 |
| T20 | T16, T17, T6 | FINAL | 5 |
| F1-F4 | T19, T20 | — | FINAL |

### Agent Dispatch Summary

- **Wave 1**: 6 tasks — T1→`quick`, T2→`quick`, T3→`quick`, T4→`unspecified-high`, T5→`unspecified-high`, T6→`writing`
- **Wave 2**: 7 tasks — T7→`deep`, T8→`deep`, T9→`unspecified-high`, T10→`unspecified-high`, T11→`unspecified-high`, T12→`unspecified-high`, T13→`quick`
- **Wave 3**: 2 tasks — T14→`deep`, T15→`deep`
- **Wave 4**: 3 tasks — T16→`unspecified-high`, T17→`unspecified-high`, T18→`deep`
- **Wave 5**: 2 tasks — T19→`quick`, T20→`writing`
- **FINAL**: 4 tasks — F1→`oracle`, F2→`unspecified-high`, F3→`unspecified-high`, F4→`deep`

---

## TODOs

> Implementation + Test = ONE Task. EVERY task has QA Scenarios.


- [x] 1. Project Scaffolding

  **What to do**:
  - Create `pyproject.toml` with Hatchling build backend, project metadata (name=opendivine, version=0.1.0, python>=3.10, MIT license, author=Amenti Labs)
  - Dependencies: `httpx>=0.27` (HTTP clients), `typer[all]>=0.12` (CLI), `mcp>=1.0,<2.0` (MCP server), `pydantic>=2.8` (models)
  - Optional deps: `[hardware]` = `openentropy>=0.12`
  - Create `src/opendivine/__init__.py` exporting `__version__ = "0.1.0"` and public API
  - Create `src/opendivine/py.typed` marker
  - Create `ruff.toml` (target=py310, line-length=100, select=["E","F","I","UP","B","SIM"])
  - Create `mypy` config in pyproject.toml (strict=true, warn_return_any=true)
  - Create `.gitignore` (Python, venv, __pycache__, dist, *.egg-info, .mypy_cache, .ruff_cache)
  - Create `.editorconfig` (utf-8, lf, 4-space indent for Python)
  - Create empty subpackage `__init__.py` files for: core/, sources/, corpora/, corpora/tarot/, corpora/iching/, oracles/, cli/, mcp/
  - Entry points in pyproject.toml: `[project.scripts] opendivine = "opendivine.cli.main:app"`, `[project.entry-points.mcp] opendivine = "opendivine.mcp.server:mcp"`

  **Must NOT do**:
  - Do NOT add torch, transformers, numpy, or any ML dependencies
  - Do NOT create Mode 2-8 module placeholders
  - Do NOT configure publishing to PyPI yet (that's T19)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: Pure scaffolding, no domain expertise needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T2, T3, T4, T5, T6)
  - **Blocks**: All subsequent tasks (T2-T20)
  - **Blocked By**: None

  **References**:
  - **Pattern**: `/Users/erai/Repos/openentropy/pyproject.toml` — Hatchling/maturin packaging pattern (lines 1-50)
  - **Pattern**: `/Users/erai/Repos/outshift-qrng-sdk/package.json` — ESM exports pattern (adapt for Python)
  - **Pattern**: `/Users/erai/Repos/openentropy-embed/pyproject.toml` — Python src layout with optional deps (lines 1-44)
  - **WHY**: These show the established packaging conventions in the ecosystem

  **Acceptance Criteria**:
  - [ ] `python3 -m venv /tmp/od-scaffold && source /tmp/od-scaffold/bin/activate && pip install -e .` succeeds
  - [ ] `python3 -c "import opendivine; print(opendivine.__version__)"` prints `0.1.0`
  - [ ] `ruff check src/` reports 0 errors
  - [ ] `mypy src/opendivine/__init__.py` reports 0 errors

  **QA Scenarios:**
  ```
  Scenario: Clean pip install succeeds
    Tool: Bash
    Preconditions: No opendivine installed
    Steps:
      1. python3 -m venv /tmp/od-scaffold-test && source /tmp/od-scaffold-test/bin/activate
      2. pip install -e .
      3. python3 -c "import opendivine; print(opendivine.__version__)"
    Expected Result: Prints "0.1.0", exit code 0
    Failure Indicators: ImportError, version mismatch, pip install failure
    Evidence: .sisyphus/evidence/task-1-pip-install.txt

  Scenario: Subpackages importable
    Tool: Bash
    Preconditions: opendivine installed
    Steps:
      1. python3 -c "from opendivine import core, sources, corpora, oracles"
    Expected Result: No ImportError
    Evidence: .sisyphus/evidence/task-1-subpackages.txt
  ```

  **Commit**: YES
  - Message: `feat: project scaffolding with pyproject.toml and src layout`
  - Files: `pyproject.toml, src/opendivine/**/__init__.py, ruff.toml, .gitignore, .editorconfig`
  - Pre-commit: `pip install -e . && ruff check src/`

- [x] 2. Core Type Definitions

  **What to do**:
  - Create `src/opendivine/types.py` with ALL core types:
    - `class EntropySource(Protocol)`: `name: str`, `source_type: Literal["hardware","network","software"]`, `is_quantum: bool`, `async def get_bytes(n: int) -> bytes`, `async def is_available() -> bool`, `async def health_check() -> SourceHealth`
    - `@dataclass class SourceHealth`: `available: bool`, `quality_score: float`, `last_error: str | None`, `bytes_served: int`
    - `@dataclass class SourceInfo`: `name: str`, `source_type: str`, `is_quantum: bool`, `description: str`, `physics: str | None`
    - `@dataclass class ProvenanceReceipt`: `id: str`, `timestamp: str`, `source_id: str`, `source_type: str`, `is_quantum: bool`, `raw_entropy_hex: str`, `entropy_bits: int`, `quality_score: float`, `mode: str`, `corpus: str`, `result_summary: str`
    - `@dataclass class TarotCard`: `number: int`, `name: str`, `suit: str | None`, `arcana: Literal["major","minor"]`, `keywords: list[str]`, `image_path: str`
    - `class Orientation(Enum)`: `UPRIGHT = "upright"`, `REVERSED = "reversed"`
    - `@dataclass class TarotDraw`: `card: TarotCard`, `orientation: Orientation`, `provenance: ProvenanceReceipt`
    - `@dataclass class Trigram`: `name: str`, `character: str`, `attribute: str`, `image: str`, `lines: tuple[int, int, int]`
    - `class LineType(Enum)`: `OLD_YIN = 6` (changing yin→yang), `YOUNG_YANG = 7` (stable yang), `YOUNG_YIN = 8` (stable yin), `OLD_YANG = 9` (changing yang→yin)
    - `class ICMethod(Enum)`: `YARROW = "yarrow"`, `THREE_COIN = "three_coin"`, `UNIFORM = "uniform"`
    - `@dataclass class Hexagram`: `number: int`, `name: str`, `pinyin: str`, `character: str`, `upper_trigram: Trigram`, `lower_trigram: Trigram`, `judgment: str`, `image_path: str`
    - `@dataclass class IChingDraw`: `primary: Hexagram`, `lines: list[LineType]` (always 6), `changing_lines: list[int]` (0-indexed positions where line is old yin/old yang), `secondary: Hexagram | None` (None if no changing lines), `method: ICMethod`, `provenance: ProvenanceReceipt`
  - All types use `__slots__` where appropriate, full type annotations, docstrings

  **Must NOT do**:
  - Do NOT add embedding-related fields (no `embedding: list[float]`)
  - Do NOT add interpretation/meaning fields (no `meaning: str`, `reading: str`)
  - Do NOT import numpy, torch, or any ML libraries

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: Pure Python dataclass/protocol definitions

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T3, T4, T5, T6)
  - **Blocks**: T7-T15
  - **Blocked By**: T1 (needs package structure)

  **References**:
  - **Pattern**: `/Users/erai/Repos/qrng-oracle/src/types.ts` (lines 1-80) — TypeScript type hierarchy. Adapt to Python dataclasses.
  - **Pattern**: `/Users/erai/Repos/openentropy/crates/openentropy-core/src/source.rs` (lines 1-60) — SourceInfo, SourceCategory enums. Match field names where sensible.
  - **WHY**: qrng-oracle shows the proven type hierarchy for oracle SDKs. openentropy shows the source metadata pattern.

  **Acceptance Criteria**:
  - [ ] `python3 -c "from opendivine.types import TarotCard, IChingDraw, ProvenanceReceipt, EntropySource; print('OK')"` succeeds
  - [ ] `mypy src/opendivine/types.py` reports 0 errors
  - [ ] All dataclasses are JSON-serializable (via dataclasses.asdict)

  **QA Scenarios:**
  ```
  Scenario: All types importable and constructable
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.types import *
         card = TarotCard(number=0, name='The Fool', suit=None, arcana='major', keywords=['beginnings'], image_path='fool.png')
         print(card.name)
         "
    Expected Result: Prints "The Fool"
    Evidence: .sisyphus/evidence/task-2-types-construct.txt

  Scenario: Types are JSON-serializable
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.types import ProvenanceReceipt
         from dataclasses import asdict
         import json
         r = ProvenanceReceipt(id='test', timestamp='2026-01-01T00:00:00Z', source_id='csprng', source_type='software', is_quantum=False, raw_entropy_hex='deadbeef', entropy_bits=32, quality_score=0.5, mode='selection', corpus='tarot', result_summary='The Fool')
         print(json.dumps(asdict(r)))
         "
    Expected Result: Valid JSON string with all fields
    Evidence: .sisyphus/evidence/task-2-types-json.txt
  ```

  **Commit**: YES (groups with T1)
  - Message: `feat: project scaffolding and core types`
  - Files: `src/opendivine/types.py`

- [x] 3. CSPRNG Source Adapter

  **What to do**:
  - Create `src/opendivine/sources/base.py` with abstract helpers if needed
  - Create `src/opendivine/sources/csprng.py` implementing `EntropySource` protocol:
    - `name = "csprng"`, `source_type = "software"`, `is_quantum = False`
    - `get_bytes(n)`: return `os.urandom(n)`
    - `is_available()`: always True
    - `health_check()`: always healthy, quality_score=0.5 (honest about non-quantum)
  - This is the always-available fallback. It MUST never fail.

  **Must NOT do**:
  - Do NOT use `random.randbytes()` (not cryptographically secure)
  - Do NOT add any network calls or hardware access

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T2, T4, T5, T6)
  - **Blocks**: T8 (registry needs at least one source)
  - **Blocked By**: T1 (needs package structure)

  **References**:
  - **Pattern**: `/Users/erai/Repos/qrng-oracle/src/provider/base.ts` (lines 1-60) — BaseProvider pattern. Adapt to Python.
  - **WHY**: Shows the provider abstraction layer that all sources implement.

  **Acceptance Criteria**:
  - [ ] `python3 -c "from opendivine.sources.csprng import CSPRNGSource; import asyncio; s=CSPRNGSource(); b=asyncio.run(s.get_bytes(32)); assert len(b)==32; print('OK')"` succeeds

  **QA Scenarios:**
  ```
  Scenario: CSPRNG always returns requested bytes
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.sources.csprng import CSPRNGSource
         import asyncio
         s = CSPRNGSource()
         assert asyncio.run(s.is_available()) == True
         for n in [1, 32, 256, 1024]:
             b = asyncio.run(s.get_bytes(n))
             assert len(b) == n, f'Expected {n} bytes, got {len(b)}'
         h = asyncio.run(s.health_check())
         assert h.available == True
         assert h.quality_score == 0.5
         print('ALL PASS')
         "
    Expected Result: Prints "ALL PASS"
    Evidence: .sisyphus/evidence/task-3-csprng.txt
  ```

  **Commit**: YES (groups with T1, T2)
  - Message: `feat: project scaffolding and core types`
  - Files: `src/opendivine/sources/csprng.py, src/opendivine/sources/base.py`

- [x] 4. Tarot Corpus Data + Rider-Waite Images

  **What to do**:
  - Create `src/opendivine/corpora/tarot/data.json`: 78 cards with fields: `number` (0-77), `name`, `suit` (null for Major Arcana, else Wands/Cups/Swords/Pentacles), `arcana` (major/minor), `keywords` (3-5 per card), `image_file` (filename reference)
  - Major Arcana: 0-The Fool through 21-The World (22 cards)
  - Minor Arcana: Ace through King in each of 4 suits (56 cards)
  - Source verified public domain Rider-Waite-Smith card images (Pamela Colman Smith originals, 1909, pre-1923 US copyright)
  - Place images in `src/opendivine/corpora/tarot/images/` as PNGs, <50KB each (thumbnail resolution ~300px wide)
  - Create `src/opendivine/corpora/tarot/__init__.py` with `load_tarot_corpus() -> list[TarotCard]` using `importlib.resources.files()`
  - Total image budget: <5MB

  **Must NOT do**:
  - Do NOT include copyrighted interpretations or meanings (no book text)
  - Do NOT include spread layouts or reading positions
  - Do NOT download images at runtime — they ship in the package

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - Reason: Requires sourcing public domain images and creating structured JSON corpus

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T2, T3, T5, T6)
  - **Blocks**: T14 (tarot oracle)
  - **Blocked By**: T1 (needs package structure)

  **References**:
  - **External**: Rider-Waite-Smith originals are widely available in PD. Search for "Rider-Waite-Smith public domain PNG" or use a verified open-source tarot dataset.
  - **Pattern**: `/Users/erai/Repos/openentropy-embed/embed/openentropy_io.py` — Shows how to load data files from a Python package (adapt for importlib.resources)
  - **WHY**: The corpus loader must use importlib.resources for pip-installed package compatibility

  **Acceptance Criteria**:
  - [ ] `python3 -c "from opendivine.corpora.tarot import load_tarot_corpus; cards=load_tarot_corpus(); assert len(cards)==78; print(f'{len(cards)} cards loaded')"` prints `78 cards loaded`
  - [ ] All 78 card image files exist and are <50KB PNG
  - [ ] data.json validates: 22 major arcana + 56 minor arcana = 78

  **QA Scenarios:**
  ```
  Scenario: Tarot corpus loads all 78 cards with images
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.corpora.tarot import load_tarot_corpus
         from importlib.resources import files
         cards = load_tarot_corpus()
         assert len(cards) == 78, f'Expected 78, got {len(cards)}'
         major = [c for c in cards if c.arcana == 'major']
         minor = [c for c in cards if c.arcana == 'minor']
         assert len(major) == 22, f'Expected 22 major, got {len(major)}'
         assert len(minor) == 56, f'Expected 56 minor, got {len(minor)}'
         # Check an image exists
         import pathlib
         img_dir = files('opendivine.corpora.tarot') / 'images'
         assert (img_dir / cards[0].image_path).is_file(), 'First card image missing'
         print('ALL PASS')
         "
    Expected Result: Prints "ALL PASS"
    Evidence: .sisyphus/evidence/task-4-tarot-corpus.txt

  Scenario: No card has empty required fields
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.corpora.tarot import load_tarot_corpus
         for c in load_tarot_corpus():
             assert c.name, f'Card {c.number} has no name'
             assert c.keywords, f'Card {c.name} has no keywords'
             assert c.image_path, f'Card {c.name} has no image_path'
         print('ALL PASS')
         "
    Expected Result: Prints "ALL PASS"
    Evidence: .sisyphus/evidence/task-4-tarot-fields.txt
  ```

  **Commit**: YES
  - Message: `feat(corpora): tarot corpus with 78 Rider-Waite cards and images`
  - Files: `src/opendivine/corpora/tarot/`

- [x] 5. I Ching Corpus Data + Hexagram SVGs

  **What to do**:
  - Create `src/opendivine/corpora/iching/data.json`: 64 hexagrams with fields: `number` (1-64, King Wen order), `name` (English), `pinyin`, `character` (Chinese), `upper_trigram` (name), `lower_trigram` (name), `judgment` (brief public-domain text, NOT full Wilhelm/Baynes), `image_file`
  - Create `src/opendivine/corpora/iching/trigrams.json`: 8 trigrams with fields: `name`, `character`, `attribute`, `image` (natural image), `lines` (3-tuple of 0/1 for yin/yang)
  - Generate 64 hexagram SVG diagrams programmatically: 6 horizontal lines (solid=yang, broken=yin), clean black-on-white, ~100x150px viewBox
  - Place SVGs in `src/opendivine/corpora/iching/images/`
  - Create `src/opendivine/corpora/iching/__init__.py` with `load_iching_corpus() -> tuple[list[Hexagram], list[Trigram]]`
  - Include lookup: `hexagram_by_lines(upper: tuple[int,int,int], lower: tuple[int,int,int]) -> Hexagram` for deriving secondary hexagram from changed lines

  **Must NOT do**:
  - Do NOT include full Wilhelm/Baynes translation (copyrighted)
  - Do NOT include individual line texts (384 entries = scope inflation)
  - Do NOT include commentary or interpretation

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - Reason: Requires I Ching domain knowledge and SVG generation

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T2, T3, T4, T6)
  - **Blocks**: T15 (I Ching oracle)
  - **Blocked By**: T1 (needs package structure)

  **References**:
  - **External**: I Ching hexagram data is well-established. King Wen sequence (1-64), 8 trigrams (Qian, Kun, Zhen, Xun, Kan, Li, Gen, Dui). Public domain descriptions available.
  - **Pattern**: Same `importlib.resources.files()` pattern as T4
  - **WHY**: The hexagram_by_lines() lookup is CRITICAL for changing line mechanics — it converts changed lines to the secondary hexagram

  **Acceptance Criteria**:
  - [ ] `python3 -c "from opendivine.corpora.iching import load_iching_corpus; h,t=load_iching_corpus(); assert len(h)==64; assert len(t)==8; print(f'{len(h)} hexagrams, {len(t)} trigrams')"` prints `64 hexagrams, 8 trigrams`
  - [ ] All 64 SVG files exist in images/
  - [ ] `hexagram_by_lines((1,1,1),(1,1,1))` returns hexagram #1 (Qian/The Creative)

  **QA Scenarios:**
  ```
  Scenario: I Ching corpus complete and lookups work
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.corpora.iching import load_iching_corpus, hexagram_by_lines
         hexagrams, trigrams = load_iching_corpus()
         assert len(hexagrams) == 64
         assert len(trigrams) == 8
         # Qian (all yang) should be hexagram 1
         h1 = hexagram_by_lines((1,1,1), (1,1,1))
         assert h1.number == 1, f'Expected #1, got #{h1.number}'
         # Kun (all yin) should be hexagram 2
         h2 = hexagram_by_lines((0,0,0), (0,0,0))
         assert h2.number == 2, f'Expected #2, got #{h2.number}'
         print('ALL PASS')
         "
    Expected Result: Prints "ALL PASS"
    Evidence: .sisyphus/evidence/task-5-iching-corpus.txt
  ```

  **Commit**: YES
  - Message: `feat(corpora): I Ching corpus with 64 hexagrams, 8 trigrams, and SVG images`
  - Files: `src/opendivine/corpora/iching/`

- [x] 6. OSS Scaffolding

  **What to do**:
  - Create `README.md`: Project name + tagline + badges (PyPI version, Python version, License, CI status), "What is this" section, Install (`pip install opendivine`), Quick Start (3-line tarot draw, 3-line I Ching draw), Source table (hardware/network/software with quantum status), CLI usage, MCP usage, Architecture overview, Contributing link, License
  - Create `LICENSE`: MIT license, copyright Amenti Labs 2026
  - Create `CONTRIBUTING.md`: Development setup (clone, venv, pip install -e .[dev]), running tests, code style (ruff, mypy), PR process, commit message convention
  - Create `CODE_OF_CONDUCT.md`: Contributor Covenant v2.1
  - Create `CHANGELOG.md`: v0.1.0 (Unreleased) section with planned features
  - Create `SECURITY.md`: Responsible disclosure policy, contact email
  - Create `.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md`
  - Create `.github/PULL_REQUEST_TEMPLATE.md`

  **Must NOT do**:
  - Do NOT write documentation for Modes 2-8
  - Do NOT create a docs/ site or MkDocs config
  - Do NOT add emojis to documentation

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: []
  - Reason: Documentation-heavy task requiring technical writing

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1-T5)
  - **Blocks**: T20 (final README polish)
  - **Blocked By**: T1 (needs repo structure)

  **References**:
  - **Pattern**: `/Users/erai/Repos/openentropy/README.md` — High-quality OSS README in the same ecosystem
  - **Pattern**: `/Users/erai/Repos/openentropy/CONTRIBUTING.md` — Contributing guide pattern
  - **Pattern**: `/Users/erai/Repos/openentropy/CODE_OF_CONDUCT.md` — Contributor Covenant
  - **Pattern**: `/Users/erai/Repos/openentropy/SECURITY.md` — Security policy
  - **WHY**: Match the openentropy ecosystem's documentation standards

  **Acceptance Criteria**:
  - [ ] README.md exists with install, quickstart, source table, CLI usage sections
  - [ ] LICENSE contains MIT text with correct copyright
  - [ ] All .github templates exist

  **QA Scenarios:**
  ```
  Scenario: All OSS files present
    Tool: Bash
    Steps:
      1. for f in README.md LICENSE CONTRIBUTING.md CODE_OF_CONDUCT.md CHANGELOG.md SECURITY.md; do test -f "$f" || echo "MISSING: $f"; done
      2. test -f .github/ISSUE_TEMPLATE/bug_report.md || echo "MISSING: bug template"
      3. test -f .github/PULL_REQUEST_TEMPLATE.md || echo "MISSING: PR template"
    Expected Result: No "MISSING" output
    Evidence: .sisyphus/evidence/task-6-oss-files.txt
  ```

  **Commit**: YES
  - Message: `docs: OSS scaffolding (README, LICENSE, CONTRIBUTING, templates)`
  - Files: `README.md, LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, CHANGELOG.md, SECURITY.md, .github/`

- [x] 7. Rejection Sampling Utility

  **What to do**:
  - Create `src/opendivine/core/sampling.py` with:
    - `rejection_sample(entropy: bytes, max_value: int) -> tuple[int, int]`: Returns (selected_index, bytes_consumed). Uses rejection sampling to produce an unbiased integer in [0, max_value). Consumes only the minimum bytes needed.
    - Algorithm: Read ceil(log2(max_value)/8) bytes at a time. Interpret as big-endian unsigned int. If value < max_value * floor(256^k / max_value), accept. Otherwise reject and read more bytes.
    - `rejection_sample_weighted(entropy: bytes, weights: list[float]) -> tuple[int, int]`: Weighted selection for I Ching yarrow/three-coin methods. CDF-based with rejection sampling.
  - CRITICAL: NEVER use `value % max_value` — this introduces modulo bias
  - Must handle edge case: entropy buffer exhausted (raise EntropyExhaustedError)

  **Must NOT do**:
  - Do NOT fall back to `value % N` when rejection threshold exceeded
  - Do NOT use Python's `random` module

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - Reason: Mathematical correctness is critical. Rejection sampling must be provably unbiased.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T8-T13)
  - **Blocks**: T14, T15 (oracles depend on this)
  - **Blocked By**: T2 (needs types)

  **References**:
  - **Anti-pattern**: `/Users/erai/Repos/qrng-oracle/src/oracle/index.ts` (line ~76) — Uses `(bytes[0] | bytes[1]<<8 | ...) % options.length`. This has 33% relative bias for 78 cards. DO NOT COPY.
  - **External**: NIST SP 800-90A rejection sampling algorithm. Wikipedia "rejection sampling" for uniform integers.
  - **WHY**: The entire credibility of a "rigorous, auditable" oracle SDK depends on provably unbiased selection.

  **Acceptance Criteria**:
  - [ ] 10,000 samples from rejection_sample(os.urandom(100000), 78) produces all 78 values with max/min ratio < 1.5
  - [ ] rejection_sample with max_value=2 consumes exactly 1 byte per accepted sample (on average)

  **QA Scenarios:**
  ```
  Scenario: Rejection sampling is uniform for 78 (tarot)
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.core.sampling import rejection_sample
         from collections import Counter
         import os
         entropy = os.urandom(100000)
         counts = Counter()
         offset = 0
         for _ in range(10000):
             val, consumed = rejection_sample(entropy[offset:], 78)
             counts[val] += 1
             offset += consumed
         assert len(counts) == 78, f'Only {len(counts)} unique values'
         ratio = max(counts.values()) / min(counts.values())
         assert ratio < 1.5, f'Bias ratio {ratio:.2f} exceeds 1.5'
         print(f'ALL PASS: {len(counts)} values, ratio={ratio:.3f}')
         "
    Expected Result: Prints "ALL PASS" with 78 values and ratio < 1.5
    Evidence: .sisyphus/evidence/task-7-rejection-uniform.txt

  Scenario: Weighted sampling matches yarrow stalk distribution
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.core.sampling import rejection_sample_weighted
         from collections import Counter
         import os
         # Yarrow stalk weights: old_yin=1/16, young_yang=5/16, young_yin=7/16, old_yang=3/16
         weights = [1/16, 5/16, 7/16, 3/16]
         entropy = os.urandom(100000)
         counts = Counter()
         offset = 0
         for _ in range(10000):
             val, consumed = rejection_sample_weighted(entropy[offset:], weights)
             counts[val] += 1
             offset += consumed
         # Check proportions are within 20% of expected
         for i, w in enumerate(weights):
             observed = counts[i] / 10000
             assert abs(observed - w) < 0.05, f'Index {i}: expected ~{w:.3f}, got {observed:.3f}'
         print(f'ALL PASS: proportions within tolerance')
         "
    Expected Result: Prints "ALL PASS"
    Evidence: .sisyphus/evidence/task-7-weighted-sampling.txt
  ```

  **Commit**: YES
  - Message: `feat(core): rejection sampling utility for unbiased draws`
  - Files: `src/opendivine/core/sampling.py`

- [x] 8. Source Registry + Fallback Chain

  **What to do**:
  - Create `src/opendivine/core/registry.py` with:
    - `class SourceRegistry`: Manages registered entropy sources with ordered fallback
    - `register(source: EntropySource, priority: int)`: Add a source
    - `async auto_detect() -> list[SourceInfo]`: Check which sources are available
    - `async get_bytes(n: int, source: str | None = None) -> tuple[bytes, SourceInfo]`: Get entropy from specified source or first available in fallback order
    - Fallback order: 1) openentropy (hardware, if available), 2) ANU, 3) Qbert, 4) Outshift, 5) CSPRNG
    - `list_sources() -> list[SourceInfo]`: Return all registered sources with availability status
    - Short timeout (2s) for source availability checks to keep CLI fast
  - The registry is the single entry point for all entropy. Oracles never talk to sources directly.
  - Auto-register CSPRNG on init (always available)
  - Lazy-register network sources (check availability on first use)

  **Must NOT do**:
  - Do NOT make the fallback chain configurable via config files (env vars + API are enough)
  - Do NOT add connection pooling or persistent connections

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - Reason: Registry pattern with async availability checking and fallback logic requires careful design

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T7, T9-T13)
  - **Blocks**: T14, T15 (oracles get entropy through registry)
  - **Blocked By**: T2 (types), T3 (CSPRNG source)

  **References**:
  - **Pattern**: `/Users/erai/Repos/qrng-oracle/src/provider/manager.ts` (lines 30-184) — ProviderManager with fallback order, source selection, availability checking
  - **Pattern**: `/Users/erai/Repos/Quantum-random-vLLM-sampler/src/qr_sampler/entropy/openentropy.py` (lines 36-165) — Graceful import guard pattern for optional openentropy
  - **WHY**: qrng-oracle's manager shows the proven fallback pattern. vLLM sampler shows how to gracefully handle missing openentropy.

  **Acceptance Criteria**:
  - [ ] Registry with only CSPRNG registered returns bytes successfully
  - [ ] `get_bytes(32, source='nonexistent')` raises appropriate error
  - [ ] `list_sources()` returns at least CSPRNG

  **QA Scenarios:**
  ```
  Scenario: Registry falls back to CSPRNG
    Tool: Bash
    Steps:
      1. python3 -c "
         import asyncio
         from opendivine.core.registry import SourceRegistry
         from opendivine.sources.csprng import CSPRNGSource
         reg = SourceRegistry()
         reg.register(CSPRNGSource(), priority=99)
         data, info = asyncio.run(reg.get_bytes(32))
         assert len(data) == 32
         assert info.name == 'csprng'
         assert info.is_quantum == False
         sources = reg.list_sources()
         assert any(s.name == 'csprng' for s in sources)
         print('ALL PASS')
         "
    Expected Result: Prints "ALL PASS"
    Evidence: .sisyphus/evidence/task-8-registry-fallback.txt

  Scenario: Explicit source selection works
    Tool: Bash
    Steps:
      1. python3 -c "
         import asyncio
         from opendivine.core.registry import SourceRegistry
         from opendivine.sources.csprng import CSPRNGSource
         reg = SourceRegistry()
         reg.register(CSPRNGSource(), priority=99)
         data, info = asyncio.run(reg.get_bytes(32, source='csprng'))
         assert info.name == 'csprng'
         try:
             asyncio.run(reg.get_bytes(32, source='nonexistent'))
             assert False, 'Should have raised'
         except Exception:
             pass
         print('ALL PASS')
         "
    Expected Result: Prints "ALL PASS"
    Evidence: .sisyphus/evidence/task-8-source-select.txt
  ```

  **Commit**: YES
  - Message: `feat(core): source registry with fallback chain`
  - Files: `src/opendivine/core/registry.py`

- [x] 9. openentropy Adapter (Optional Hardware Source)

  **What to do**:
  - Create `src/opendivine/sources/openentropy_source.py` implementing `EntropySource`:
    - Optional import guard: `try: import openentropy; _AVAILABLE = True except ImportError: _AVAILABLE = False`
    - `name = "openentropy"`, `source_type = "hardware"`, `is_quantum = True` (when using QCicada or similar)
    - `is_available()`: Check `_AVAILABLE` flag, then try `EntropyPool.auto()` with short timeout
    - `get_bytes(n)`: `pool.collect_all(parallel=True, timeout=2.0)` then `pool.get_bytes(n, conditioning="sha256")`
    - `health_check()`: Use `pool.health_report()` to populate SourceHealth
    - Support conditioning mode override via constructor: `OpenEntropySource(conditioning="raw")`
    - Handle edge case: `collect_all()` returns 0 bytes → raise SourceUnavailableError

  **Must NOT do**:
  - Do NOT make openentropy a hard import (must work without it)
  - Do NOT use analysis functions (spectral, chaos, etc.) — those are v0.2+

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - Reason: Needs understanding of openentropy Python API and graceful degradation patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T7, T8, T10-T13)
  - **Blocks**: T8 (registers into registry)
  - **Blocked By**: T2 (types)

  **References**:
  - **Pattern**: `/Users/erai/Repos/Quantum-random-vLLM-sampler/src/qr_sampler/entropy/openentropy.py` (lines 36-165) — EXACT pattern to follow: graceful import, _AVAILABLE flag, collect_all with timeout, get_bytes, health_check with 8192-byte chunks
  - **API**: `/Users/erai/Repos/openentropy/openentropy/__init__.py` (lines 1-60) — Python API surface: EntropyPool.auto(), collect_all(), get_bytes(), health_report()
  - **WHY**: The vLLM sampler is a production-tested openentropy wrapper in Python — copy this pattern exactly.

  **Acceptance Criteria**:
  - [ ] Module imports successfully even without openentropy installed: `python3 -c "from opendivine.sources.openentropy_source import OpenEntropySource; print('OK')"`
  - [ ] `is_available()` returns False when openentropy not installed

  **QA Scenarios:**
  ```
  Scenario: Graceful degradation without openentropy
    Tool: Bash
    Steps:
      1. python3 -c "
         import asyncio
         from opendivine.sources.openentropy_source import OpenEntropySource
         src = OpenEntropySource()
         avail = asyncio.run(src.is_available())
         # In CI, openentropy may not be installed
         print(f'Available: {avail}')
         if not avail:
             print('Gracefully unavailable (no openentropy installed)')
         print('PASS')
         "
    Expected Result: No ImportError, prints either available status
    Evidence: .sisyphus/evidence/task-9-openentropy-graceful.txt
  ```

  **Commit**: YES
  - Message: `feat(sources): openentropy hardware adapter with graceful fallback`
  - Files: `src/opendivine/sources/openentropy_source.py`

- [x] 10. ANU QRNG Adapter

  **What to do**:
  - Create `src/opendivine/sources/anu.py` implementing `EntropySource`:
    - `name = "anu"`, `source_type = "network"`, `is_quantum = True`
    - Endpoint: `GET https://qrng.anu.edu.au/API/jsonI.php?length=N&type=uint8`
    - Response: `{"type":"uint8","length":N,"data":[...],"success":true}`
    - Use httpx async client for HTTP requests
    - Implement byte cache: fetch 1024 bytes at a time, serve from cache until depleted
    - `is_available()`: HEAD request with 2s timeout
    - `health_check()`: Check last successful request, track bytes served
    - API key via env var `ANU_API_KEY` (optional — ANU has a free tier)
    - Handle rate limiting gracefully (429 → backoff)

  **Must NOT do**:
  - Do NOT hardcode any API keys
  - Do NOT use requests library (use httpx for async)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocked By**: T2 (types)

  **References**:
  - **Pattern**: `/Users/erai/Repos/qrng-oracle/src/provider/api/anu.ts` (lines 30-105) — ANU adapter with cache pattern
  - **External**: ANU QRNG API docs at https://qrng.anu.edu.au/
  - **WHY**: qrng-oracle's ANU adapter is proven; port the cache + error handling pattern to Python.

  **Acceptance Criteria**:
  - [ ] Module imports without network: `python3 -c "from opendivine.sources.anu import ANUSource; print('OK')"`
  - [ ] Constructor accepts optional api_key parameter

  **QA Scenarios:**
  ```
  Scenario: ANU source constructs and has correct metadata
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.sources.anu import ANUSource
         src = ANUSource()
         assert src.name == 'anu'
         assert src.source_type == 'network'
         assert src.is_quantum == True
         print('PASS')
         "
    Expected Result: Prints "PASS"
    Evidence: .sisyphus/evidence/task-10-anu-construct.txt
  ```

  **Commit**: YES (groups with T11, T12)
  - Message: `feat(sources): ANU, Qbert, and Outshift QRNG adapters`
  - Files: `src/opendivine/sources/anu.py`

- [x] 11. Qbert QRNG Adapter

  **What to do**:
  - Create `src/opendivine/sources/qbert.py` implementing `EntropySource`:
    - `name = "qbert"`, `source_type = "network"`, `is_quantum = True`
    - Endpoint: `GET https://qbert.cipherstone.co/api/v1/random?type=uint8&length=N`
    - Auth: `X-API-Key` header from env var `QBERT_API_KEY`
    - Response: JSON array of uint8 values
    - Cache-on-connect pattern: fetch 1024 bytes on first request, serve from cache
    - Exponential backoff on failure, respect `Retry-After` header
    - Track `X-QRNG-Device` response header in health metadata
    - `is_available()`: Only if QBERT_API_KEY env var is set + health check passes

  **Must NOT do**:
  - Do NOT hardcode API keys or ship a shared community key

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocked By**: T2 (types)

  **References**:
  - **Pattern**: `/Users/erai/Repos/qrng-oracle/src/provider/api/qbert.ts` (lines 43-208) — Qbert adapter with cache-on-connect, backoff, Retry-After, device tracking
  - **API Spec**: `/Users/erai/Repos/qbert/API_GUIDE.md` (lines 53-120) — Endpoint docs, rate limits, response format
  - **WHY**: qrng-oracle's Qbert adapter is production-tested; port the pattern to Python httpx.

  **QA Scenarios:**
  ```
  Scenario: Qbert source requires API key
    Tool: Bash
    Steps:
      1. python3 -c "
         import asyncio, os
         os.environ.pop('QBERT_API_KEY', None)
         from opendivine.sources.qbert import QbertSource
         src = QbertSource()
         assert asyncio.run(src.is_available()) == False, 'Should be unavailable without key'
         print('PASS')
         "
    Expected Result: Prints "PASS"
    Evidence: .sisyphus/evidence/task-11-qbert-no-key.txt
  ```

  **Commit**: YES (groups with T10, T12)
  - Message: `feat(sources): ANU, Qbert, and Outshift QRNG adapters`
  - Files: `src/opendivine/sources/qbert.py`

- [x] 12. Outshift QRNG Adapter

  **What to do**:
  - Create `src/opendivine/sources/outshift.py` implementing `EntropySource`:
    - `name = "outshift"`, `source_type = "network"`, `is_quantum = True` (note: DRBG post-processed)
    - Endpoint: `POST https://api.qrng.outshift.com/api/v1/random_numbers`
    - Body: `{"number_of_bits": N*8, "number_of_samples": 1}`
    - Auth: `x-id-api-key` header from env var `OUTSHIFT_API_KEY` or `~/.config/qrng/outshift.json`
    - Port retry logic from TypeScript SDK: exponential backoff, max 3 retries
    - Port error hierarchy: AuthError, RateLimitError, ValidationError

  **Must NOT do**:
  - Do NOT hardcode API keys

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocked By**: T2 (types)

  **References**:
  - **Pattern**: `/Users/erai/Repos/outshift-qrng-sdk/src/client.ts` (lines 24-196) — EXACT source to port: POST endpoint, auth header, retry with backoff, config file at ~/.config/qrng/outshift.json
  - **Pattern**: `/Users/erai/Repos/outshift-qrng-sdk/src/types.ts` — Request/response types
  - **Pattern**: `/Users/erai/Repos/outshift-qrng-sdk/src/errors.ts` — Error hierarchy
  - **WHY**: Port the TypeScript SDK directly to Python, maintaining the same behavior and config file location.

  **QA Scenarios:**
  ```
  Scenario: Outshift source reads config file path
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.sources.outshift import OutshiftSource
         src = OutshiftSource()
         assert src.name == 'outshift'
         assert src.is_quantum == True
         print('PASS')
         "
    Expected Result: Prints "PASS"
    Evidence: .sisyphus/evidence/task-12-outshift-construct.txt
  ```

  **Commit**: YES (groups with T10, T11)
  - Message: `feat(sources): ANU, Qbert, and Outshift QRNG adapters`
  - Files: `src/opendivine/sources/outshift.py`

- [x] 13. Provenance Receipt System

  **What to do**:
  - Create `src/opendivine/core/provenance.py` with:
    - `create_provenance(source_info: SourceInfo, raw_entropy: bytes, mode: str, corpus: str, result_summary: str) -> ProvenanceReceipt`
    - Generates UUID v4 for `id`
    - ISO 8601 timestamp
    - Stores raw entropy as hex string
    - Computes `entropy_bits = len(raw_entropy) * 8`
    - `quality_score` from SourceHealth
    - `receipt_to_json(receipt: ProvenanceReceipt) -> str`: Pretty-printed JSON
    - `receipt_to_dict(receipt: ProvenanceReceipt) -> dict`: For embedding in API responses
  - Every draw MUST create a provenance receipt. This is non-optional.

  **Must NOT do**:
  - Do NOT add cryptographic signing (future feature)
  - Do NOT add receipt storage/persistence (future feature)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: Simple dataclass construction + JSON serialization

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocked By**: T2 (types)

  **References**:
  - **Pattern**: PLAN.md lines 192-213 — Provenance receipt format specification
  - **WHY**: The receipt format is defined in the project plan. Follow it exactly.

  **QA Scenarios:**
  ```
  Scenario: Provenance receipt has all required fields
    Tool: Bash
    Steps:
      1. python3 -c "
         from opendivine.core.provenance import create_provenance
         from opendivine.types import SourceInfo
         info = SourceInfo(name='csprng', source_type='software', is_quantum=False, description='OS CSPRNG', physics=None)
         receipt = create_provenance(info, b'\xde\xad\xbe\xef', 'selection', 'tarot', 'The Fool')
         assert receipt.id  # non-empty UUID
         assert receipt.timestamp  # ISO 8601
         assert receipt.source_id == 'csprng'
         assert receipt.is_quantum == False
         assert receipt.raw_entropy_hex == 'deadbeef'
         assert receipt.entropy_bits == 32
         assert receipt.mode == 'selection'
         assert receipt.corpus == 'tarot'
         print('ALL PASS')
         "
    Expected Result: Prints "ALL PASS"
    Evidence: .sisyphus/evidence/task-13-provenance.txt
  ```

  **Commit**: YES
  - Message: `feat(core): provenance receipt system for auditable draws`
  - Files: `src/opendivine/core/provenance.py`

- [x] 14. Tarot Selection Oracle

  **What to do**:
  - Create `src/opendivine/oracles/tarot.py` with:
    - `async def draw_tarot(source: str | None = None, registry: SourceRegistry | None = None) -> TarotDraw`:
      1. Get entropy bytes from registry (32+ bytes for rejection sampling headroom)
      2. Use `rejection_sample(entropy, 78)` to select card index (unbiased)
      3. Use 1 additional entropy bit for orientation (upright/reversed)
      4. Load card from tarot corpus
      5. Create ProvenanceReceipt with source metadata + raw entropy hex
      6. Return TarotDraw(card, orientation, provenance)
    - Default registry: create module-level registry with auto-detected sources
    - Convenience function: `draw_tarot_sync(source=None) -> TarotDraw` wrapping async
  - Verify: 78 × 2 = 156 possible outcomes, all reachable

  **Must NOT do**:
  - Do NOT add multi-card draws or spread logic (future feature)
  - Do NOT add card interpretation or meaning text
  - Do NOT use `value % 78`

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - Reason: Must correctly wire rejection sampling + provenance + corpus loading

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with T15)
  - **Blocks**: T16, T17, T18
  - **Blocked By**: T4 (corpus), T7 (sampling), T8 (registry), T13 (provenance)

  **References**:
  - **API**: `src/opendivine/core/sampling.py` — rejection_sample() from T7
  - **API**: `src/opendivine/core/registry.py` — SourceRegistry.get_bytes() from T8
  - **API**: `src/opendivine/core/provenance.py` — create_provenance() from T13
  - **API**: `src/opendivine/corpora/tarot/__init__.py` — load_tarot_corpus() from T4
  - **WHY**: This is the integration task — wires all Wave 1-2 components together.

  **Acceptance Criteria**:
  - [ ] 10,000 draws produce all 78 cards with max/min ratio <1.5
  - [ ] Both upright and reversed orientations appear in draws
  - [ ] Every draw includes complete ProvenanceReceipt

  **QA Scenarios:**
  ```
  Scenario: Tarot draw returns valid card with provenance
    Tool: Bash
    Steps:
      1. python3 -c "
         import asyncio
         from opendivine.oracles.tarot import draw_tarot
         result = asyncio.run(draw_tarot(source='csprng'))
         assert result.card.name, 'Card has no name'
         assert result.orientation.value in ('upright', 'reversed')
         assert result.provenance.source_id == 'csprng'
         assert result.provenance.is_quantum == False
         assert result.provenance.raw_entropy_hex, 'No raw entropy'
         print(f'Drew: {result.card.name} ({result.orientation.value})')
         print('PASS')
         "
    Expected Result: Prints card name, orientation, and "PASS"
    Evidence: .sisyphus/evidence/task-14-tarot-draw.txt

  Scenario: Tarot draws are uniform (no modulo bias)
    Tool: Bash
    Steps:
      1. python3 -c "
         import asyncio
         from opendivine.oracles.tarot import draw_tarot
         from collections import Counter
         cards = Counter()
         orientations = Counter()
         for _ in range(10000):
             r = asyncio.run(draw_tarot(source='csprng'))
             cards[r.card.number] += 1
             orientations[r.orientation.value] += 1
         assert len(cards) == 78, f'Only {len(cards)} unique cards'
         ratio = max(cards.values()) / min(cards.values())
         assert ratio < 1.5, f'Card bias ratio {ratio:.2f}'
         assert orientations['upright'] > 4000, 'Too few upright'
         assert orientations['reversed'] > 4000, 'Too few reversed'
         print(f'ALL PASS: {len(cards)} cards, ratio={ratio:.3f}, orientations={dict(orientations)}')
         "
    Expected Result: 78 cards, ratio < 1.5, ~50/50 orientations
    Evidence: .sisyphus/evidence/task-14-tarot-uniform.txt
  ```

  **Commit**: YES
  - Message: `feat(oracles): tarot selection oracle with rejection sampling`
  - Files: `src/opendivine/oracles/tarot.py`

- [x] 15. I Ching Selection Oracle + Changing Lines

  **What to do**:
  - Create `src/opendivine/oracles/iching.py` with:
    - `async def draw_iching(method: ICMethod = ICMethod.YARROW, source: str | None = None, registry: SourceRegistry | None = None) -> IChingDraw`:
      1. Get entropy bytes from registry
      2. For each of 6 lines, determine LineType using selected method:
         - **YARROW**: rejection_sample_weighted with weights [1/16, 5/16, 7/16, 3/16] mapping to [OLD_YIN(6), YOUNG_YANG(7), YOUNG_YIN(8), OLD_YANG(9)]
         - **THREE_COIN**: rejection_sample_weighted with weights [1/8, 3/8, 3/8, 1/8] mapping to same LineType values
         - **UNIFORM**: rejection_sample with max_value=4 (equal probability)
      3. Build primary hexagram from 6 lines (yin=0 for YIN types, yang=1 for YANG types)
      4. Identify changing lines (positions where line is OLD_YIN or OLD_YANG)
      5. If changing lines exist: flip those lines to get secondary hexagram lines, look up via `hexagram_by_lines()`
      6. Create ProvenanceReceipt
      7. Return IChingDraw(primary, lines, changing_lines, secondary, method, provenance)
    - `draw_iching_sync()` convenience wrapper
  - Edge cases: 0 changing lines (valid, secondary=None), 6 changing lines (valid, secondary=complement)

  **Must NOT do**:
  - Do NOT add line text interpretations
  - Do NOT add hexagram meaning generation
  - Do NOT hardcode hexagram lookup — use hexagram_by_lines() from corpus

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - Reason: Most complex oracle logic. Yarrow stalk probability model, changing lines, secondary hexagram derivation.

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with T14)
  - **Blocks**: T16, T17, T18
  - **Blocked By**: T5 (corpus), T7 (sampling), T8 (registry), T13 (provenance)

  **References**:
  - **External**: Yarrow stalk probabilities: P(old_yin)=1/16, P(young_yang)=5/16, P(young_yin)=7/16, P(old_yang)=3/16. Three-coin: P(old_yin)=1/8, P(young_yang)=3/8, P(young_yin)=3/8, P(old_yang)=1/8.
  - **API**: `src/opendivine/corpora/iching/__init__.py` — hexagram_by_lines() from T5
  - **WHY**: The I Ching is a binary system at its core — perfect QRNG fit. The yarrow stalk model is the most traditional and mathematically interesting.

  **Acceptance Criteria**:
  - [ ] Yarrow method produces line types with correct distribution (within 5% tolerance over 10k trials)
  - [ ] 0 changing lines produces secondary=None
  - [ ] 6 changing lines produces valid secondary hexagram
  - [ ] Primary and secondary are always valid hexagram numbers (1-64)

  **QA Scenarios:**
  ```
  Scenario: I Ching draw with yarrow stalk method
    Tool: Bash
    Steps:
      1. python3 -c "
         import asyncio
         from opendivine.oracles.iching import draw_iching
         from opendivine.types import ICMethod
         result = asyncio.run(draw_iching(method=ICMethod.YARROW, source='csprng'))
         assert 1 <= result.primary.number <= 64
         assert len(result.lines) == 6
         if result.changing_lines:
             assert result.secondary is not None
             assert 1 <= result.secondary.number <= 64
         else:
             assert result.secondary is None
         assert result.method == ICMethod.YARROW
         assert result.provenance.corpus == 'iching'
         print(f'Primary: #{result.primary.number} {result.primary.name}')
         print(f'Lines: {[l.value for l in result.lines]}')
         print(f'Changing: {result.changing_lines}')
         if result.secondary:
             print(f'Secondary: #{result.secondary.number} {result.secondary.name}')
         print('PASS')
         "
    Expected Result: Valid hexagram, lines, optional secondary, "PASS"
    Evidence: .sisyphus/evidence/task-15-iching-yarrow.txt

  Scenario: Yarrow stalk probabilities are correct
    Tool: Bash
    Steps:
      1. python3 -c "
         import asyncio
         from opendivine.oracles.iching import draw_iching
         from opendivine.types import ICMethod, LineType
         from collections import Counter
         counts = Counter()
         for _ in range(10000):
             r = asyncio.run(draw_iching(method=ICMethod.YARROW, source='csprng'))
             for line in r.lines:
                 counts[line] += 1
         total = sum(counts.values())  # 60000
         expected = {LineType.OLD_YIN: 1/16, LineType.YOUNG_YANG: 5/16, LineType.YOUNG_YIN: 7/16, LineType.OLD_YANG: 3/16}
         for lt, expected_p in expected.items():
             observed_p = counts[lt] / total
             assert abs(observed_p - expected_p) < 0.02, f'{lt}: expected ~{expected_p:.3f}, got {observed_p:.3f}'
         print('ALL PASS: yarrow stalk probabilities correct')
         "
    Expected Result: All line types within 2% of expected probabilities
    Evidence: .sisyphus/evidence/task-15-iching-probabilities.txt
  ```

  **Commit**: YES
  - Message: `feat(oracles): I Ching oracle with changing lines and traditional probability models`
  - Files: `src/opendivine/oracles/iching.py`

- [x] 16. CLI via Typer

  **What to do**:
  - Create `src/opendivine/cli/main.py` with Typer app:
    - `opendivine draw tarot [--source SOURCE] [--json] [--format human|json]`: Draw a tarot card. Default output: human-readable Rich format. `--json`: JSON output.
    - `opendivine draw iching [--method yarrow|three_coin|uniform] [--source SOURCE] [--json]`: Draw I Ching hexagram with changing lines.
    - `opendivine sources [--json]`: List available entropy sources with name, type, quantum status, availability.
    - `opendivine version`: Print version.
    - Human-readable output uses Rich library (comes with Typer[all]) for colored, formatted output.
    - JSON output uses `receipt_to_json()` from provenance system.
    - All draws must complete in <3 seconds (use short timeout on source collection).

  **Must NOT do**:
  - Do NOT add interactive TUI mode
  - Do NOT add animated loading spinners (simple status messages are fine)
  - Do NOT add web server launch from CLI

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - Reason: CLI integration with Rich output formatting

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with T17, T18)
  - **Blocks**: T18, T20
  - **Blocked By**: T14, T15 (oracles)

  **References**:
  - **Pattern**: `/Users/erai/Repos/openentropy/crates/openentropy-cli/src/main.rs` — CLI structure with subcommands (adapt for Typer)
  - **External**: Typer documentation at https://typer.tiangolo.com/
  - **WHY**: Match the openentropy CLI UX conventions (subcommands, --json flag).

  **Acceptance Criteria**:
  - [ ] `opendivine draw tarot --source csprng --json` returns valid JSON with card + provenance
  - [ ] `opendivine draw iching --source csprng --method yarrow --json` returns valid JSON
  - [ ] `opendivine sources --json` returns JSON array of sources
  - [ ] All commands complete in <3 seconds

  **QA Scenarios:**
  ```
  Scenario: CLI tarot draw returns valid JSON
    Tool: Bash
    Steps:
      1. opendivine draw tarot --source csprng --json | python3 -c "
         import sys, json
         d = json.load(sys.stdin)
         assert 'card' in d, 'No card field'
         assert 'orientation' in d, 'No orientation field'
         assert 'provenance' in d, 'No provenance field'
         assert d['provenance']['source_id'] == 'csprng'
         print(f'Drew: {d["card"]["name"]} ({d["orientation"]})')
         print('PASS')
         "
    Expected Result: Card name, orientation, "PASS"
    Evidence: .sisyphus/evidence/task-16-cli-tarot.txt

  Scenario: CLI sources lists available sources
    Tool: Bash
    Steps:
      1. opendivine sources --json | python3 -c "
         import sys, json
         sources = json.load(sys.stdin)
         assert isinstance(sources, list)
         names = [s['name'] for s in sources]
         assert 'csprng' in names, 'CSPRNG not listed'
         print(f'Sources: {names}')
         print('PASS')
         "
    Expected Result: List including 'csprng', "PASS"
    Evidence: .sisyphus/evidence/task-16-cli-sources.txt
  ```

  **Commit**: YES
  - Message: `feat(cli): Typer CLI for tarot, iching, and source listing`
  - Files: `src/opendivine/cli/main.py`

- [x] 17. MCP Server via FastMCP

  **What to do**:
  - Create `src/opendivine/mcp/server.py` with FastMCP:
    - `mcp = FastMCP("opendivine")`
    - Tool `draw_tarot(source: str | None = None) -> dict`: Draws a tarot card, returns card + orientation + provenance as dict. Docstring explains the tool for LLM agents.
    - Tool `draw_iching(method: str = "yarrow", source: str | None = None) -> dict`: Draws I Ching hexagram with changing lines.
    - Tool `entropy_status() -> dict`: Returns available sources and their status.
    - Transport: stdio (default, compatible with Claude Desktop)
    - Add to pyproject.toml entry point: `[project.entry-points.mcp] opendivine = "opendivine.mcp.server:mcp"`
    - Alternatively runnable via: `python3 -m opendivine.mcp`

  **Must NOT do**:
  - Do NOT add MCP resources or prompts (tools only for v0.1)
  - Do NOT add HTTP transport configuration
  - Do NOT exceed 5 tools

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - Reason: Needs understanding of MCP SDK patterns

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with T16, T18)
  - **Blocks**: T18, T20
  - **Blocked By**: T14, T15 (oracles)

  **References**:
  - **External**: Python MCP SDK (FastMCP) — `from mcp.server.fastmcp import FastMCP`, `@mcp.tool()` decorator
  - **Pattern**: Any existing MCP server using FastMCP pattern (mcp package on PyPI)
  - **WHY**: MCP is a key differentiator — no other divination tool ships as an MCP server.

  **Acceptance Criteria**:
  - [ ] MCP server responds to initialize request via stdio
  - [ ] `draw_tarot` tool returns valid card data
  - [ ] `entropy_status` tool returns source list

  **QA Scenarios:**
  ```
  Scenario: MCP server initializes and lists tools
    Tool: Bash
    Steps:
      1. echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | python3 -m opendivine.mcp 2>/dev/null | head -1 | python3 -c "
         import sys, json
         line = sys.stdin.readline()
         d = json.loads(line)
         assert 'result' in d, 'No result in response'
         print('MCP INITIALIZE: PASS')
         "
    Expected Result: Valid MCP initialize response
    Evidence: .sisyphus/evidence/task-17-mcp-init.txt
  ```

  **Commit**: YES
  - Message: `feat(mcp): MCP server with draw_tarot, draw_iching, entropy_status tools`
  - Files: `src/opendivine/mcp/server.py, src/opendivine/mcp/__main__.py`

- [x] 18. Test Suite + pytest Setup

  **What to do**:
  - Create `tests/conftest.py` with:
    - `csprng_registry` fixture: SourceRegistry with only CSPRNG registered (no network, no hardware)
    - `tarot_corpus` fixture: loaded tarot cards
    - `iching_corpus` fixture: loaded hexagrams + trigrams
  - Create test files:
    - `tests/test_sampling.py`: Test rejection_sample uniformity (78, 64, 2, 4), test rejection_sample_weighted with known weights, test edge cases (max_value=1, empty entropy)
    - `tests/test_sources.py`: Test CSPRNG always available, returns correct length, openentropy graceful import guard
    - `tests/test_tarot.py`: Test corpus loads 78 cards (22 major + 56 minor), test draw returns valid card + orientation + provenance, test 1000-draw uniformity
    - `tests/test_iching.py`: Test corpus loads 64 hexagrams + 8 trigrams, test hexagram_by_lines lookup, test all 3 methods produce valid output, test 0 and 6 changing lines edge cases, test yarrow stalk probabilities
    - `tests/test_cli.py`: Test CLI commands via subprocess (draw tarot --json, draw iching --json, sources --json), test --source flag
    - `tests/test_mcp.py`: Test MCP server import, test tool registration
    - `tests/test_provenance.py`: Test receipt creation, JSON serialization, all fields present
  - Add `[project.optional-dependencies] dev = ["pytest>=8.0", "pytest-asyncio>=0.24"]` to pyproject.toml
  - All tests MUST pass with CSPRNG-only mode (no hardware, no network)

  **Must NOT do**:
  - Do NOT mock network calls — test with CSPRNG-only mode instead
  - Do NOT require openentropy to be installed for tests to pass

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - Reason: Comprehensive test suite covering all modules with statistical validation

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with T16, T17)
  - **Blocks**: T19
  - **Blocked By**: T14, T15, T16, T17 (needs all implementation complete)

  **References**:
  - **Pattern**: `/Users/erai/Repos/outshift-qrng-sdk/test/` — vitest test patterns (adapt for pytest)
  - **Pattern**: `/Users/erai/Repos/openentropy-embed/tests/` — pytest patterns in the ecosystem
  - **WHY**: Tests must validate the core claims: unbiased draws, correct probability models, graceful fallback.

  **Acceptance Criteria**:
  - [ ] `pytest` passes with all tests green
  - [ ] `pytest --co` shows tests for all major modules
  - [ ] Tests complete in <30 seconds (no network calls)

  **QA Scenarios:**
  ```
  Scenario: Full test suite passes
    Tool: Bash
    Steps:
      1. pip install -e ".[dev]"
      2. pytest -v
    Expected Result: All tests pass, 0 failures
    Evidence: .sisyphus/evidence/task-18-pytest.txt
  ```

  **Commit**: YES
  - Message: `test: comprehensive test suite for all modules`
  - Files: `tests/`

- [x] 19. GitHub Actions CI/CD

  **What to do**:
  - Create `.github/workflows/ci.yml`:
    - Trigger: push to main, pull requests
    - Matrix: Python 3.10, 3.11, 3.12
    - Steps: checkout, setup-python, pip install -e ".[dev]", ruff check src/, mypy src/, pytest
  - Create `.github/workflows/publish.yml`:
    - Trigger: GitHub Release created
    - Uses Trusted Publishing (OIDC) for PyPI — no API tokens needed
    - Steps: checkout, setup-python, pip install build, python -m build, publish to PyPI via trusted publisher
  - Add status badges to README.md (CI, PyPI version)

  **Must NOT do**:
  - Do NOT configure PyPI API tokens (use Trusted Publishing OIDC)
  - Do NOT add deployment steps beyond PyPI

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with T20)
  - **Blocks**: FINAL
  - **Blocked By**: T18 (tests must exist first)

  **References**:
  - **Pattern**: `/Users/erai/Repos/openentropy/.github/` if it exists — CI patterns in the ecosystem
  - **External**: PyPI Trusted Publishing docs: https://docs.pypi.org/trusted-publishers/
  - **WHY**: Standard OSS CI + Trusted Publishing is the modern best practice.

  **Acceptance Criteria**:
  - [ ] `.github/workflows/ci.yml` validates with `actionlint` or equivalent
  - [ ] CI workflow includes ruff, mypy, and pytest steps

  **QA Scenarios:**
  ```
  Scenario: CI workflow files are valid YAML
    Tool: Bash
    Steps:
      1. python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('ci.yml: valid')"
      2. python3 -c "import yaml; yaml.safe_load(open('.github/workflows/publish.yml')); print('publish.yml: valid')"
    Expected Result: Both print "valid"
    Evidence: .sisyphus/evidence/task-19-ci-yaml.txt
  ```

  **Commit**: YES
  - Message: `ci: GitHub Actions for lint, test, and PyPI publish`
  - Files: `.github/workflows/ci.yml, .github/workflows/publish.yml`

- [x] 20. Examples Directory + README Finalization

  **What to do**:
  - Create `examples/` directory with:
    - `basic_draw.py`: Simple tarot draw (5 lines), I Ching draw (5 lines)
    - `iching_changing_lines.py`: Demonstrate yarrow vs three-coin methods, show changing lines and secondary hexagram
    - `custom_source.py`: Show how to implement a custom EntropySource and register it
    - `provenance_audit.py`: Show how to inspect provenance receipts
  - Update README.md with:
    - Finalized quick start code using actual working API
    - Badge URLs pointing to real CI and PyPI (placeholders until published)
    - MCP configuration example for Claude Desktop (claude_desktop_config.json snippet)
    - Complete source table with all 5 sources
    - Architecture diagram (text-based, no images)
  - Update CHANGELOG.md with actual v0.1.0 features

  **Must NOT do**:
  - Do NOT add examples for Modes 2-8
  - Do NOT add a docs/ site

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with T19)
  - **Blocks**: FINAL
  - **Blocked By**: T16, T17, T6 (needs CLI + MCP to be complete for accurate docs)

  **References**:
  - **Pattern**: `/Users/erai/Repos/openentropy/examples/` — Example scripts in the ecosystem
  - **WHY**: Examples are the most important documentation for an SDK. They must work end-to-end.

  **Acceptance Criteria**:
  - [ ] All example files run without error: `for f in examples/*.py; do python3 "$f" || exit 1; done`
  - [ ] README has install, quickstart, source table, CLI, MCP sections

  **QA Scenarios:**
  ```
  Scenario: All examples execute successfully
    Tool: Bash
    Steps:
      1. for f in examples/*.py; do echo "Running $f..."; python3 "$f" || echo "FAILED: $f"; done
    Expected Result: All examples run without error
    Evidence: .sisyphus/evidence/task-20-examples.txt
  ```

  **Commit**: YES
  - Message: `docs: examples and finalized README`
  - Files: `examples/, README.md, CHANGELOG.md`

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `ruff check src/` + `mypy src/` + `pytest`. Review all files for: `as Any`, `# type: ignore` without justification, bare `except:`, `print()` in library code, `value % N` for draws (CRITICAL: reject immediately). Check for unused imports, missing docstrings on public functions.
  Output: `Ruff [PASS/FAIL] | Mypy [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real QA** — `unspecified-high`
  Execute ALL acceptance criteria (AC-1 through AC-9) in a clean venv. Test cross-feature integration. Test edge cases: draw with no network, draw with invalid source name, I Ching with 0 and 6 changing lines, concurrent draws. Save evidence to `.sisyphus/evidence/final-qa/`.
  Output: `ACs [N/N pass] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual implementation. Verify 1:1 — everything in spec was built, nothing beyond spec was built. Check "Must NOT Have" compliance (no ML imports, no Modes 2-8, no hardcoded keys). Detect unaccounted files.
  Output: `Tasks [N/N compliant] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `feat: project scaffolding and core types` — pyproject.toml, src layout, types.py, csprng.py
- **Wave 1b**: `feat: tarot and iching corpora with images` — data files + images
- **Wave 1c**: `docs: OSS scaffolding` — README, LICENSE, CONTRIBUTING, etc.
- **Wave 2**: `feat: entropy source registry and QRNG adapters` — registry, ANU, Qbert, Outshift, openentropy, provenance
- **Wave 3**: `feat: tarot and iching selection oracles` — oracle logic, rejection sampling
- **Wave 4**: `feat: CLI and MCP server` — typer commands, fastmcp tools
- **Wave 4b**: `test: add pytest suite` — tests for all modules
- **Wave 5**: `ci: GitHub Actions for lint, test, publish` — workflows
- **Wave 5b**: `docs: examples and README finalization` — examples, final README

---

## Success Criteria

### Verification Commands
```bash
# Clean install
python3 -m venv /tmp/od-test && source /tmp/od-test/bin/activate && pip install -e . && python3 -c "import opendivine; print(opendivine.__version__)"
# Expected: 0.1.0

# Tarot draw
opendivine draw tarot --source csprng
# Expected: JSON with card name, orientation, provenance

# I Ching draw
opendivine draw iching --source csprng --method yarrow
# Expected: JSON with primary hexagram, changing lines, secondary hexagram

# Source listing
opendivine sources
# Expected: Table of available sources with type and quantum status

# Uniformity test
python3 -c "from opendivine.oracles.tarot import draw_tarot; from collections import Counter; c=Counter(draw_tarot(source='csprng').card.name for _ in range(10000)); print(f'Cards: {len(c)}, Ratio: {max(c.values())/min(c.values()):.2f}')"
# Expected: Cards: 78, Ratio: <1.50

# Lint + typecheck
ruff check src/ && mypy src/
# Expected: 0 errors

# Tests
pytest
# Expected: All pass
```

### Final Checklist
- [x] All "Must Have" items present and verified
- [x] All "Must NOT Have" items absent (grep confirms)
- [x] All tests pass with CSPRNG-only mode
- [x] `pip install -e .` succeeds in clean venv
- [x] CLI responds in <3 seconds
- [x] MCP server handles initialize + tool calls
- [x] Images load correctly via importlib.resources
- [x] Provenance receipt on every draw
- [x] Rejection sampling produces uniform distribution
