"""Tarot corpus loader."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from opendivine.types import TarotCard


def load_tarot_corpus() -> list[TarotCard]:
    """Load all 78 Rider-Waite tarot cards."""
    data_file = files("opendivine.corpora.tarot") / "data.json"
    data = json.loads(data_file.read_text(encoding="utf-8"))
    return [
        TarotCard(
            number=card["number"],
            name=card["name"],
            suit=card.get("suit"),
            arcana=card["arcana"],
            keywords=card["keywords"],
            image_path=card["image_file"],
        )
        for card in data
    ]


def get_card_image_path(card: TarotCard) -> Path:
    """Get the filesystem path to a card's image."""
    return Path(str(files("opendivine.corpora.tarot") / "images" / card.image_path))
