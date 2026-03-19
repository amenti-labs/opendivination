from __future__ import annotations

import asyncio
from collections import Counter
from os import urandom

from opendivination.corpora.iching import hexagram_by_lines
from opendivination.oracles import iching as iching_module
from opendivination.oracles.iching import draw_iching
from opendivination.types import ICMethod, LineType


def test_iching_corpus_loads_64_hexagrams_and_8_trigrams(iching_corpus) -> None:
    hexagrams, trigrams = iching_corpus
    assert len(hexagrams) == 64
    assert len(trigrams) == 8


def test_hexagram_by_lines_lookup_known_values() -> None:
    qian = hexagram_by_lines((1, 1, 1), (1, 1, 1))
    kun = hexagram_by_lines((0, 0, 0), (0, 0, 0))
    assert qian.number == 1
    assert kun.number == 2


def test_draw_iching_all_methods(csprng_registry) -> None:
    for method in (ICMethod.YARROW, ICMethod.THREE_COIN, ICMethod.UNIFORM):
        result = asyncio.run(draw_iching(method=method, source="csprng", registry=csprng_registry))
        assert result.method == method
        assert len(result.lines) == 6
        assert result.primary.number in range(1, 65)
        assert result.provenance.source_id == "csprng"


def test_draw_iching_defaults_to_csprng(csprng_registry) -> None:
    result = asyncio.run(draw_iching(registry=csprng_registry))
    assert result.provenance.source_id == "csprng"
    assert result.provenance.is_quantum is False


def test_draw_iching_zero_changing_lines(monkeypatch, csprng_registry) -> None:
    def always_young_yang(entropy: bytes, method: ICMethod):
        return LineType.YOUNG_YANG, 1

    monkeypatch.setattr(iching_module, "_sample_line", always_young_yang)
    result = asyncio.run(
        draw_iching(method=ICMethod.YARROW, source="csprng", registry=csprng_registry)
    )
    assert result.changing_lines == []
    assert result.secondary is None


def test_draw_iching_six_changing_lines(monkeypatch, csprng_registry) -> None:
    def always_old_yin(entropy: bytes, method: ICMethod):
        return LineType.OLD_YIN, 1

    monkeypatch.setattr(iching_module, "_sample_line", always_old_yin)
    result = asyncio.run(
        draw_iching(method=ICMethod.YARROW, source="csprng", registry=csprng_registry)
    )
    assert result.changing_lines == [0, 1, 2, 3, 4, 5]
    assert result.secondary is not None


def test_yarrow_stalk_probabilities() -> None:
    counts: Counter[LineType] = Counter()
    samples = 5000

    for _ in range(samples):
        line, _ = iching_module._sample_line(urandom(4), ICMethod.YARROW)
        counts[line] += 1

    expected = {
        LineType.OLD_YIN: 1 / 16,
        LineType.YOUNG_YANG: 5 / 16,
        LineType.YOUNG_YIN: 7 / 16,
        LineType.OLD_YANG: 3 / 16,
    }

    for line_type, p in expected.items():
        observed = counts[line_type] / samples
        assert abs(observed - p) < 0.03
