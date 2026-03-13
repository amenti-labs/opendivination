from __future__ import annotations

from collections import Counter
from os import urandom

import pytest

from opendivine.core.sampling import (
    EntropyExhaustedError,
    rejection_sample,
    rejection_sample_weighted,
)


def test_rejection_sample_rejects_then_accepts() -> None:
    index, consumed = rejection_sample(bytes([255, 5]), 10)
    assert index == 5
    assert consumed == 2


def test_rejection_sample_uniformity() -> None:
    counts: Counter[int] = Counter()
    samples = 5000

    for _ in range(samples):
        index, consumed = rejection_sample(urandom(4), 10)
        assert consumed >= 1
        counts[index] += 1

    expected = samples / 10
    chi_square = sum((counts[i] - expected) ** 2 / expected for i in range(10))
    assert chi_square < 35.0


def test_rejection_sample_weighted_distribution() -> None:
    weights = [1.0, 3.0, 6.0]
    counts: Counter[int] = Counter()
    samples = 5000

    for _ in range(samples):
        index, consumed = rejection_sample_weighted(urandom(6), weights)
        assert consumed >= 1
        counts[index] += 1

    observed = [counts[i] / samples for i in range(3)]
    expected = [0.1, 0.3, 0.6]
    for o, e in zip(observed, expected, strict=False):
        assert abs(o - e) < 0.05


def test_rejection_sample_weighted_invalid_weights() -> None:
    with pytest.raises(ValueError):
        rejection_sample_weighted(b"\x00\x01", [])

    with pytest.raises(ValueError):
        rejection_sample_weighted(b"\x00\x01", [0.0, 0.0])


def test_rejection_sample_entropy_exhausted() -> None:
    with pytest.raises(EntropyExhaustedError):
        rejection_sample(bytes([255]), 10)
