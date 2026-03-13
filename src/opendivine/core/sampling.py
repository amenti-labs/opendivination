from __future__ import annotations

import math
from bisect import bisect_right


class EntropyExhaustedError(Exception):
    pass


def rejection_sample(entropy: bytes, max_value: int) -> tuple[int, int]:
    """Sample an unbiased integer in ``[0, max_value)`` from raw entropy.

    The function reads fixed-size chunks from ``entropy`` and uses rejection
    sampling to avoid modulo bias.

    Args:
        entropy: Entropy buffer to consume.
        max_value: Exclusive upper bound of the sampled integer.

    Returns:
        A tuple of ``(index, bytes_consumed)``.

    Raises:
        ValueError: If ``max_value`` is less than 1.
        EntropyExhaustedError: If entropy is exhausted before acceptance.
    """
    if max_value < 1:
        raise ValueError("max_value must be >= 1")
    if max_value == 1:
        return (0, 0)

    bytes_needed = max(1, math.ceil((max_value - 1).bit_length() / 8))
    range_size = 1 << (8 * bytes_needed)
    threshold = (range_size // max_value) * max_value

    offset = 0
    entropy_len = len(entropy)
    while offset + bytes_needed <= entropy_len:
        value = int.from_bytes(entropy[offset : offset + bytes_needed], "big")
        offset += bytes_needed
        if value < threshold:
            return (value % max_value, offset)

    raise EntropyExhaustedError("Insufficient entropy bytes for rejection sampling")


def rejection_sample_weighted(entropy: bytes, weights: list[float]) -> tuple[int, int]:
    """Sample a weighted index from entropy using rejection-sampled uniform draw.

    Args:
        entropy: Entropy buffer to consume.
        weights: Non-negative weights; at least one must be greater than zero.

    Returns:
        A tuple of ``(index, bytes_consumed)``.

    Raises:
        ValueError: If weights are invalid.
        EntropyExhaustedError: If entropy is exhausted before acceptance.
    """
    if not weights:
        raise ValueError("weights must not be empty")
    if any((not math.isfinite(weight)) or weight < 0 for weight in weights):
        raise ValueError("weights must contain only finite, non-negative values")

    total_weight = sum(weights)
    if total_weight <= 0:
        raise ValueError("weights must contain at least one positive value")

    cumulative: list[float] = []
    running = 0.0
    for weight in weights:
        running += weight / total_weight
        cumulative.append(running)
    cumulative[-1] = 1.0

    scale = 1 << 16
    uniform_value, bytes_consumed = rejection_sample(entropy, scale)
    unit_value = uniform_value / scale
    index = bisect_right(cumulative, unit_value)

    if index >= len(weights):
        index = len(weights) - 1

    return (index, bytes_consumed)


__all__ = [
    "EntropyExhaustedError",
    "rejection_sample",
    "rejection_sample_weighted",
]
