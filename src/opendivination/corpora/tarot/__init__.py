"""Tarot corpus loader."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from opendivination.types import TarotCard


def load_tarot_corpus() -> list[TarotCard]:
    """Load all 78 Rider-Waite tarot cards."""
    data_file = files("opendivination.corpora.tarot") / "data.json"
    data = json.loads(data_file.read_text(encoding="utf-8"))
    visual_captions_file = files("opendivination.corpora.tarot") / "visual_captions.json"
    visual_captions: dict[str, str] = {}
    if visual_captions_file.is_file():
        visual_captions = json.loads(visual_captions_file.read_text(encoding="utf-8"))
    return [
        TarotCard(
            number=card["number"],
            name=card["name"],
            suit=card.get("suit"),
            arcana=card["arcana"],
            keywords=card["keywords"],
            image_path=card["image_file"],
            description=card.get("description"),
            reversed_keywords=card.get("reversed_keywords"),
            element=card.get("element"),
            astrological=card.get("astrological"),
            visual_caption=visual_captions.get(card["image_file"]),
        )
        for card in data
    ]


def get_card_image_path(card: TarotCard) -> Path:
    """Get the filesystem path to a card's image."""
    return Path(str(files("opendivination.corpora.tarot") / "images" / card.image_path))
