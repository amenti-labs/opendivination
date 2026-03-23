from __future__ import annotations

import asyncio
import json
from pathlib import Path

from opendivination.config import OpenDivinationConfig
from opendivination.embeddings import EmbeddingCache
from opendivination.embeddings.base import EmbeddingError
from opendivination.embeddings.providers import (
    DeterministicEmbeddingProvider,
    create_embedding_provider,
)
from opendivination.oracles.resonance import (
    DEFAULT_RESONANCE_ENTROPY_BYTES,
    DEFAULT_RESONANCE_SHORTLIST_SIZE,
    build_entropy_text,
)
from opendivination.oracles.tarot import (
    draw_tarot_by_resonance,
    prepare_tarot_resonance_corpus_embeddings,
)
from opendivination.types import ResonanceEntropyTextProfile


def test_build_entropy_text_bare_hex_variants() -> None:
    raw_entropy = bytes([0x00, 0x01, 0xAB, 0xFF])

    assert build_entropy_text(raw_entropy) == "00 01 ab ff"
    assert (
        build_entropy_text(
            raw_entropy,
            ResonanceEntropyTextProfile.BARE_HEX_COMPACT,
        )
        == "0001abff"
    )


def test_draw_tarot_by_resonance_uses_stable_defaults(csprng_registry) -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)

    result = asyncio.run(
        draw_tarot_by_resonance(
            provider=provider,
            source="csprng",
            registry=csprng_registry,
        )
    )

    assert result.provider == "deterministic"
    assert result.entropy_bytes == DEFAULT_RESONANCE_ENTROPY_BYTES
    assert result.shortlist_size == DEFAULT_RESONANCE_SHORTLIST_SIZE
    assert result.asset_text_profile.value == "descriptive"
    assert result.entropy_text_profile.value == "bare_hex_spaced"
    assert result.provenance.mode == "resonance"
    assert result.provenance.source_id == "csprng"
    assert result.provenance.is_quantum is False
    assert result.provenance.details is not None
    assert len(result.provenance.details["shortlist_cards"]) == DEFAULT_RESONANCE_SHORTLIST_SIZE
    assert result.provenance.details["asset_text_profile"] == "descriptive"
    assert result.provenance.details["entropy_text_profile"] == "bare_hex_spaced"
    assert result.provenance.details["ranked_matches"][0]["name"] == result.card.name


def test_card_text_can_be_overridden_by_json_config(csprng_registry) -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)
    config = OpenDivinationConfig.model_validate(
        {
            "tarot": {
                "card_text": {
                    "profiles": {
                        "descriptive": {
                            "template": (
                                "Configured {name}. Arcana {arcana}. "
                                "Suit {suit}. Keywords {keywords}."
                            )
                        }
                    }
                }
            }
        }
    )

    result = asyncio.run(
        draw_tarot_by_resonance(
            provider=provider,
            source="csprng",
            registry=csprng_registry,
            config=config,
        )
    )

    assert result.provenance.details is not None
    assert result.provenance.details["asset_text_profile_configured"] is True
    assert result.provenance.details["asset_text_configured_profiles"] == ["descriptive"]


def test_prepare_tarot_resonance_corpus_uses_cache(tmp_path) -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)
    cache = EmbeddingCache(tmp_path)

    first = asyncio.run(
        prepare_tarot_resonance_corpus_embeddings(
            provider=provider,
            cache=cache,
        )
    )
    second = asyncio.run(
        prepare_tarot_resonance_corpus_embeddings(
            provider=provider,
            cache=cache,
        )
    )

    assert first.prepared_cards == 78
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert first.cache_variant == second.cache_variant
    assert first.cache_path == second.cache_path
    payload = json.loads(Path(first.cache_path).read_text(encoding="utf-8"))
    assert payload["variant_id"] == first.cache_variant


def test_local_provider_error_is_actionable_when_no_runtime(monkeypatch) -> None:
    monkeypatch.setattr(
        "opendivination.embeddings.providers._probe_ollama",
        lambda timeout=1.0: False,
    )

    try:
        create_embedding_provider("local")
    except EmbeddingError as exc:
        message = str(exc)
        assert "No local embedding runtime available" in message
        assert "Ollama" in message
        assert "sentence-transformers" in message
    else:
        raise AssertionError("Expected local provider creation to fail without a local runtime")
