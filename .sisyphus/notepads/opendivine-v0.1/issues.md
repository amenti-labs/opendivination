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
