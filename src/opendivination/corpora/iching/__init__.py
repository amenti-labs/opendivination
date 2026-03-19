"""I Ching corpus loader."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from opendivination.types import Hexagram, Trigram

_hexagrams: list[Hexagram] | None = None
_trigrams: dict[str, Trigram] | None = None
_lines_to_hexagram: dict[tuple[tuple[int, ...], tuple[int, ...]], Hexagram] | None = None


def load_iching_corpus() -> tuple[list[Hexagram], list[Trigram]]:
    """Load all 64 hexagrams and 8 trigrams."""
    global _hexagrams, _trigrams
    if _hexagrams is None:
        hex_file = files("opendivination.corpora.iching") / "data.json"
        tri_file = files("opendivination.corpora.iching") / "trigrams.json"

        hex_data = json.loads(hex_file.read_text(encoding="utf-8"))
        tri_data = json.loads(tri_file.read_text(encoding="utf-8"))

        _trigrams_list = [
            Trigram(
                name=t["name"],
                character=t["character"],
                attribute=t["attribute"],
                image=t["image"],
                lines=tuple(t["lines"]),
            )
            for t in tri_data
        ]
        _trigrams = {t.name: t for t in _trigrams_list}

        _hexagrams = [
            Hexagram(
                number=h["number"],
                name=h["name"],
                pinyin=h["pinyin"],
                character=h["character"],
                upper_trigram=h["upper_trigram"],
                lower_trigram=h["lower_trigram"],
                judgment=h["judgment"],
                image_path=h["image_file"],
                image_text=h.get("image_text"),
                description=h.get("description"),
                line_texts=h.get("line_texts"),
            )
            for h in hex_data
        ]

    return _hexagrams, list(_trigrams.values()) if _trigrams else []


def hexagram_by_lines(
    upper: tuple[int, int, int],
    lower: tuple[int, int, int],
) -> Hexagram:
    """Look up hexagram by upper and lower trigram lines.

    Args:
        upper: 3-tuple of 0/1 (yin/yang) for upper trigram, bottom to top
        lower: 3-tuple of 0/1 (yin/yang) for lower trigram, bottom to top

    Returns:
        The matching Hexagram

    Raises:
        ValueError: If no hexagram matches the given trigram lines.
    """
    global _lines_to_hexagram
    hexagrams, tri_list = load_iching_corpus()

    if _lines_to_hexagram is None:
        # Build lookup table
        _lines_to_hexagram = {}

        for h in hexagrams:
            upper_tri = next((t for t in tri_list if t.name == h.upper_trigram), None)
            lower_tri = next((t for t in tri_list if t.name == h.lower_trigram), None)
            if upper_tri and lower_tri:
                key = (tuple(upper_tri.lines), tuple(lower_tri.lines))
                _lines_to_hexagram[key] = h

    key = (tuple(upper), tuple(lower))
    if key not in _lines_to_hexagram:
        raise ValueError(f"No hexagram found for upper={upper}, lower={lower}")
    return _lines_to_hexagram[key]


def get_hexagram_image_path(hexagram: Hexagram) -> Path:
    """Get the filesystem path to a hexagram's SVG image."""
    return Path(str(files("opendivination.corpora.iching") / "images" / hexagram.image_path))
