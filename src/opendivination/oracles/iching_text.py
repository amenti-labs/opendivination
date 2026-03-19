"""I Ching hexagram text rendering helpers."""

from __future__ import annotations

from opendivination.types import Hexagram


def build_iching_hexagram_text(hexagram: Hexagram) -> str:
    """Build the text representation for an I Ching hexagram.

    Returns a single string suitable for embedding and coherence
    comparison.
    """
    parts = [
        f"I Ching hexagram #{hexagram.number} {hexagram.symbol}: {hexagram.name}",
        f"({hexagram.pinyin}, {hexagram.character}).",
        f"Upper trigram: {hexagram.upper_trigram}.",
        f"Lower trigram: {hexagram.lower_trigram}.",
        f"Judgment: {hexagram.judgment}.",
    ]
    if hexagram.image_text:
        parts.append(f"Image: {hexagram.image_text}")
    if hexagram.description:
        parts.append(hexagram.description)
    return " ".join(parts)


__all__ = ["build_iching_hexagram_text"]
