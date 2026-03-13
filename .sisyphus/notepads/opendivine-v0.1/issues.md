# OpenDivine v0.1 — Issues & Gotchas

## [2026-03-12] Known Issues

### T6 Incomplete
- `.github/` directory missing (ISSUE_TEMPLATE/bug_report.md, feature_request.md, PULL_REQUEST_TEMPLATE.md)
- Need to check if CODE_OF_CONDUCT.md, CHANGELOG.md, SECURITY.md exist

### Tarot Images
- Images are SVG placeholders saved as `.png` (NOT real Rider-Waite PNGs)
- Wikimedia Commons returned 403/429 during T4
- Functionally correct for v0.1 — real images can replace later

### CLI Stub
- `src/opendivine/cli/main.py` only has `version` command
- T16 must add `draw tarot`, `draw iching`, `sources` commands

### No Commits Yet
- All Wave 1 files exist but no git commits
- First commit should happen after Wave 2 completes

### openentropy Not Installed in Dev Environment
- `openentropy` may not be installed — T9 adapter must handle gracefully
- Tests must pass with CSPRNG-only mode


## [2026-03-12] F1 Plan Compliance Audit Findings

- FAIL: Modulo operator present in core sampler: `src/opendivine/core/sampling.py:43` uses `value % max_value` (plan requires NEVER `value % N`).
- FAIL: README claims a research layer and references `experiments/` + `docs/research/` (forbidden by plan; also those paths do not exist): `README.md:156`.
- FAIL: Missing evidence files referenced by plan:
  - `.sisyphus/evidence/task-1-subpackages.txt`
  - `.sisyphus/evidence/task-2-types-json.txt`
  - `.sisyphus/evidence/task-4-tarot-fields.txt`
- NOTE: This notepad has stale items above (CLI + .github are now implemented in repo); treat earlier sections as historical.
