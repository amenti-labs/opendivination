from __future__ import annotations

import asyncio
import os

from opendivine.core.provenance import create_provenance
from opendivine.core.registry import SourceRegistry
from opendivine.core.sampling import rejection_sample
from opendivine.corpora.tarot import load_tarot_corpus
from opendivine.types import Orientation, TarotCard, TarotDraw

_registry: SourceRegistry | None = None
_corpus: list[TarotCard] | None = None


def _get_registry() -> SourceRegistry:
    global _registry
    if _registry is None:
        _registry = SourceRegistry()
    return _registry


def _get_corpus() -> list[TarotCard]:
    global _corpus
    if _corpus is None:
        _corpus = load_tarot_corpus()
    return _corpus


async def draw_tarot(
    source: str | None = None,
    registry: SourceRegistry | None = None,
) -> TarotDraw:
    active_registry = registry if registry is not None else _get_registry()
    entropy, source_info = await active_registry.get_bytes(64, source=source)

    card_index, bytes_consumed = rejection_sample(entropy, 78)
    orientation_byte = (
        entropy[bytes_consumed] if bytes_consumed < len(entropy) else os.urandom(1)[0]
    )
    orientation = Orientation.UPRIGHT if orientation_byte & 1 else Orientation.REVERSED

    corpus = _get_corpus()
    card = corpus[card_index]
    receipt = create_provenance(
        source_info,
        entropy[: bytes_consumed + 1],
        "selection",
        "tarot",
        f"{card.name} ({orientation.value})",
    )
    return TarotDraw(card=card, orientation=orientation, provenance=receipt)


def draw_tarot_sync(source: str | None = None) -> TarotDraw:
    return asyncio.run(draw_tarot(source=source))


__all__ = ["draw_tarot", "draw_tarot_sync"]
