from __future__ import annotations

import hashlib
import json

from opendivination.config import OpenDivinationConfig
from opendivination.core.provenance import create_provenance
from opendivination.core.sampling import rejection_sample
from opendivination.corpora.tarot import load_tarot_corpus
from opendivination.embeddings import (
    EmbeddingCache,
    cache_key_for_content,
    cache_variant_id,
    cosine_similarity,
)
from opendivination.oracles.tarot_text import (
    build_tarot_card_text,
    configured_tarot_text_profiles,
)
from opendivination.types import (
    EmbeddingContent,
    EmbeddingProvider,
    EmbeddingTaskType,
    ResonanceAssetTextProfile,
    ResonanceEntropyTextProfile,
    SourceInfo,
    TarotCard,
    TarotResonanceCorpusPreparation,
    TarotResonanceDraw,
)

DEFAULT_RESONANCE_ENTROPY_BYTES = 256
DEFAULT_RESONANCE_SHORTLIST_SIZE = 3
DEFAULT_ASSET_TEXT_PROFILE = ResonanceAssetTextProfile.DESCRIPTIVE
DEFAULT_ENTROPY_TEXT_PROFILE = ResonanceEntropyTextProfile.BARE_HEX_SPACED


def _resolve_asset_text_profile(
    profile: ResonanceAssetTextProfile,
) -> ResonanceAssetTextProfile:
    if profile is ResonanceAssetTextProfile.AUTO:
        return DEFAULT_ASSET_TEXT_PROFILE
    return profile


def _resolve_entropy_text_profile(
    profile: ResonanceEntropyTextProfile,
) -> ResonanceEntropyTextProfile:
    if profile is ResonanceEntropyTextProfile.AUTO:
        return DEFAULT_ENTROPY_TEXT_PROFILE
    return profile


def build_entropy_text(
    raw_entropy: bytes,
    profile: ResonanceEntropyTextProfile = DEFAULT_ENTROPY_TEXT_PROFILE,
) -> str:
    resolved_profile = _resolve_entropy_text_profile(profile)
    if not raw_entropy:
        return "Empty entropy sample."
    if resolved_profile is ResonanceEntropyTextProfile.BARE_HEX_COMPACT:
        return raw_entropy.hex()
    return " ".join(f"{value:02x}" for value in raw_entropy)


def _config_variant(config: OpenDivinationConfig | None) -> str:
    if config is None:
        return "default"
    payload = config.model_dump(mode="json", exclude_defaults=True)
    if not payload:
        return "default"
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]
    return f"cfg_{digest}"


def _variant_id(
    asset_text_profile: ResonanceAssetTextProfile,
    config: OpenDivinationConfig | None,
) -> str:
    return cache_variant_id(
        "tarot_resonance_text",
        asset_text_profile.value,
        _config_variant(config),
    )


def _card_content(
    card: TarotCard,
    *,
    asset_text_profile: ResonanceAssetTextProfile,
    config: OpenDivinationConfig | None,
) -> EmbeddingContent:
    return EmbeddingContent(
        text=build_tarot_card_text(card, asset_text_profile, config=config),
        metadata={"title": card.name},
    )


def _content_cache_key(content: EmbeddingContent) -> str:
    return cache_key_for_content(
        text=content.text,
        image_bytes=None,
        image_mime_type=None,
        metadata=content.metadata,
    )


def _sample_shortlist(
    *,
    raw_entropy: bytes,
    corpus_size: int,
    shortlist_size: int,
) -> list[int]:
    shortlist_size = max(1, min(shortlist_size, corpus_size))
    available_indexes = list(range(corpus_size))
    chosen_indexes: list[int] = []
    offset = 0

    while len(chosen_indexes) < shortlist_size:
        pick, bytes_consumed = rejection_sample(
            raw_entropy[offset:],
            len(available_indexes),
        )
        offset += bytes_consumed
        chosen_indexes.append(available_indexes.pop(pick))

    return chosen_indexes


async def prepare_tarot_resonance_corpus(
    *,
    provider: EmbeddingProvider,
    asset_text_profile: ResonanceAssetTextProfile = ResonanceAssetTextProfile.AUTO,
    corpus: list[TarotCard] | None = None,
    cache: EmbeddingCache | None = None,
    config: OpenDivinationConfig | None = None,
) -> tuple[TarotResonanceCorpusPreparation, list[list[float]]]:
    cards = corpus or load_tarot_corpus()
    resolved_asset_text_profile = _resolve_asset_text_profile(asset_text_profile)
    contents = [
        _card_content(
            card,
            asset_text_profile=resolved_asset_text_profile,
            config=config,
        )
        for card in cards
    ]
    variant_id = _variant_id(resolved_asset_text_profile, config)
    cache_path = ""
    cache_hit = False

    if cache is not None:
        cache_path = str(
            cache.path_for(
                corpus_id="tarot",
                space_id=provider.info.space_id,
                variant_id=variant_id,
            )
        )
        cached_vectors = cache.load(
            corpus_id="tarot",
            space_id=provider.info.space_id,
            variant_id=variant_id,
        )
        if cached_vectors is not None:
            try:
                vectors = [cached_vectors[_content_cache_key(content)] for content in contents]
                cache_hit = True
            except KeyError:
                vectors = []
        else:
            vectors = []
    else:
        vectors = []

    if not vectors:
        vectors = await provider.embed(
            contents,
            task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT,
        )
        if cache is not None:
            cache.save(
                corpus_id="tarot",
                space_id=provider.info.space_id,
                variant_id=variant_id,
                vectors={
                    _content_cache_key(content): vector
                    for content, vector in zip(contents, vectors, strict=True)
                },
                metadata={
                    "asset_text_profile": resolved_asset_text_profile.value,
                    "config_variant": _config_variant(config),
                },
            )

    preparation = TarotResonanceCorpusPreparation(
        corpus="tarot",
        provider=provider.info.provider_id,
        model=provider.info.model,
        space_id=provider.info.space_id,
        asset_text_profile=resolved_asset_text_profile,
        prepared_cards=len(cards),
        cache_hit=cache_hit,
        cache_variant=variant_id,
        cache_path=cache_path,
    )
    return preparation, vectors


async def draw_tarot_resonance(
    *,
    provider: EmbeddingProvider,
    raw_entropy: bytes,
    source_info: SourceInfo,
    entropy_bytes: int | None = None,
    shortlist_size: int = DEFAULT_RESONANCE_SHORTLIST_SIZE,
    asset_text_profile: ResonanceAssetTextProfile = ResonanceAssetTextProfile.AUTO,
    entropy_text_profile: ResonanceEntropyTextProfile = ResonanceEntropyTextProfile.AUTO,
    corpus: list[TarotCard] | None = None,
    cache: EmbeddingCache | None = None,
    config: OpenDivinationConfig | None = None,
) -> TarotResonanceDraw:
    cards = corpus or load_tarot_corpus()
    resolved_asset_text_profile = _resolve_asset_text_profile(asset_text_profile)
    resolved_entropy_text_profile = _resolve_entropy_text_profile(entropy_text_profile)
    preparation, corpus_vectors = await prepare_tarot_resonance_corpus(
        provider=provider,
        asset_text_profile=resolved_asset_text_profile,
        corpus=cards,
        cache=cache,
        config=config,
    )

    query_text = build_entropy_text(raw_entropy, resolved_entropy_text_profile)
    query_vector = (
        await provider.embed(
            [EmbeddingContent(text=query_text)],
            task_type=EmbeddingTaskType.RETRIEVAL_QUERY,
        )
    )[0]
    shortlist_indexes = _sample_shortlist(
        raw_entropy=raw_entropy,
        corpus_size=len(cards),
        shortlist_size=shortlist_size,
    )

    ranked_matches = [
        (
            index,
            cards[index].name,
            cosine_similarity(query_vector, corpus_vectors[index]),
        )
        for index in shortlist_indexes
    ]
    ranked_matches.sort(key=lambda item: item[2], reverse=True)

    winner_index = ranked_matches[0][0]
    winner_score = ranked_matches[0][2]
    winner_card = cards[winner_index]
    configured_profiles = sorted(configured_tarot_text_profiles(config))
    ranked_matches_payload = [
        {"index": index, "name": name, "score": score}
        for index, name, score in ranked_matches
    ]

    provenance = create_provenance(
        source_info=source_info,
        raw_entropy=raw_entropy,
        mode="resonance",
        corpus="tarot",
        result_summary=winner_card.name,
        details={
            "provider_id": provider.info.provider_id,
            "provider_model": provider.info.model,
            "space_id": provider.info.space_id,
            "entropy_bytes": entropy_bytes or len(raw_entropy),
            "shortlist_size": shortlist_size,
            "shortlist_card_indexes": shortlist_indexes,
            "shortlist_cards": [cards[index].name for index in shortlist_indexes],
            "asset_text_profile": resolved_asset_text_profile.value,
            "entropy_text_profile": resolved_entropy_text_profile.value,
            "asset_text_profile_configured": (
                resolved_asset_text_profile.value in configured_profiles
            ),
            "asset_text_configured_profiles": configured_profiles,
            "corpus_cache_hit": preparation.cache_hit,
            "corpus_cache_variant": preparation.cache_variant,
            "ranked_matches": ranked_matches_payload,
        },
    )

    return TarotResonanceDraw(
        card=winner_card,
        score=winner_score,
        distance=1.0 - winner_score,
        provider=provider.info.provider_id,
        model=provider.info.model,
        space_id=provider.info.space_id,
        entropy_bytes=entropy_bytes or len(raw_entropy),
        asset_text_profile=resolved_asset_text_profile,
        entropy_text_profile=resolved_entropy_text_profile,
        shortlist_size=shortlist_size,
        provenance=provenance,
    )


__all__ = [
    "DEFAULT_ASSET_TEXT_PROFILE",
    "DEFAULT_ENTROPY_TEXT_PROFILE",
    "DEFAULT_RESONANCE_ENTROPY_BYTES",
    "DEFAULT_RESONANCE_SHORTLIST_SIZE",
    "build_entropy_text",
    "build_tarot_card_text",
    "draw_tarot_resonance",
    "prepare_tarot_resonance_corpus",
]
