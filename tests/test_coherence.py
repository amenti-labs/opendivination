"""Tests for corpus-agnostic coherence scoring."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys

from opendivination.core.coherence import compute_coherence
from opendivination.embeddings.providers import DeterministicEmbeddingProvider
from opendivination.oracles.iching import draw_iching
from opendivination.oracles.iching_text import build_iching_hexagram_text
from opendivination.oracles.tarot import draw_tarot, draw_tarot_by_resonance

# -- core coherence function --------------------------------------------------


def test_compute_coherence_returns_score_and_hash() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)
    question = "What should I focus on today?"
    symbol_text = "Tarot card: The Fool. Keywords: beginnings, innocence."

    result = asyncio.run(
        compute_coherence(
            question=question,
            symbol_text=symbol_text,
            provider=provider,
        )
    )

    assert 0.0 <= result.score <= 1.0
    assert result.question_hash == hashlib.sha256(question.encode()).hexdigest()
    assert result.provider == "deterministic"
    assert result.model == "hash-v1"


def test_compute_coherence_score_is_clamped() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)

    result = asyncio.run(
        compute_coherence(
            question="test",
            symbol_text="test",
            provider=provider,
        )
    )

    assert 0.0 <= result.score <= 1.0


def test_compute_coherence_different_inputs_produce_different_hashes() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)

    r1 = asyncio.run(
        compute_coherence(
            question="What is my purpose?",
            symbol_text="The Star: hope, inspiration.",
            provider=provider,
        )
    )
    r2 = asyncio.run(
        compute_coherence(
            question="Should I change jobs?",
            symbol_text="The Star: hope, inspiration.",
            provider=provider,
        )
    )

    assert r1.question_hash != r2.question_hash


# -- I Ching text builder -----------------------------------------------------


def test_build_iching_hexagram_text(iching_corpus) -> None:
    hexagrams, _ = iching_corpus
    text = build_iching_hexagram_text(hexagrams[0])

    assert hexagrams[0].name in text
    assert hexagrams[0].pinyin in text
    assert hexagrams[0].character in text
    assert hexagrams[0].upper_trigram in text
    assert hexagrams[0].lower_trigram in text
    assert hexagrams[0].judgment in text
    assert text.startswith("I Ching hexagram #")


def test_build_iching_all_hexagrams_produce_text(iching_corpus) -> None:
    hexagrams, _ = iching_corpus
    for hexagram in hexagrams:
        text = build_iching_hexagram_text(hexagram)
        assert len(text) > 20
        assert hexagram.name in text


# -- tarot coherence via draw_tarot -------------------------------------------


def test_draw_tarot_without_question_has_no_coherence(csprng_registry) -> None:
    result = asyncio.run(draw_tarot(source="csprng", registry=csprng_registry))

    assert result.coherence is None


def test_draw_tarot_with_question_has_coherence(csprng_registry) -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)

    result = asyncio.run(
        draw_tarot(
            source="csprng",
            registry=csprng_registry,
            question="What does the future hold?",
            provider=provider,
        )
    )

    assert result.coherence is not None
    assert 0.0 <= result.coherence.score <= 1.0
    assert result.coherence.provider == "deterministic"
    assert len(result.coherence.question_hash) == 64  # SHA-256 hex


def test_draw_tarot_question_without_provider_has_no_coherence(csprng_registry) -> None:
    result = asyncio.run(
        draw_tarot(
            source="csprng",
            registry=csprng_registry,
            question="Will this work?",
            provider=None,
        )
    )

    assert result.coherence is None


# -- tarot resonance coherence -------------------------------------------------


def test_draw_tarot_resonance_with_question_has_coherence(csprng_registry) -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)

    result = asyncio.run(
        draw_tarot_by_resonance(
            provider=provider,
            source="csprng",
            registry=csprng_registry,
            question="What should I focus on?",
        )
    )

    assert result.coherence is not None
    assert 0.0 <= result.coherence.score <= 1.0
    # Resonance score (entropy-to-card) and coherence score (question-to-card)
    # should both be present and distinct concepts.
    assert result.score is not None  # resonance score
    assert result.coherence.score is not None  # coherence score


def test_draw_tarot_resonance_without_question_has_no_coherence(csprng_registry) -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)

    result = asyncio.run(
        draw_tarot_by_resonance(
            provider=provider,
            source="csprng",
            registry=csprng_registry,
        )
    )

    assert result.coherence is None


# -- I Ching coherence via draw_iching -----------------------------------------


def test_draw_iching_without_question_has_no_coherence(csprng_registry) -> None:
    result = asyncio.run(
        draw_iching(source="csprng", registry=csprng_registry)
    )

    assert result.coherence is None


def test_draw_iching_with_question_has_coherence(csprng_registry) -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)

    result = asyncio.run(
        draw_iching(
            source="csprng",
            registry=csprng_registry,
            question="How should I approach this conflict?",
            provider=provider,
        )
    )

    assert result.coherence is not None
    assert 0.0 <= result.coherence.score <= 1.0
    assert result.coherence.provider == "deterministic"


def test_draw_iching_question_without_provider_has_no_coherence(csprng_registry) -> None:
    result = asyncio.run(
        draw_iching(
            source="csprng",
            registry=csprng_registry,
            question="Will this work?",
            provider=None,
        )
    )

    assert result.coherence is None


# -- edge cases ----------------------------------------------------------------


def test_coherence_with_empty_question() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)
    result = asyncio.run(
        compute_coherence(
            question="",
            symbol_text="The Fool: beginnings, innocence.",
            provider=provider,
        )
    )
    assert 0.0 <= result.score <= 1.0


def test_coherence_with_unicode_question() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)
    result = asyncio.run(
        compute_coherence(
            question="我的未来会怎样？🔮",
            symbol_text="The Star: hope, inspiration.",
            provider=provider,
        )
    )
    assert 0.0 <= result.score <= 1.0
    assert len(result.question_hash) == 64


def test_coherence_consistency_deterministic() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=64)
    kwargs = {
        "question": "What awaits?",
        "symbol_text": "The Tower: destruction, upheaval.",
        "provider": provider,
    }
    r1 = asyncio.run(compute_coherence(**kwargs))
    r2 = asyncio.run(compute_coherence(**kwargs))
    assert r1.score == r2.score
    assert r1.question_hash == r2.question_hash


def test_question_without_provider_warns(csprng_registry) -> None:
    import warnings as _warnings

    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        asyncio.run(
            draw_tarot(
                source="csprng",
                registry=csprng_registry,
                question="Will this work?",
                provider=None,
            )
        )

    assert len(caught) == 1
    assert "question was provided without" in str(caught[0].message)


# -- hexagram symbol -----------------------------------------------------------


def test_hexagram_symbol_unicode_mapping(iching_corpus) -> None:
    hexagrams, _ = iching_corpus
    for hexagram in hexagrams:
        expected = chr(0x4DC0 + hexagram.number - 1)
        assert hexagram.symbol == expected


def test_hexagram_symbol_first_and_last(iching_corpus) -> None:
    hexagrams, _ = iching_corpus
    assert hexagrams[0].symbol == "䷀"  # #1 The Creative
    assert hexagrams[63].symbol == "䷿"  # #64 Before Completion


# -- cosine similarity ---------------------------------------------------------


def test_cosine_similarity_identical_vectors() -> None:
    from opendivination.embeddings.base import cosine_similarity

    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) > 0.999


def test_cosine_similarity_orthogonal_vectors() -> None:
    from opendivination.embeddings.base import cosine_similarity

    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert abs(cosine_similarity(a, b)) < 0.001


def test_cosine_similarity_dimension_mismatch() -> None:
    import pytest

    from opendivination.embeddings.base import EmbeddingError, cosine_similarity

    with pytest.raises(EmbeddingError):
        cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])


def test_normalize_vector_zero_vector() -> None:
    from opendivination.embeddings.base import normalize_vector

    result = normalize_vector([0.0, 0.0, 0.0])
    assert result == [0.0, 0.0, 0.0]


# -- coherence in JSON output --------------------------------------------------


def test_tarot_coherence_serializes_to_json(csprng_registry) -> None:
    import dataclasses

    provider = DeterministicEmbeddingProvider(dimensions=64)
    result = asyncio.run(
        draw_tarot(
            source="csprng",
            registry=csprng_registry,
            question="What awaits?",
            provider=provider,
        )
    )

    data = json.loads(json.dumps(dataclasses.asdict(result), default=str))
    assert "coherence" in data
    assert data["coherence"]["score"] >= 0.0
    assert "question_hash" in data["coherence"]
    assert data["coherence"]["provider"] == "deterministic"


def test_iching_coherence_serializes_to_json(csprng_registry) -> None:
    import dataclasses

    provider = DeterministicEmbeddingProvider(dimensions=64)
    result = asyncio.run(
        draw_iching(
            source="csprng",
            registry=csprng_registry,
            question="What awaits?",
            provider=provider,
        )
    )

    data = json.loads(json.dumps(dataclasses.asdict(result), default=str))
    assert "coherence" in data
    assert data["coherence"]["score"] >= 0.0
    assert "question_hash" in data["coherence"]


def test_no_coherence_serializes_as_none(csprng_registry) -> None:
    import dataclasses

    result = asyncio.run(draw_tarot(source="csprng", registry=csprng_registry))
    data = json.loads(json.dumps(dataclasses.asdict(result), default=str))
    assert data["coherence"] is None


# -- CLI integration -----------------------------------------------------------


def test_cli_tarot_with_question_json(csprng_registry) -> None:
    import subprocess

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "opendivination.cli.main",
            "draw",
            "tarot",
            "--question",
            "What should I focus on?",
            "--embed-provider",
            "deterministic",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert "coherence" in data
    assert data["coherence"] is not None
    assert data["coherence"]["score"] >= 0.0


def test_cli_tarot_without_question_json() -> None:
    import subprocess

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "opendivination.cli.main",
            "draw",
            "tarot",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["coherence"] is None


def test_cli_iching_with_question_json() -> None:
    import subprocess

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "opendivination.cli.main",
            "draw",
            "iching",
            "--question",
            "How should I proceed?",
            "--embed-provider",
            "deterministic",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert "coherence" in data
    assert data["coherence"] is not None
    assert data["coherence"]["score"] >= 0.0


def test_cli_iching_without_question_json() -> None:
    import subprocess

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "opendivination.cli.main",
            "draw",
            "iching",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["coherence"] is None
