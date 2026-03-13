# OpenDivine v0.1 — Learnings

## [2026-03-12] Wave 1 Completed

### Package Layout
- `src/opendivine/` — src layout, Hatchling build backend
- All subpackages have `__init__.py`: core/, sources/, corpora/, corpora/tarot/, corpora/iching/, oracles/, cli/, mcp/
- `src/opendivine/py.typed` marker exists

### Tarot Corpus
- `src/opendivine/corpora/tarot/data.json` — 78 cards (22 major + 56 minor)
- Images are SVG placeholders saved as `.png` files (NOT real Rider-Waite PNGs — Wikimedia returned 403/429)
- `load_tarot_corpus()` uses `importlib.resources.files()` pattern
- Image field in data.json is `image_path` (not `image_file`)

### I Ching Corpus
- `src/opendivine/corpora/iching/data.json` — 64 hexagrams (King Wen order)
- `src/opendivine/corpora/iching/trigrams.json` — 8 trigrams
- SVG images generated programmatically (clean black-on-white line diagrams)
- `hexagram_by_lines((1,1,1),(1,1,1))` → #1 Qian, `hexagram_by_lines((0,0,0),(0,0,0))` → #2 Kun

### Types (src/opendivine/types.py)
- All 12 core types defined: EntropySource (Protocol), SourceHealth, SourceInfo, ProvenanceReceipt, TarotCard, Orientation, TarotDraw, Trigram, LineType, ICMethod, Hexagram, IChingDraw
- LineType: OLD_YIN=6, YOUNG_YANG=7, YOUNG_YIN=8, OLD_YANG=9
- ICMethod: YARROW, THREE_COIN, UNIFORM

### CSPRNG Source
- `src/opendivine/sources/csprng.py` — CSPRNGSource, quality_score=0.5
- Uses `os.urandom()`, always available

### CLI
- `src/opendivine/cli/main.py` — stub with only `version` command (T16 will fill this out)

### OSS Docs
- README.md, LICENSE, CONTRIBUTING.md exist
- `.github/` directory does NOT exist yet (T6 incomplete)
- CODE_OF_CONDUCT.md, CHANGELOG.md, SECURITY.md — check if they exist

### Git State
- No commits yet (all files exist but uncommitted)

## [2026-03-12] Task: T7
- Implemented unbiased rejection sampling in `src/opendivine/core/sampling.py` using threshold rejection (`threshold = floor(256^k / N) * N`) and fixed-size chunk reads with exact byte-consumption tracking.
- `max_value=1` short-circuits to `(0, 0)`; entropy exhaustion raises `EntropyExhaustedError`.
- Weighted sampling normalizes a float CDF, draws uniform integers via `rejection_sample(..., 2^16)`, and maps with `bisect_right` to avoid modulo bias and preserve deterministic entropy usage.
- LSP diagnostics are clean for the new module; verification evidence saved under `.sisyphus/evidence/task-7-rejection-uniform.txt` and `.sisyphus/evidence/task-7-weighted-sampling.txt`.

## [2026-03-12] Task: T8
- Added `SourceRegistry` in `src/opendivine/core/registry.py` with priority-based registration, availability auto-detection, explicit source selection, and fallback byte retrieval.
- Implemented required fallback chain ordering (`openentropy -> anu -> qbert -> outshift -> csprng`) via priority values, with optional-source import guards and always-on `CSPRNGSource` auto-registration at priority `99`.
- Enforced 2-second availability checks using `asyncio.wait_for(...)` and introduced `SourceNotFoundError` plus `NoSourceAvailableError` for deterministic failure behavior.
- QA evidence captured in `.sisyphus/evidence/task-8-registry-fallback.txt` and `.sisyphus/evidence/task-8-source-select.txt`; both scenarios passed.

## [2026-03-12] Task: T13
- Implemented provenance receipt system in `src/opendivine/core/provenance.py` with three core functions:
  - `create_provenance(source_info, raw_entropy, mode, corpus, result_summary)` generates UUID v4, ISO 8601 timestamp, hex-encoded entropy, and entropy bit count
  - `receipt_to_json(receipt)` serializes to pretty-printed JSON using `dataclasses.asdict()` and `json.dumps(indent=2)`
  - `receipt_to_dict(receipt)` converts to dict for API response embedding
- All SourceInfo fields properly mapped: name→source_id, source_type, is_quantum, quality_score
- QA verified: UUID generation, timestamp format, hex encoding, bit calculation, JSON/dict conversion
- LSP diagnostics clean; evidence saved to `.sisyphus/evidence/task-13-provenance.txt`

## [2026-03-12] Task: T10
- Created `src/opendivine/sources/anu.py` — ANUSource class implementing EntropySource protocol.
- Byte cache pattern: fetch 1024 bytes per API call via `_refill_cache()`, serve from `_cache` until depleted.
- httpx.AsyncClient for all HTTP (2s timeout on `is_available`, 10s on `_refill_cache`).
- Rate-limiting: 429 sets `_rate_limited` flag → `is_available()` returns False once, then resets for retry.
- API key: constructor param or `ANU_API_KEY` env var; passed as `x-api-key` header.
- quality_score=0.9 (ANU applies hash-based conditioning — not raw quantum, but still quantum-sourced).
- No network calls during import or construction — cache is empty until first `get_bytes()` call.
- Evidence: `.sisyphus/evidence/task-10-anu-construct.txt`

## [2026-03-12] Task: T11
- Created `src/opendivine/sources/qbert.py` — QbertSource class implementing EntropySource protocol.
- Endpoint: `GET https://qbert.cipherstone.co/api/v1/random?type=uint8&length=N`; auth via `X-API-Key` header.
- Cache-on-connect: first `get_bytes()` prefetches `max(n, 1024)` bytes; subsequent calls served from `_cache`.
- Exponential backoff: `_INITIAL_BACKOFF_S=1.0`, doubles per retry, capped at 60s, up to `_MAX_RETRIES=5`.
- Respects `Retry-After` header on HTTP 429 responses (float seconds) before falling back to backoff.
- Tracks `X-QRNG-Device` response header in `_last_device` (exposed via `last_device` property).
- `is_available()` returns `False` immediately if no API key — no network call, fits 2s registry timeout.
- `quality_score=1.0` — raw quantum tunneling entropy, no conditioning/hashing.
- Follows same pattern as ANUSource (T10): constructor takes optional `api_key`, falls back to env var.
- Key difference from TS reference: task spec uses `/api/v1/random` path (not bare `/?type=uint8&length=N`).
- Evidence: `.sisyphus/evidence/task-11-qbert-no-key.txt`

## [2026-03-12] Task: T9
- Created `src/opendivine/sources/openentropy.py` — OpenEntropySource class with graceful import guard.
- Import guard pattern: `try: from openentropy import EntropyPool` / `except ImportError: _OPENENTROPY_AVAILABLE = False`
- Constructor works without openentropy installed — sets `self._pool = None`, all methods degrade gracefully.
- Registry expects `opendivine.sources.openentropy` module path (NOT `openentropy_source.py`) — file at `sources/openentropy.py`.
- Registry calls `source_class()` with no args — constructor default `conditioning="sha256"` makes this work.
- `is_available()` uses `asyncio.to_thread(EntropyPool.auto)` wrapped in `asyncio.wait_for(..., timeout=2.0)` for non-blocking 2s probe.
- `get_bytes()` calls `pool.collect_all(parallel=True, timeout=2.0)` then `pool.get_bytes(n, conditioning=...)` — raises RuntimeError if 0 bytes.
- quality_score=0.95 when available (hardware quantum), 0.0 when unavailable.
- Evidence: `.sisyphus/evidence/task-9-openentropy-graceful.txt`

## [2026-03-12] Task: T12
- Created `src/opendivine/sources/outshift.py` — OutshiftSource class implementing EntropySource protocol.
- Ported from `outshift-qrng-sdk/src/client.ts`: POST endpoint, `x-id-api-key` auth header, exponential backoff retry.
- Error hierarchy ported from `errors.ts`: OutshiftError base, AuthError (401), ForbiddenError (403), ValidationError (422), RateLimitError (429), ServerError (5xx).
- API key resolution chain: constructor arg → `OUTSHIFT_API_KEY` env var → `~/.config/qrng/outshift.json` (reads `apiKey` or `api_key` field).
- Retry logic: max 3 retries, exponential backoff (1s, 2s, 4s capped at 10s), retries on network errors/429/5xx, immediate raise on 400/401/403/422.
- Cache-on-connect pattern matching ANU/Qbert: 1024-byte prefetch, serve from `_cache` until depleted.
- `is_available()` uses 1.5s timeout for health ping (fits 2s registry limit).
- quality_score=0.85 — honest about DRBG post-processing (not raw quantum like Qbert's 1.0, but higher than CSPRNG's 0.5).
- Body format: `{"number_of_bits": N*8, "number_of_samples": 1}` — single-sample request per the task spec.
- Ruff import sorting: avoid double blank lines between import block and first code section.
- Evidence: `.sisyphus/evidence/task-12-outshift-construct.txt`

## [2026-03-12] Task: T14
- Created `src/opendivine/oracles/tarot.py` with lazy module-level `_registry` and `_corpus` initialization helpers (`_get_registry()`, `_get_corpus()`).
- `draw_tarot(source=None, registry=None)` retrieves 64 entropy bytes from `SourceRegistry.get_bytes(...)`, selects card index via unbiased `rejection_sample(entropy, 78)`, derives orientation from one additional entropy bit, and returns `TarotDraw` with complete provenance.
- Provenance receipt uses `create_provenance(source_info, entropy[:bytes_consumed+1], "selection", "tarot", f"{card.name} ({orientation.value})")` so entropy usage is auditable and bounded to consumed bytes.
- Added `draw_tarot_sync(source=None)` convenience wrapper using `asyncio.run(draw_tarot(source=source))`.
- QA evidence saved: `.sisyphus/evidence/task-14-tarot-draw.txt` and `.sisyphus/evidence/task-14-tarot-uniform.txt` (10,000 draws covered all 78 cards, ratio < 1.5, upright/reversed both > 4000).


## [2026-03-12] Task: T15
- Added `src/opendivine/oracles/iching.py` with lazy module-level initialization for `SourceRegistry` and I Ching corpus loading.
- Implemented `draw_iching(...)` line sampling for all methods using required mappings:
  - YARROW weights `[1/16, 5/16, 7/16, 3/16]` -> `[OLD_YIN, YOUNG_YANG, YOUNG_YIN, OLD_YANG]`
  - THREE_COIN weights `[1/8, 3/8, 3/8, 1/8]` -> same mapping
  - UNIFORM via `rejection_sample(..., 4)` -> same index mapping
- Hexagram lookup uses `hexagram_by_lines(upper, lower)` with bottom-to-top line ordering (`upper=lines[3:6]`, `lower=lines[0:3]`).
- Changing lines tracked as 0-indexed positions for `OLD_YIN`/`OLD_YANG`; secondary is `None` with 0 changes and valid when changes exist (including 6 changing lines).
- Provenance uses consumed entropy bytes and records `mode=method.value`, `corpus='iching'`.
- Evidence: `.sisyphus/evidence/task-15-iching-yarrow.txt` and `.sisyphus/evidence/task-15-iching-probabilities.txt`.

## [2026-03-12] Task: T17
- Created `src/opendivine/mcp/server.py` — FastMCP server with 3 tools: `draw_tarot`, `draw_iching`, `entropy_status`.
- `_sanitize()` helper recursively converts `dataclasses.asdict()` output: Enum→.value, tuple→list, nested dicts/lists handled.
- `draw_iching` tool takes `method: str` (not ICMethod enum) and validates against `ICMethod` values before constructing.
- `entropy_status` creates a fresh `SourceRegistry()` per call — `list_sources()` returns all registered sources (no async availability check needed).
- `__main__.py` enables `python3 -m opendivine.mcp` invocation; just imports `mcp` and calls `mcp.run()`.
- MCP server responds correctly to `initialize` request via stdio (protocolVersion "2024-11-05", serverInfo name "opendivine").
- ANU QRNG may return 500 errors — tests should use `source='csprng'` for deterministic local testing.
- Evidence: `.sisyphus/evidence/task-17-mcp-init.txt`

## [2026-03-12] Task: T16
- Full CLI implemented in `src/opendivine/cli/main.py` with Typer: `draw tarot`, `draw iching`, `sources`, `version` commands.
- Subcommand pattern: `draw_app = typer.Typer()` + `app.add_typer(draw_app, name="draw")` for `opendivine draw tarot|iching`.
- `dataclasses.asdict()` does NOT convert Enum values to primitives. Must use `json.dumps(data, default=_json_default)` with custom handler returning `obj.value`.
- `--json/--no-json` Typer flag: use `output_json: bool = typer.Option(False, "--json/--no-json")` -- parameter name differs from CLI flag.
- Avoid `from __future__ import annotations` in Typer CLI files -- Typer uses runtime annotation inspection for argument parsing.
- `list_sources()` is sync and returns `available=False` for all sources (no network check). `auto_detect()` is async and checks real availability.
- Sources JSON uses `type` (not `source_type`) per API convention -- manual dict construction, not `dataclasses.asdict()`.
- All commands complete in ~0.13s with `--source csprng` (well under 3s requirement).
- Evidence: `.sisyphus/evidence/task-16-cli-tarot.txt` and `.sisyphus/evidence/task-16-cli-sources.txt`

## [2026-03-12] Task: T18
- Added a full pytest suite under `tests/` with focused modules: sampling, sources, tarot, iching, CLI, MCP, and provenance.
- `tests/conftest.py` now provides reusable fixtures for a CSPRNG-only registry plus tarot and I Ching corpus loading.
- Test reliability improvement: async behavior is tested via `asyncio.run(...)` wrappers so the suite remains green even when `pytest-asyncio` is not installed in the active interpreter.
- Statistical checks use bounded sample sizes (1000-5000) and broad but meaningful thresholds (chi-square / absolute probability deltas) to keep runtime fast and avoid flakiness.
- CLI tests run through subprocess calls to the installed `opendivine` entrypoint with `--json` output validation.
- Evidence file for this task: `.sisyphus/evidence/task-18-pytest.txt`.

## [2026-03-12] Task: T19

- Created `.github/workflows/ci.yml` — GitHub Actions CI workflow for lint, type check, and test.
  - Triggers on `push` to `main` and `pull_request` to `main`.
  - Matrix: Python 3.10, 3.11, 3.12 on ubuntu-latest.
  - Steps: checkout → setup-python → `pip install -e ".[dev]"` → `ruff check src/` → `mypy src/` → `pytest`.
  - Uses `actions/checkout@v4` and `actions/setup-python@v5`.
  - All steps run sequentially; pytest runs last to catch any issues.

- Created `.github/workflows/publish.yml` — GitHub Actions publish workflow for PyPI.
  - Triggers on `release: types: [published]` (GitHub Release published event).
  - Uses Trusted Publishing (OIDC) with `id-token: write` permission.
  - Environment: `pypi` (configured in GitHub repo settings for trusted publisher).
  - Steps: checkout → setup-python (3.12) → `pip install build` → `python -m build` → `pypa/gh-action-pypi-publish@release/v1`.
  - No API token configuration needed — OIDC handles authentication.

- Both YAML files validated with `yaml.safe_load()` — no syntax errors.
- Evidence saved to `.sisyphus/evidence/task-19-ci-yaml.txt`.

## T20: Examples and README finalization (2026-03-12)

### API patterns confirmed
- `draw_tarot_sync(source="csprng")` — always works, no network needed
- `draw_iching_sync(method=ICMethod.YARROW, source="csprng")` — method takes ICMethod enum, not string
- `receipt_to_json(receipt)` — returns pretty-printed JSON string (2-space indent)
- `SourceRegistry.register(source, priority=N)` — lower N = higher priority
- Custom sources: implement `name`, `source_type`, `is_quantum`, `description` as class attributes + `get_bytes`, `is_available`, `health_check` async methods
- Pass custom registry to `draw_tarot(registry=registry)` (async version), not to `draw_tarot_sync`

### IChingDraw fields
- `result.lines` — list of 6 LineType values, bottom to top
- `result.changing_lines` — list of 0-indexed positions that are changing
- `result.secondary` — None if no changing lines, Hexagram otherwise
- `result.primary.character` — Chinese character for the hexagram

### LineType enum values
- OLD_YIN = 6 (changing, becomes yang)
- YOUNG_YANG = 7 (stable yang)
- YOUNG_YIN = 8 (stable yin)
- OLD_YANG = 9 (changing, becomes yin)

### Registry internals
- Default sources registered: openentropy (10), anu (20), qbert (30), outshift (40), csprng (99)
- Optional sources silently skipped if import fails
- `_build_source_info` hardcodes quality_score=0.5 for csprng, 0.0 for others

### README update pattern
- Quick Start must use `source="csprng"` so copy-paste works offline
- Source table needs ID column (the string you pass to `source=`)
- MCP section: show both the CLI invocation AND the config JSON
