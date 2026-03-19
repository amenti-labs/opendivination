from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from opendivination.types import EmbeddingTaskType


@dataclass(frozen=True)
class EmbeddingModelProfile:
    profile_id: str
    match_substrings: tuple[str, ...] = ()
    task_prefixes: Mapping[EmbeddingTaskType, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    task_templates: Mapping[EmbeddingTaskType, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def matches(self, model_name: str) -> bool:
        normalized = model_name.strip().lower()
        return any(token in normalized for token in self.match_substrings)

    def format_text(self, text: str, *, task_type: EmbeddingTaskType) -> str:
        template = self.task_templates.get(task_type)
        if template is not None:
            return template.format(text=text)
        return f"{self.task_prefixes.get(task_type, '')}{text}"


GENERIC_EMBEDDING_PROFILE = EmbeddingModelProfile(profile_id="generic")

NOMIC_EMBEDDING_PROFILE = EmbeddingModelProfile(
    profile_id="nomic",
    match_substrings=(
        "nomic-embed-text",
        "modernbert-embed",
    ),
    task_prefixes=MappingProxyType(
        {
            EmbeddingTaskType.RETRIEVAL_QUERY: "search_query: ",
            EmbeddingTaskType.RETRIEVAL_DOCUMENT: "search_document: ",
            EmbeddingTaskType.CLASSIFICATION: "classification: ",
            EmbeddingTaskType.CLUSTERING: "clustering: ",
        }
    ),
)

QWEN3_EMBEDDING_PROFILE = EmbeddingModelProfile(
    profile_id="qwen3",
    match_substrings=("qwen3-embedding",),
    task_templates=MappingProxyType(
        {
            EmbeddingTaskType.RETRIEVAL_QUERY: (
                "Instruct: Given a web search query, retrieve relevant passages "
                "that answer the query\nQuery: {text}"
            ),
        }
    ),
)

_EMBEDDING_MODEL_PROFILES = (
    NOMIC_EMBEDDING_PROFILE,
    QWEN3_EMBEDDING_PROFILE,
)


def resolve_embedding_model_profile(model_name: str) -> EmbeddingModelProfile:
    for profile in _EMBEDDING_MODEL_PROFILES:
        if profile.matches(model_name):
            return profile
    return GENERIC_EMBEDDING_PROFILE


def format_embedding_text(
    text: str,
    *,
    task_type: EmbeddingTaskType,
    model_name: str,
) -> str:
    profile = resolve_embedding_model_profile(model_name)
    return profile.format_text(text, task_type=task_type)
