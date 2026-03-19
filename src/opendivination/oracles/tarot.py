from __future__ import annotations

import asyncio
import os
import warnings

from opendivination.config import OpenDivinationConfig
from opendivination.core.provenance import create_provenance
from opendivination.core.registry import SourceRegistry
from opendivination.core.sampling import rejection_sample
from opendivination.corpora.tarot import load_tarot_corpus
from opendivination.embeddings import EmbeddingCache
from opendivination.oracles.resonance import (
    DEFAULT_RESONANCE_ENTROPY_BYTES,
    DEFAULT_RESONANCE_SHORTLIST_SIZE,
    draw_tarot_resonance,
    prepare_tarot_resonance_corpus,
)
from opendivination.types import (
    DEFAULT_ENTROPY_SOURCE,
    CoherenceResult,
    EmbeddingProvider,
    Orientation,
    ResonanceAssetTextProfile,
    ResonanceEntropyTextProfile,
    TarotCard,
    TarotDraw,
    TarotResonanceCorpusPreparation,
    TarotResonanceDraw,
)

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


async def _compute_tarot_coherence(
    card: TarotCard,
    question: str,
    provider: EmbeddingProvider,
    config: OpenDivinationConfig | None = None,
) -> CoherenceResult:
    from opendivination.core.coherence import compute_coherence
    from opendivination.oracles.tarot_text import build_tarot_card_text

    symbol_text = build_tarot_card_text(card, config=config)
    return await compute_coherence(
        question=question,
        symbol_text=symbol_text,
        provider=provider,
    )


async def draw_tarot(
    source: str | None = DEFAULT_ENTROPY_SOURCE,
    registry: SourceRegistry | None = None,
    *,
    question: str | None = None,
    provider: EmbeddingProvider | None = None,
    config: OpenDivinationConfig | None = None,
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

    coherence = None
    if question is not None and provider is None:
        warnings.warn(
            "question was provided without an embedding provider; "
            "coherence scoring requires both question and provider",
            stacklevel=2,
        )
    if question is not None and provider is not None:
        coherence = await _compute_tarot_coherence(
            card, question, provider, config
        )

    return TarotDraw(
        card=card, orientation=orientation, provenance=receipt, coherence=coherence
    )


async def draw_tarot_by_resonance(
    *,
    provider: EmbeddingProvider,
    source: str | None = DEFAULT_ENTROPY_SOURCE,
    registry: SourceRegistry | None = None,
    entropy_bytes: int = DEFAULT_RESONANCE_ENTROPY_BYTES,
    shortlist_size: int = DEFAULT_RESONANCE_SHORTLIST_SIZE,
    asset_text_profile: ResonanceAssetTextProfile = ResonanceAssetTextProfile.AUTO,
    entropy_text_profile: ResonanceEntropyTextProfile = ResonanceEntropyTextProfile.AUTO,
    cache: EmbeddingCache | None = None,
    config: OpenDivinationConfig | None = None,
    question: str | None = None,
) -> TarotResonanceDraw:
    active_registry = registry if registry is not None else _get_registry()
    entropy, source_info = await active_registry.get_bytes(entropy_bytes, source=source)
    result = await draw_tarot_resonance(
        provider=provider,
        raw_entropy=entropy,
        source_info=source_info,
        entropy_bytes=entropy_bytes,
        shortlist_size=shortlist_size,
        asset_text_profile=asset_text_profile,
        entropy_text_profile=entropy_text_profile,
        corpus=_get_corpus(),
        cache=cache,
        config=config,
    )

    if question is not None:
        coherence = await _compute_tarot_coherence(
            result.card, question, provider, config
        )
        result.coherence = coherence

    return result


async def prepare_tarot_resonance_corpus_embeddings(
    *,
    provider: EmbeddingProvider,
    asset_text_profile: ResonanceAssetTextProfile = ResonanceAssetTextProfile.AUTO,
    cache: EmbeddingCache | None = None,
    config: OpenDivinationConfig | None = None,
) -> TarotResonanceCorpusPreparation:
    preparation, _ = await prepare_tarot_resonance_corpus(
        provider=provider,
        asset_text_profile=asset_text_profile,
        corpus=_get_corpus(),
        cache=cache,
        config=config,
    )
    return preparation


def draw_tarot_sync(
    source: str | None = DEFAULT_ENTROPY_SOURCE,
    registry: SourceRegistry | None = None,
    *,
    question: str | None = None,
    provider: EmbeddingProvider | None = None,
    config: OpenDivinationConfig | None = None,
) -> TarotDraw:
    return asyncio.run(
        draw_tarot(
            source=source,
            registry=registry,
            question=question,
            provider=provider,
            config=config,
        )
    )


def draw_tarot_by_resonance_sync(
    *,
    provider: EmbeddingProvider,
    source: str | None = DEFAULT_ENTROPY_SOURCE,
    registry: SourceRegistry | None = None,
    entropy_bytes: int = DEFAULT_RESONANCE_ENTROPY_BYTES,
    shortlist_size: int = DEFAULT_RESONANCE_SHORTLIST_SIZE,
    asset_text_profile: ResonanceAssetTextProfile = ResonanceAssetTextProfile.AUTO,
    entropy_text_profile: ResonanceEntropyTextProfile = ResonanceEntropyTextProfile.AUTO,
    cache: EmbeddingCache | None = None,
    config: OpenDivinationConfig | None = None,
    question: str | None = None,
) -> TarotResonanceDraw:
    return asyncio.run(
        draw_tarot_by_resonance(
            provider=provider,
            source=source,
            registry=registry,
            entropy_bytes=entropy_bytes,
            shortlist_size=shortlist_size,
            asset_text_profile=asset_text_profile,
            entropy_text_profile=entropy_text_profile,
            cache=cache,
            config=config,
            question=question,
        )
    )


def prepare_tarot_resonance_corpus_embeddings_sync(
    *,
    provider: EmbeddingProvider,
    asset_text_profile: ResonanceAssetTextProfile = ResonanceAssetTextProfile.AUTO,
    cache: EmbeddingCache | None = None,
    config: OpenDivinationConfig | None = None,
) -> TarotResonanceCorpusPreparation:
    return asyncio.run(
        prepare_tarot_resonance_corpus_embeddings(
            provider=provider,
            asset_text_profile=asset_text_profile,
            cache=cache,
            config=config,
        )
    )


__all__ = [
    "draw_tarot",
    "draw_tarot_by_resonance",
    "draw_tarot_by_resonance_sync",
    "draw_tarot_sync",
    "prepare_tarot_resonance_corpus_embeddings",
    "prepare_tarot_resonance_corpus_embeddings_sync",
]
