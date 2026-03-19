from __future__ import annotations

import asyncio
import base64
import hashlib
import inspect
import json
import os
from dataclasses import replace
from typing import Any

import httpx

from opendivination.embeddings.base import EmbeddingError, normalize_vector
from opendivination.embeddings.profiles import format_embedding_text
from opendivination.types import (
    EmbeddingCapabilities,
    EmbeddingContent,
    EmbeddingModality,
    EmbeddingMultimodalSurface,
    EmbeddingProvider,
    EmbeddingProviderInfo,
    EmbeddingTaskType,
)


def _space_id(provider_id: str, model: str, dimensions: int) -> str:
    return f"{provider_id}:{model}:{dimensions}"


def _task_type_to_google(task_type: EmbeddingTaskType) -> str:
    mapping = {
        EmbeddingTaskType.SIMILARITY: "SEMANTIC_SIMILARITY",
        EmbeddingTaskType.RETRIEVAL_QUERY: "RETRIEVAL_QUERY",
        EmbeddingTaskType.RETRIEVAL_DOCUMENT: "RETRIEVAL_DOCUMENT",
        EmbeddingTaskType.CODE_RETRIEVAL_QUERY: "CODE_RETRIEVAL_QUERY",
        EmbeddingTaskType.QUESTION_ANSWERING: "QUESTION_ANSWERING",
        EmbeddingTaskType.FACT_VERIFICATION: "FACT_VERIFICATION",
        EmbeddingTaskType.CLASSIFICATION: "CLASSIFICATION",
        EmbeddingTaskType.CLUSTERING: "CLUSTERING",
    }
    return mapping[task_type]


def _ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def _openai_compatible_base_url() -> str:
    return (
        os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or "https://api.openai.com/v1"
    ).rstrip("/")


def _probe_ollama(*, timeout: float = 1.0) -> bool:
    try:
        response = httpx.get(f"{_ollama_base_url()}/api/tags", timeout=timeout)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


def _ensure_modality_supported(
    capabilities: EmbeddingCapabilities,
    content: EmbeddingContent,
    *,
    provider_id: str,
) -> None:
    if content.modality is EmbeddingModality.TEXT and not capabilities.supports_text:
        raise EmbeddingError(f"{provider_id} does not support text embeddings")
    if content.modality is EmbeddingModality.IMAGE and not capabilities.supports_image:
        raise EmbeddingError(f"{provider_id} does not support image-only embeddings")
    if content.modality is EmbeddingModality.MULTIMODAL and not capabilities.supports_multimodal:
        raise EmbeddingError(f"{provider_id} does not support multimodal embeddings")


class DeterministicEmbeddingProvider:
    """Dependency-free local provider for tests, offline use, and architecture plumbing."""

    def __init__(self, dimensions: int = 256) -> None:
        if dimensions < 8:
            raise ValueError("dimensions must be >= 8")
        self.info = EmbeddingProviderInfo(
            provider_id="deterministic",
            model="hash-v1",
            dimensions=dimensions,
            space_id=_space_id("deterministic", "hash-v1", dimensions),
            normalized=True,
            vendor="OpenDivination",
            multimodal_surface=EmbeddingMultimodalSurface.SHARED_VECTOR,
            capabilities=EmbeddingCapabilities(
                supports_text=True,
                supports_image=True,
                supports_multimodal=True,
                supports_task_type=True,
                supports_output_dimensions=False,
            ),
        )

    async def embed(
        self,
        contents: list[EmbeddingContent],
        *,
        task_type: EmbeddingTaskType = EmbeddingTaskType.SIMILARITY,
        output_dimensions: int | None = None,
    ) -> list[list[float]]:
        if output_dimensions is not None:
            raise EmbeddingError("deterministic provider does not support output_dimensions")

        return [self._embed_content(content, task_type=task_type) for content in contents]

    def _embed_content(
        self, content: EmbeddingContent, *, task_type: EmbeddingTaskType
    ) -> list[float]:
        _ensure_modality_supported(
            self.info.capabilities,
            content,
            provider_id=self.info.provider_id,
        )
        vector = [0.0 for _ in range(self.info.dimensions)]

        if content.text:
            prefixed = f"{task_type.value}:{content.text}".encode()
            self._accumulate(vector, prefixed, salt=b"text")

        if content.image:
            self._accumulate(
                vector,
                content.image.data,
                salt=content.image.mime_type.encode(),
            )

        if content.metadata:
            metadata_blob = json.dumps(content.metadata, sort_keys=True).encode("utf-8")
            self._accumulate(vector, metadata_blob, salt=b"metadata")

        return normalize_vector(vector)

    def _accumulate(self, vector: list[float], payload: bytes, *, salt: bytes) -> None:
        if not payload:
            return

        step = 16 if len(payload) > 512 else 8
        for index in range(0, len(payload), step):
            chunk = payload[index : index + step]
            digest = hashlib.blake2b(salt + chunk, digest_size=16).digest()
            bucket = int.from_bytes(digest[:8], "big") % len(vector)
            sign = 1.0 if digest[8] & 1 else -1.0
            magnitude = 1.0 + (digest[9] / 255.0)
            vector[bucket] += sign * magnitude


class OpenAIEmbeddingProvider:
    """Hosted OpenAI text embeddings via the REST API."""

    _DEFAULT_DIMS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "text-embedding-3-large",
        base_url: str = "https://api.openai.com/v1",
        dimensions: int | None = None,
        timeout: float = 30.0,
        require_api_key: bool = True,
    ) -> None:
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if require_api_key and not self._api_key:
            raise EmbeddingError("OPENAI_API_KEY must be set for OpenAIEmbeddingProvider")
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        resolved_dimensions = dimensions or self._DEFAULT_DIMS.get(model, 1536)
        self.info = EmbeddingProviderInfo(
            provider_id="openai",
            model=model,
            dimensions=resolved_dimensions,
            space_id=_space_id("openai", model, resolved_dimensions),
            normalized=True,
            vendor="OpenAI",
            multimodal_surface=EmbeddingMultimodalSurface.TEXT_ONLY,
            capabilities=EmbeddingCapabilities(
                supports_text=True,
                supports_image=False,
                supports_multimodal=False,
                supports_task_type=False,
                supports_output_dimensions=True,
            ),
        )

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def embed(
        self,
        contents: list[EmbeddingContent],
        *,
        task_type: EmbeddingTaskType = EmbeddingTaskType.SIMILARITY,
        output_dimensions: int | None = None,
    ) -> list[list[float]]:
        texts: list[str] = []
        for content in contents:
            _ensure_modality_supported(
                self.info.capabilities,
                content,
                provider_id=self.info.provider_id,
            )
            if not content.text:
                raise EmbeddingError("OpenAI embeddings require text content")
            texts.append(
                format_embedding_text(
                    content.text,
                    task_type=task_type,
                    model_name=self.info.model,
                )
            )

        body: dict[str, Any] = {"model": self.info.model, "input": texts}
        requested_dimensions = output_dimensions
        if requested_dimensions is not None:
            body["dimensions"] = requested_dimensions

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                headers=self._build_headers(),
                json=body,
            )
        response.raise_for_status()
        payload = response.json()
        vectors = [item["embedding"] for item in payload["data"]]

        dimensions = len(vectors[0]) if vectors else self.info.dimensions
        self.info = replace(
            self.info,
            dimensions=dimensions,
            space_id=_space_id(self.info.provider_id, self.info.model, dimensions),
        )
        return [normalize_vector([float(value) for value in vector]) for vector in vectors]


class OpenAICompatibleEmbeddingProvider(OpenAIEmbeddingProvider):
    """Generic OpenAI-style embeddings transport for compatible hosted gateways."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "text-embedding-3-large",
        base_url: str | None = None,
        dimensions: int | None = None,
        timeout: float = 30.0,
    ) -> None:
        compatible_api_key = (
            api_key
            or os.getenv("OPENAI_COMPATIBLE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        super().__init__(
            api_key=compatible_api_key,
            model=model,
            base_url=base_url or _openai_compatible_base_url(),
            dimensions=dimensions,
            timeout=timeout,
            require_api_key=False,
        )
        self.info = replace(
            self.info,
            provider_id="openai_compatible",
            space_id=_space_id("openai_compatible", model, self.info.dimensions),
            vendor="OpenAI-compatible",
        )


class OllamaEmbeddingProvider:
    """Local text embeddings via the Ollama HTTP API."""

    _DEFAULT_DIMS = {
        "nomic-embed-text": 768,
        "nomic-embed-text:latest": 768,
        "qwen3-embedding:0.6b": 1024,
    }

    def __init__(
        self,
        *,
        model: str = "nomic-embed-text",
        base_url: str | None = None,
        dimensions: int | None = None,
        timeout: float = 30.0,
    ) -> None:
        resolved_dimensions = dimensions or self._DEFAULT_DIMS.get(model, 768)
        self._base_url = (base_url or _ollama_base_url()).rstrip("/")
        self._timeout = timeout
        self.info = EmbeddingProviderInfo(
            provider_id="ollama",
            model=model,
            dimensions=resolved_dimensions,
            space_id=_space_id("ollama", model, resolved_dimensions),
            normalized=True,
            vendor="Ollama",
            multimodal_surface=EmbeddingMultimodalSurface.TEXT_ONLY,
            capabilities=EmbeddingCapabilities(
                supports_text=True,
                supports_image=False,
                supports_multimodal=False,
                supports_task_type=True,
                supports_output_dimensions=False,
            ),
        )

    async def embed(
        self,
        contents: list[EmbeddingContent],
        *,
        task_type: EmbeddingTaskType = EmbeddingTaskType.SIMILARITY,
        output_dimensions: int | None = None,
    ) -> list[list[float]]:
        if output_dimensions is not None:
            raise EmbeddingError("Ollama embeddings do not support output_dimensions")

        texts: list[str] = []
        for content in contents:
            _ensure_modality_supported(
                self.info.capabilities,
                content,
                provider_id=self.info.provider_id,
            )
            if not content.text:
                raise EmbeddingError("Ollama embeddings require text content")
            texts.append(
                format_embedding_text(
                    content.text,
                    task_type=task_type,
                    model_name=self.info.model,
                )
            )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/embed",
                    json={"model": self.info.model, "input": texts},
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmbeddingError(
                f"OllamaEmbeddingProvider request failed for model '{self.info.model}'"
            ) from exc

        payload = response.json()
        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise EmbeddingError("Ollama did not return the expected embeddings payload")

        vectors = [
            [float(value) for value in vector]
            for vector in embeddings
        ]
        dimensions = len(vectors[0]) if vectors else self.info.dimensions
        self.info = replace(
            self.info,
            dimensions=dimensions,
            space_id=_space_id(self.info.provider_id, self.info.model, dimensions),
        )
        return [normalize_vector(vector) for vector in vectors]


class GeminiEmbeddingProvider:
    """Hosted Google Gemini embeddings via the Gemini API.

    `gemini-embedding-001` is text-only. `gemini-embedding-2-preview`
    supports multimodal inputs in a unified space.
    """

    _MULTIMODAL_MODELS = ("gemini-embedding-2",)
    _SUPPORTED_IMAGE_MIME_TYPES = {"image/png", "image/jpeg"}
    _MAX_INDIVIDUAL_REQUEST_CONCURRENCY = 8
    _MAX_REQUEST_RETRIES = 3
    _RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "gemini-embedding-001",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        dimensions: int = 3072,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self._api_key:
            raise EmbeddingError(
                "GOOGLE_API_KEY or GEMINI_API_KEY must be set for GeminiEmbeddingProvider"
            )
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        supports_multimodal = model.startswith(self._MULTIMODAL_MODELS)
        self.info = EmbeddingProviderInfo(
            provider_id="gemini",
            model=model,
            dimensions=dimensions,
            space_id=_space_id("gemini", model, dimensions),
            normalized=True,
            vendor="Google",
            multimodal_surface=(
                EmbeddingMultimodalSurface.SHARED_VECTOR
                if supports_multimodal
                else EmbeddingMultimodalSurface.TEXT_ONLY
            ),
            capabilities=EmbeddingCapabilities(
                supports_text=True,
                supports_image=supports_multimodal,
                supports_multimodal=supports_multimodal,
                supports_task_type=True,
                supports_output_dimensions=True,
            ),
        )

    async def embed(
        self,
        contents: list[EmbeddingContent],
        *,
        task_type: EmbeddingTaskType = EmbeddingTaskType.SIMILARITY,
        output_dimensions: int | None = None,
    ) -> list[list[float]]:
        for content in contents:
            _ensure_modality_supported(
                self.info.capabilities,
                content,
                provider_id=self.info.provider_id,
            )

        if contents and all(content.modality is EmbeddingModality.TEXT for content in contents):
            try:
                vectors = await self._batch_embed_text_only(
                    contents,
                    task_type=task_type,
                    output_dimensions=output_dimensions,
                )
            except httpx.HTTPStatusError as exc:
                # Some Gemini models reject batchEmbedContents and only support embedContent.
                if exc.response.status_code not in {400, 404, 405}:
                    raise
                vectors = await self._embed_individually(
                    contents,
                    task_type=task_type,
                    output_dimensions=output_dimensions,
                )
        else:
            vectors = await self._embed_individually(
                contents,
                task_type=task_type,
                output_dimensions=output_dimensions,
            )

        dimensions = len(vectors[0]) if vectors else self.info.dimensions
        self.info = replace(
            self.info,
            dimensions=dimensions,
            space_id=_space_id(self.info.provider_id, self.info.model, dimensions),
        )
        return [normalize_vector(vector) for vector in vectors]

    async def _batch_embed_text_only(
        self,
        contents: list[EmbeddingContent],
        *,
        task_type: EmbeddingTaskType,
        output_dimensions: int | None,
    ) -> list[list[float]]:
        requests = [
            self._build_request(
                content,
                task_type=task_type,
                output_dimensions=output_dimensions,
                include_model=True,
            )
            for content in contents
        ]
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await self._post_with_retries(
                client,
                f"{self._base_url}/models/{self.info.model}:batchEmbedContents",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self._api_key,
                },
                json={"requests": requests},
            )
        response.raise_for_status()
        payload = response.json()
        embeddings_payload = payload.get("embeddings", [])
        if len(embeddings_payload) != len(contents):
            raise EmbeddingError(
                "Gemini batchEmbedContents returned an unexpected number "
                "of embeddings"
            )
        return [self._extract_embedding_values(item) for item in embeddings_payload]

    async def _embed_individually(
        self,
        contents: list[EmbeddingContent],
        *,
        task_type: EmbeddingTaskType,
        output_dimensions: int | None,
    ) -> list[list[float]]:
        semaphore = asyncio.Semaphore(self._MAX_INDIVIDUAL_REQUEST_CONCURRENCY)

        async def embed_one(index: int, content: EmbeddingContent) -> tuple[int, list[float]]:
            async with semaphore:
                response = await self._post_with_retries(
                    client,
                    f"{self._base_url}/models/{self.info.model}:embedContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self._api_key,
                    },
                    json=self._build_request(
                        content,
                        task_type=task_type,
                        output_dimensions=output_dimensions,
                        include_model=False,
                    ),
                )
            response.raise_for_status()
            payload = response.json()
            embedding_payload = payload.get("embedding")
            if embedding_payload is None:
                embeddings_payload = payload.get("embeddings", [])
                if embeddings_payload:
                    embedding_payload = embeddings_payload[0]
            if embedding_payload is None:
                raise EmbeddingError("Gemini did not return an embedding payload")
            return index, self._extract_embedding_values(embedding_payload)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            results = await asyncio.gather(
                *(embed_one(index, content) for index, content in enumerate(contents))
            )
        ordered = sorted(results, key=lambda item: item[0])
        return [vector for _, vector in ordered]

    async def _post_with_retries(
        self,
        client: httpx.AsyncClient,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
    ) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(1, self._MAX_REQUEST_RETRIES + 1):
            try:
                response = await client.post(url, headers=headers, json=json)
                status_code = getattr(response, "status_code", 200)
                if status_code in self._RETRYABLE_STATUS_CODES:
                    response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code not in self._RETRYABLE_STATUS_CODES:
                    raise
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
                last_error = exc

            if attempt >= self._MAX_REQUEST_RETRIES:
                break
            await asyncio.sleep(0.4 * attempt)

        if last_error is not None:
            raise last_error
        raise EmbeddingError("Gemini request failed without an explicit exception")

    def _build_request(
        self,
        content: EmbeddingContent,
        *,
        task_type: EmbeddingTaskType,
        output_dimensions: int | None,
        include_model: bool,
    ) -> dict[str, Any]:
        parts: list[dict[str, Any]] = []
        if content.text:
            parts.append({"text": content.text})
        if content.image:
            if content.image.mime_type not in self._SUPPORTED_IMAGE_MIME_TYPES:
                raise EmbeddingError(
                    "Gemini multimodal embeddings currently support PNG and JPEG images"
                )
            parts.append(
                {
                    "inline_data": {
                        "mime_type": content.image.mime_type,
                        "data": base64.b64encode(content.image.data).decode("ascii"),
                    }
                }
            )
        if not parts:
            raise EmbeddingError("Gemini embeddings require text or image content")

        request: dict[str, Any] = {
            "content": {"parts": parts},
            "taskType": _task_type_to_google(task_type),
        }
        if include_model:
            request["model"] = f"models/{self.info.model}"
        if output_dimensions is not None:
            request["outputDimensionality"] = output_dimensions
        title = content.metadata.get("title")
        if task_type is EmbeddingTaskType.RETRIEVAL_DOCUMENT and title:
            request["title"] = title
        return request

    def _extract_embedding_values(self, payload: dict[str, Any]) -> list[float]:
        values = payload.get("values")
        if values is None:
            raise EmbeddingError("Gemini embedding payload did not include values")
        return [float(value) for value in values]


class SentenceTransformersEmbeddingProvider:
    """Optional local text embedding provider powered by sentence-transformers."""

    def __init__(
        self,
        *,
        model: str = "nomic-ai/nomic-embed-text-v1.5",
        normalize: bool = True,
    ) -> None:
        try:
            from sentence_transformers import (  # type: ignore[import-not-found]
                SentenceTransformer,
            )
        except ImportError as exc:
            raise EmbeddingError(
                "sentence-transformers is required for SentenceTransformersEmbeddingProvider"
            ) from exc

        self._normalize = normalize
        sentence_transformer_cls: Any = SentenceTransformer
        self._model = sentence_transformer_cls(model, trust_remote_code=True)
        dimensions = int(self._model.get_sentence_embedding_dimension())
        self.info = EmbeddingProviderInfo(
            provider_id="sentence_transformers",
            model=model,
            dimensions=dimensions,
            space_id=_space_id("sentence_transformers", model, dimensions),
            normalized=normalize,
            vendor="SentenceTransformers",
            multimodal_surface=EmbeddingMultimodalSurface.TEXT_ONLY,
            capabilities=EmbeddingCapabilities(
                supports_text=True,
                supports_image=False,
                supports_multimodal=False,
                supports_task_type=True,
                supports_output_dimensions=False,
            ),
        )

    async def embed(
        self,
        contents: list[EmbeddingContent],
        *,
        task_type: EmbeddingTaskType = EmbeddingTaskType.SIMILARITY,
        output_dimensions: int | None = None,
    ) -> list[list[float]]:
        if output_dimensions is not None:
            raise EmbeddingError(
                "SentenceTransformersEmbeddingProvider does not support output_dimensions"
            )

        raw_inputs: list[str] = []
        fallback_inputs: list[str] = []
        for content in contents:
            _ensure_modality_supported(
                self.info.capabilities,
                content,
                provider_id=self.info.provider_id,
            )
            if not content.text:
                raise EmbeddingError("SentenceTransformers embeddings require text content")
            raw_inputs.append(content.text)
            fallback_inputs.append(
                format_embedding_text(
                    content.text,
                    task_type=task_type,
                    model_name=self.info.model,
                )
            )

        vectors = self._encode_with_retrieval_method(raw_inputs, task_type)
        if vectors is None:
            vectors = self._model.encode(
                fallback_inputs,
                normalize_embeddings=self._normalize,
                convert_to_numpy=False,
            )

        return [
            [float(value) for value in (vector.tolist() if hasattr(vector, "tolist") else vector)]
            for vector in vectors
        ]

    def _encode_with_retrieval_method(
        self,
        inputs: list[str],
        task_type: EmbeddingTaskType,
    ) -> Any | None:
        method_name: str | None = None
        if task_type is EmbeddingTaskType.RETRIEVAL_QUERY:
            method_name = "encode_query"
        elif task_type is EmbeddingTaskType.RETRIEVAL_DOCUMENT:
            method_name = "encode_document"
        if method_name is None:
            return None

        method = getattr(self._model, method_name, None)
        if not callable(method):
            return None

        kwargs: dict[str, Any] = {"convert_to_numpy": False}
        try:
            signature = inspect.signature(method)
        except (TypeError, ValueError):
            signature = None
        if signature is not None and "normalize_embeddings" in signature.parameters:
            kwargs["normalize_embeddings"] = self._normalize
        return method(inputs, **kwargs)


def create_embedding_provider(
    provider: str,
    *,
    model: str | None = None,
    dimensions: int | None = None,
    api_key: str | None = None,
    project: str | None = None,
    location: str = "global",
    access_token: str | None = None,
) -> EmbeddingProvider:
    normalized = provider.strip().lower()
    if normalized == "deterministic":
        return DeterministicEmbeddingProvider(dimensions=dimensions or 256)
    if normalized in {"local"}:
        if model and "/" in model:
            return SentenceTransformersEmbeddingProvider(model=model)
        if _probe_ollama():
            return OllamaEmbeddingProvider(
                model=model or "nomic-embed-text",
                dimensions=dimensions,
            )
        return SentenceTransformersEmbeddingProvider(
            model=model or "sentence-transformers/all-MiniLM-L6-v2"
        )
    if normalized in {"ollama"}:
        return OllamaEmbeddingProvider(
            model=model or "nomic-embed-text",
            dimensions=dimensions,
        )
    if normalized == "openai":
        return OpenAIEmbeddingProvider(
            api_key=api_key,
            model=model or "text-embedding-3-large",
            dimensions=dimensions,
        )
    if normalized in {"openai_compatible", "openai-compatible", "openai_compat"}:
        return OpenAICompatibleEmbeddingProvider(
            api_key=api_key,
            model=model or "text-embedding-3-large",
            dimensions=dimensions,
        )
    if normalized in {"gemini", "google"}:
        return GeminiEmbeddingProvider(
            api_key=api_key,
            model=model or "gemini-embedding-001",
            dimensions=dimensions or 3072,
        )
    if normalized in {"sentence_transformers", "sentence-transformers", "st"}:
        return SentenceTransformersEmbeddingProvider(
            model=model or "nomic-ai/nomic-embed-text-v1.5"
        )
    raise EmbeddingError(f"Unknown embedding provider: {provider}")
