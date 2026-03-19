# Contributing to OpenDivination

Thanks for your interest in contributing. This document covers development setup, code style, and the PR process.

---

## Development Setup

```bash
git clone https://github.com/amentilabs/opendivination.git
cd opendivination

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

The `[dev]` extra installs testing and linting dependencies. If you want hardware QRNG support locally:

```bash
pip install -e ".[dev,hardware]"
```

---

## Running Tests

```bash
pytest
```

For coverage:

```bash
pytest --cov=src/opendivination --cov-report=term-missing
```

Tests that require network access (ANU QRNG, Qbert, Outshift) are marked with `@pytest.mark.network` and skipped by default. Run them explicitly:

```bash
pytest -m network
```

---

## Code Style

We use `ruff` for linting and `mypy` for type checking.

```bash
ruff check src/
mypy src/
```

Format with:

```bash
ruff format src/
```

All public functions and classes need type annotations. The CI will fail without them.

If you change the bundled agent skill in `skills/divination/`, keep the instructions aligned
with the actual CLI and source selection behavior.

---

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Outshift entropy source
fix: correct rejection sampling boundary in tarot draw
docs: update entropy source table in README
test: add unit tests for provenance receipt serialization
ci: add mypy to pre-commit hooks
refactor: extract source registry into separate module
```

The type prefix matters. It drives the changelog and version bumps.

---

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Make your changes with tests
3. Run `ruff check src/`, `mypy src/`, and `pytest` locally
4. Open a PR against `main`
5. Fill out the PR template
6. A maintainer will review within a few days

Keep PRs focused. One logical change per PR. If you're fixing a bug and also refactoring something unrelated, split them.

---

## Adding a New Entropy Source

Entropy sources implement the `EntropySource` protocol defined in `src/opendivination/types.py`:

```python
class EntropySource(Protocol):
    name: str
    source_type: str  # "hardware" | "network" | "software"
    is_quantum: bool
    description: str

    async def get_bytes(self, n: int) -> bytes: ...
    async def is_available(self) -> bool: ...
    async def health_check(self) -> SourceHealth: ...
```

Steps:

1. Create `src/opendivination/sources/your_source.py`
2. Implement the protocol
3. Register it in `src/opendivination/core/registry.py`
4. Add tests in `tests/test_sources.py`
5. Update the entropy sources table in `README.md`

If your source requires an API key, follow the existing pattern: read from an environment variable, document it in the README, and never hardcode credentials.

---

## Reporting Issues

Use the GitHub issue templates. For security issues, see [SECURITY.md](SECURITY.md).
