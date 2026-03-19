from __future__ import annotations

import asyncio
from collections import Counter

from opendivination.corpora.tarot import get_card_image_path
from opendivination.oracles.tarot import draw_tarot
from opendivination.types import Orientation


def test_tarot_corpus_loads_78_cards(tarot_corpus) -> None:
    assert len(tarot_corpus) == 78
    numbers = {card.number for card in tarot_corpus}
    assert numbers == set(range(78))


def test_draw_tarot_valid_card_and_provenance(csprng_registry, tarot_corpus) -> None:
    result = asyncio.run(draw_tarot(source="csprng", registry=csprng_registry))
    assert result.card.number in {card.number for card in tarot_corpus}
    assert result.orientation in {Orientation.UPRIGHT, Orientation.REVERSED}

    image_path = get_card_image_path(result.card)
    assert image_path.exists()

    receipt = result.provenance
    assert receipt.source_id == "csprng"
    assert receipt.corpus == "tarot"
    assert receipt.mode == "selection"
    assert receipt.raw_entropy_hex


def test_draw_tarot_defaults_to_csprng(csprng_registry) -> None:
    result = asyncio.run(draw_tarot(registry=csprng_registry))
    assert result.provenance.source_id == "csprng"
    assert result.provenance.is_quantum is False


def test_tarot_1000_draw_uniformity(csprng_registry) -> None:
    async def _run_draws() -> Counter[int]:
        counts: Counter[int] = Counter()
        draws = 1000
        for _ in range(draws):
            result = await draw_tarot(source="csprng", registry=csprng_registry)
            counts[result.card.number] += 1
        return counts

    counts = asyncio.run(_run_draws())
    draws = 1000

    expected = draws / 78
    chi_square = sum((counts[i] - expected) ** 2 / expected for i in range(78))
    assert chi_square < 170.0
