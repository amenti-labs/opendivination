"""Corpus-agnostic coherence scoring.

Computes semantic similarity between a user's question and a drawn
symbol's text description using embedding cosine similarity.
"""

from __future__ import annotations

import hashlib

from opendivination.embeddings.base import cosine_similarity
from opendivination.types import (
    CoherenceResult,
    EmbeddingContent,
    EmbeddingProvider,
    EmbeddingTaskType,
)


async def compute_coherence(
    *,
    question: str,
    symbol_text: str,
    provider: EmbeddingProvider,
) -> CoherenceResult:
    """Compute coherence between a question and a symbol's text.

    Embeds the question as a retrieval query and the symbol text as a
    retrieval document, then returns the cosine similarity as a 0.0-1.0
    score.

    Args:
        question: The user's question or intention.
        symbol_text: The text description of the drawn symbol
            (card keywords, hexagram judgment, etc.).
        provider: An embedding provider instance.

    Returns:
        A CoherenceResult with the similarity score and metadata.
    """
    question_content = EmbeddingContent(text=question)
    symbol_content = EmbeddingContent(text=symbol_text)

    question_vector, symbol_vector = await _embed_pair(
        question_content, symbol_content, provider
    )

    score = cosine_similarity(question_vector, symbol_vector)
    # Clamp to [0, 1] — cosine similarity on normalized vectors is
    # already in [-1, 1] but negative coherence is meaningless here.
    score = max(0.0, min(1.0, score))

    question_hash = hashlib.sha256(question.encode()).hexdigest()

    return CoherenceResult(
        score=score,
        question_hash=question_hash,
        provider=provider.info.provider_id,
        model=provider.info.model,
    )


async def _embed_pair(
    question: EmbeddingContent,
    symbol: EmbeddingContent,
    provider: EmbeddingProvider,
) -> tuple[list[float], list[float]]:
    """Embed question and symbol text in a single batch call."""
    # Use RETRIEVAL_QUERY for the question and RETRIEVAL_DOCUMENT for
    # the symbol.  Providers that support task_type will place them in
    # the correct subspace; providers that ignore it still produce
    # comparable vectors.
    #
    # We issue two separate calls because task_type applies per-batch.
    question_vectors = await provider.embed(
        [question],
        task_type=EmbeddingTaskType.RETRIEVAL_QUERY,
    )
    symbol_vectors = await provider.embed(
        [symbol],
        task_type=EmbeddingTaskType.RETRIEVAL_DOCUMENT,
    )
    return question_vectors[0], symbol_vectors[0]


__all__ = ["compute_coherence"]
