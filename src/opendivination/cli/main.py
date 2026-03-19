"""OpenDivination CLI entry point."""

from __future__ import annotations

import asyncio
import dataclasses
import json
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, cast

import typer

if TYPE_CHECKING:
    from opendivination.config import OpenDivinationConfig
    from opendivination.embeddings import EmbeddingCache
    from opendivination.types import TarotDraw, TarotResonanceDraw

from opendivination.types import DEFAULT_ENTROPY_SOURCE

app = typer.Typer(name="opendivination", help="Quantum-entropy oracle SDK")
draw_app = typer.Typer(help="Draw from oracle corpora")
cache_app = typer.Typer(help="Prepare embedding caches for oracle corpora")
app.add_typer(draw_app, name="draw")
app.add_typer(cache_app, name="cache")


def _json_default(obj: object) -> object:
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _build_embedding_cache(
    *,
    use_embedding_cache: bool,
    embedding_cache_dir: str | None,
) -> EmbeddingCache | None:
    from opendivination.embeddings import EmbeddingCache

    if not use_embedding_cache:
        return None
    if embedding_cache_dir is not None:
        return EmbeddingCache(Path(embedding_cache_dir).expanduser())
    return EmbeddingCache()


def _load_cli_config(config_path: str | None) -> OpenDivinationConfig:
    from opendivination.config import load_config

    try:
        return load_config(config_path, allow_missing=config_path is None)
    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc), param_hint="--config") from exc


@draw_app.command("tarot")
def draw_tarot_cmd(
    source: str = typer.Option(
        DEFAULT_ENTROPY_SOURCE,
        help=(
            "Entropy source name. Defaults to csprng for stable local behavior; "
            "opt in to QRNG sources such as anu, openentropy:qcicada, or qcicada. "
            "Examples: csprng, anu, openentropy, "
            "openentropy:qcicada, qcicada, or qcicada?conditioning=raw&mode=raw."
        ),
    ),
    mode: str = typer.Option("selection", help="selection|resonance"),
    question: str | None = typer.Option(
        None,
        "--question",
        "-q",
        help="Question or intention for coherence scoring (requires --embed-provider)",
    ),
    config_path: str | None = typer.Option(
        None,
        "--config",
        help="Optional JSON config path for tarot card text overrides",
    ),
    embedding_provider: str = typer.Option(
        "local",
        "--embed-provider",
        help="deterministic|local|ollama|openai|openai_compatible|gemini|sentence_transformers",
    ),
    embedding_model: str | None = typer.Option(
        None,
        "--embed-model",
        help="Embedding model identifier for resonance mode",
    ),
    entropy_bytes: int = typer.Option(
        256,
        "--entropy-bytes",
        min=1,
        help="Number of entropy bytes to sample for resonance mode",
    ),
    shortlist_size: int = typer.Option(
        3,
        "--shortlist-size",
        min=1,
        help="Number of uniformly sampled candidate cards considered in resonance mode",
    ),
    use_embedding_cache: bool = typer.Option(
        True,
        "--embed-cache/--no-embed-cache",
        help="Cache tarot text embeddings on disk for resonance mode",
    ),
    embedding_cache_dir: str | None = typer.Option(
        None,
        "--embed-cache-dir",
        help="Optional cache directory for resonance embeddings",
    ),
    output_json: bool = typer.Option(False, "--json/--no-json", help="Output as JSON"),
) -> None:
    """Draw a tarot card."""
    from opendivination.embeddings.providers import create_embedding_provider
    from opendivination.oracles.tarot import draw_tarot_by_resonance_sync, draw_tarot_sync

    provider_instance = None
    if question is not None or mode == "resonance":
        provider_instance = create_embedding_provider(
            embedding_provider,
            model=embedding_model,
        )

    result: TarotDraw | TarotResonanceDraw
    if mode == "selection":
        result = draw_tarot_sync(
            source=source,
            question=question,
            provider=provider_instance,
            config=_load_cli_config(config_path) if question else None,
        )
    elif mode == "resonance":
        cache = _build_embedding_cache(
            use_embedding_cache=use_embedding_cache,
            embedding_cache_dir=embedding_cache_dir,
        )
        result = draw_tarot_by_resonance_sync(
            provider=provider_instance,
            source=source,
            entropy_bytes=entropy_bytes,
            shortlist_size=shortlist_size,
            cache=cache,
            config=_load_cli_config(config_path),
            question=question,
        )
    else:
        raise typer.BadParameter("mode must be 'selection' or 'resonance'")

    if output_json:
        typer.echo(json.dumps(dataclasses.asdict(result), indent=2, default=_json_default))
        return

    if mode == "selection":
        selection_result = cast("TarotDraw", result)
        lines = [
            f"Card: {selection_result.card.name} ({selection_result.orientation.value})",
            f"Source: {selection_result.provenance.source_id} "
            f"(quantum: {selection_result.provenance.is_quantum})",
        ]
        if selection_result.coherence is not None:
            lines.append(f"Coherence: {selection_result.coherence.score:.4f}")
        typer.echo("\n".join(lines))
        return

    resonance_result = cast("TarotResonanceDraw", result)
    lines = [
        f"Card: {resonance_result.card.name}",
        f"Score: {resonance_result.score:.6f}",
        f"Embedding: {resonance_result.provider}/{resonance_result.model}",
        f"Source: {resonance_result.provenance.source_id} "
        f"(quantum: {resonance_result.provenance.is_quantum})",
    ]
    if resonance_result.coherence is not None:
        lines.append(f"Coherence: {resonance_result.coherence.score:.4f}")
    typer.echo("\n".join(lines))


@cache_app.command("tarot")
def cache_tarot_cmd(
    config_path: str | None = typer.Option(
        None,
        "--config",
        help="Optional JSON config path for tarot card text overrides",
    ),
    embedding_provider: str = typer.Option(
        "local",
        "--embed-provider",
        help="deterministic|local|ollama|openai|openai_compatible|gemini|sentence_transformers",
    ),
    embedding_model: str | None = typer.Option(
        None,
        "--embed-model",
        help="Embedding model identifier for resonance cache preparation",
    ),
    use_embedding_cache: bool = typer.Option(
        True,
        "--embed-cache/--no-embed-cache",
        help="Write prepared tarot text embeddings to the cache",
    ),
    embedding_cache_dir: str | None = typer.Option(
        None,
        "--embed-cache-dir",
        help="Optional cache directory for resonance embeddings",
    ),
    output_json: bool = typer.Option(False, "--json/--no-json", help="Output as JSON"),
) -> None:
    """Prepare tarot text embeddings for resonance mode."""
    from opendivination.embeddings.providers import create_embedding_provider
    from opendivination.oracles.tarot import prepare_tarot_resonance_corpus_embeddings_sync

    provider = create_embedding_provider(
        embedding_provider,
        model=embedding_model,
    )
    cache = _build_embedding_cache(
        use_embedding_cache=use_embedding_cache,
        embedding_cache_dir=embedding_cache_dir,
    )
    result = prepare_tarot_resonance_corpus_embeddings_sync(
        provider=provider,
        cache=cache,
        config=_load_cli_config(config_path),
    )

    if output_json:
        typer.echo(json.dumps(dataclasses.asdict(result), indent=2, default=_json_default))
        return

    typer.echo(
        f"Corpus: {result.corpus}\n"
        f"Embedding: {result.provider}/{result.model}\n"
        f"Prepared cards: {result.prepared_cards}\n"
        f"Cache hit: {result.cache_hit}\n"
        f"Cache variant: {result.cache_variant}"
    )


@draw_app.command("iching")
def draw_iching_cmd(
    method: str = typer.Option("yarrow", help="yarrow|three_coin|uniform"),
    source: str = typer.Option(
        DEFAULT_ENTROPY_SOURCE,
        help=(
            "Entropy source name. Defaults to csprng for stable local behavior; "
            "opt in to QRNG sources such as anu, openentropy:qcicada, or qcicada. "
            "Examples: csprng, anu, openentropy, "
            "openentropy:qcicada, qcicada, or qcicada?conditioning=raw&mode=raw."
        ),
    ),
    question: str | None = typer.Option(
        None,
        "--question",
        "-q",
        help="Question or intention for coherence scoring (requires --embed-provider)",
    ),
    embedding_provider: str = typer.Option(
        "local",
        "--embed-provider",
        help="deterministic|local|ollama|openai|openai_compatible|gemini|sentence_transformers",
    ),
    embedding_model: str | None = typer.Option(
        None,
        "--embed-model",
        help="Embedding model identifier for coherence scoring",
    ),
    output_json: bool = typer.Option(False, "--json/--no-json", help="Output as JSON"),
) -> None:
    """Draw an I Ching hexagram."""
    from opendivination.oracles.iching import draw_iching_sync
    from opendivination.types import ICMethod

    provider_instance = None
    if question is not None:
        from opendivination.embeddings.providers import create_embedding_provider

        provider_instance = create_embedding_provider(
            embedding_provider,
            model=embedding_model,
        )

    result = draw_iching_sync(
        method=ICMethod(method),
        source=source,
        question=question,
        provider=provider_instance,
    )

    if output_json:
        typer.echo(json.dumps(dataclasses.asdict(result), indent=2, default=_json_default))
        return

    lines = [f"{result.primary.symbol}  Hexagram #{result.primary.number}: {result.primary.name}"]
    if result.changing_lines:
        lines.append(f"Changing lines: {result.changing_lines}")
        if result.secondary:
            lines.append(f"Secondary: #{result.secondary.number} {result.secondary.name}")
    else:
        lines.append("No changing lines")
    if result.coherence is not None:
        lines.append(f"Coherence: {result.coherence.score:.4f}")
    typer.echo("\n".join(lines))


@app.command("sources")
def sources_cmd(
    output_json: bool = typer.Option(False, "--json/--no-json", help="Output as JSON"),
    expand_openentropy: bool = typer.Option(
        False,
        "--expand-openentropy/--no-expand-openentropy",
        help="Expand named OpenEntropy selectors such as openentropy:qcicada",
    ),
) -> None:
    """List available entropy sources."""
    from opendivination.core.registry import SourceRegistry

    registry = SourceRegistry()
    detected = {source.name: source for source in asyncio.run(registry.auto_detect())}
    source_list = registry.list_sources(expand_openentropy=expand_openentropy)

    for source in source_list:
        if source.name in detected:
            source.available = True
            source.quality_score = detected[source.name].quality_score

    if output_json:
        typer.echo(
            json.dumps(
                [
                    {
                        "name": source.name,
                        "type": source.source_type,
                        "is_quantum": source.is_quantum,
                        "description": source.description,
                        "available": source.available,
                        "backend": source.backend,
                        "selector": source.selector,
                        "selection_mode": source.selection_mode,
                        "conditioning": source.conditioning,
                        "device_mode": source.device_mode,
                    }
                    for source in source_list
                ],
                indent=2,
            )
        )
        return

    typer.echo(f"{'Name':<28} {'Type':<12} {'Quantum':<10} {'Available':<10}")
    typer.echo("-" * 64)
    for source in source_list:
        quantum_str = "yes" if source.is_quantum else "no"
        available_str = "yes" if source.available else "no"
        typer.echo(
            f"{source.name:<28} {source.source_type:<12} {quantum_str:<10} {available_str:<10}"
        )


@app.command("version")
def version_cmd() -> None:
    """Show OpenDivination version."""
    from opendivination import __version__

    typer.echo(f"OpenDivination {__version__}")


if __name__ == "__main__":
    app()
