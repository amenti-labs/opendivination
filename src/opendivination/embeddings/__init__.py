"""Embedding providers and utilities for resonance-style oracle modes."""

from opendivination.embeddings.base import EmbeddingError, cosine_similarity, normalize_vector
from opendivination.embeddings.cache import EmbeddingCache, cache_key_for_content, cache_variant_id
from opendivination.embeddings.profiles import (
    EmbeddingModelProfile,
    format_embedding_text,
    resolve_embedding_model_profile,
)
from opendivination.embeddings.providers import (
    DeterministicEmbeddingProvider,
    GeminiEmbeddingProvider,
    OllamaEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
    OpenAIEmbeddingProvider,
    SentenceTransformersEmbeddingProvider,
    create_embedding_provider,
)

__all__ = [
    "DeterministicEmbeddingProvider",
    "EmbeddingCache",
    "EmbeddingError",
    "EmbeddingModelProfile",
    "GeminiEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "OpenAICompatibleEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "SentenceTransformersEmbeddingProvider",
    "cache_key_for_content",
    "cache_variant_id",
    "cosine_similarity",
    "create_embedding_provider",
    "format_embedding_text",
    "normalize_vector",
    "resolve_embedding_model_profile",
]
