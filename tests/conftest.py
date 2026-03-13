from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from opendivine.core.registry import SourceRegistry
from opendivine.corpora.iching import load_iching_corpus
from opendivine.corpora.tarot import load_tarot_corpus
from opendivine.sources.csprng import CSPRNGSource


@pytest.fixture
def csprng_registry() -> SourceRegistry:
    registry = SourceRegistry()
    registry._sources.clear()
    registry.register(CSPRNGSource(), priority=99)
    return registry


@pytest.fixture
def tarot_corpus():
    return load_tarot_corpus()


@pytest.fixture
def iching_corpus():
    return load_iching_corpus()
