from __future__ import annotations

import math


class EmbeddingError(RuntimeError):
    """Raised when an embedding provider cannot fulfill a request."""


def normalize_vector(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return [0.0 for _ in values]
    return [value / norm for value in values]


def cosine_similarity(lhs: list[float], rhs: list[float]) -> float:
    if len(lhs) != len(rhs):
        raise EmbeddingError(
            f"Cannot compare embeddings with different dimensions: {len(lhs)} != {len(rhs)}"
        )
    lhs_normalized = normalize_vector(lhs)
    rhs_normalized = normalize_vector(rhs)
    return sum(
        left * right
        for left, right in zip(lhs_normalized, rhs_normalized, strict=True)
    )
