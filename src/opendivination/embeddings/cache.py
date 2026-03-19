from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def default_cache_dir() -> Path:
    configured = os.getenv("OPENDIVINE_CACHE_DIR")
    if configured:
        return Path(configured).expanduser()

    xdg_cache = os.getenv("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache).expanduser() / "opendivination"
    return Path.home() / ".cache" / "opendivination"


def cache_key_for_content(
    *,
    text: str | None,
    image_bytes: bytes | None,
    image_mime_type: str | None,
    metadata: dict[str, str],
) -> str:
    digest = hashlib.sha256()
    digest.update((text or "").encode("utf-8"))
    digest.update(b"\0")
    digest.update((image_mime_type or "").encode("utf-8"))
    digest.update(b"\0")
    if image_bytes:
        digest.update(image_bytes)
    digest.update(b"\0")
    digest.update(json.dumps(metadata, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def cache_variant_id(*parts: str) -> str:
    normalized_parts = []
    for part in parts:
        slug = part.strip().lower().replace("/", "_").replace(":", "_")
        slug = slug.replace(" ", "_")
        normalized_parts.append(slug)
    return "__".join(normalized_parts)


class EmbeddingCache:
    """Simple filesystem cache keyed by corpus and embedding space."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = (root or default_cache_dir()) / "embeddings"

    def load(
        self,
        *,
        corpus_id: str,
        space_id: str,
        variant_id: str,
    ) -> dict[str, list[float]] | None:
        path = self.path_for(corpus_id=corpus_id, space_id=space_id, variant_id=variant_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("space_id") != space_id:
            return None
        if payload.get("variant_id") != variant_id:
            return None
        return {
            key: [float(value) for value in vector]
            for key, vector in payload.get("vectors", {}).items()
        }

    def save(
        self,
        *,
        corpus_id: str,
        space_id: str,
        variant_id: str,
        vectors: dict[str, list[float]],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        path = self.path_for(corpus_id=corpus_id, space_id=space_id, variant_id=variant_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 2,
            "corpus_id": corpus_id,
            "space_id": space_id,
            "variant_id": variant_id,
            "metadata": metadata or {},
            "vectors": vectors,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    def path_for(self, *, corpus_id: str, space_id: str, variant_id: str) -> Path:
        corpus_slug = corpus_id.replace("/", "_")
        space_slug = space_id.replace("/", "_").replace(":", "__")
        variant_slug = variant_id.replace("/", "_").replace(":", "__")
        return self._root / corpus_slug / variant_slug / f"{space_slug}.json"
