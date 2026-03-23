"""OpenDivination CLI entry point."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import sys
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, cast

import typer

if TYPE_CHECKING:
    from opendivination.config import OpenDivinationConfig
    from opendivination.embeddings import EmbeddingCache
    from opendivination.types import EmbeddingProvider, TarotDraw, TarotResonanceDraw

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


def _resolve_cli_source(source: str | None, config: OpenDivinationConfig) -> str:
    if source is not None:
        return source
    return config.sources.default or DEFAULT_ENTROPY_SOURCE


def _resolve_cli_embedding_provider(
    embedding_provider: str | None, config: OpenDivinationConfig
) -> str:
    if embedding_provider is not None:
        return embedding_provider
    return config.defaults.resonance.provider


def _resolve_cli_embedding_model(
    embedding_model: str | None, config: OpenDivinationConfig
) -> str | None:
    if embedding_model is not None:
        return embedding_model
    return config.defaults.resonance.model


def _prompt_choice(prompt: str, *, choices: tuple[str, ...], default: str) -> str:
    allowed = ", ".join(choices)
    while True:
        value = cast(str, typer.prompt(prompt, default=default)).strip()
        if value in choices:
            return value
        typer.echo(f"Choose one of: {allowed}", err=True)


def _discover_source_snapshot() -> list[dict[str, object]]:
    from opendivination.core.registry import SourceRegistry

    registry = SourceRegistry()
    detected = {source.name: source for source in asyncio.run(registry.auto_detect())}
    source_list = registry.list_sources(expand_openentropy=True)
    snapshot: list[dict[str, object]] = []
    for source in source_list:
        if source.name in detected:
            source.available = True
            source.quality_score = detected[source.name].quality_score
        snapshot.append(
            {
                "name": source.name,
                "type": source.source_type,
                "is_quantum": source.is_quantum,
                "available": source.available,
                "backend": source.backend,
            }
        )
    return snapshot


@app.command("setup")
def setup_cmd(
    config_path: str | None = typer.Option(
        None,
        "--config",
        help="Optional JSON config path. Defaults to ~/.config/opendivination/config.json",
    ),
    source_profile: str | None = typer.Option(
        None,
        "--source-profile",
        help="computer|remote_quantum|local_hardware",
    ),
    qrng_provider: str | None = typer.Option(
        None,
        "--qrng-provider",
        help="anu|outshift (used with --source-profile remote_quantum)",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        help="Optional API key for the selected remote QRNG provider",
    ),
    hardware_source: str | None = typer.Option(
        None,
        "--hardware-source",
        help="Preferred hardware source, for example qcicada or openentropy",
    ),
    output_json: bool = typer.Option(False, "--json/--no-json", help="Output as JSON"),
) -> None:
    """Guided onboarding for source selection and QRNG credentials."""
    from opendivination.config import default_config_path, load_config, save_config

    resolved_config_path = (
        Path(config_path).expanduser() if config_path is not None else default_config_path()
    )
    config = load_config(resolved_config_path, allow_missing=True)
    snapshot = _discover_source_snapshot()
    hardware_candidates = [
        cast(str, entry["name"])
        for entry in snapshot
        if entry["type"] == "hardware" and bool(entry["available"])
    ]
    interactive = (
        source_profile is None
        and qrng_provider is None
        and api_key is None
        and hardware_source is None
        and sys.stdin.isatty()
    )

    if interactive:
        typer.echo("OpenDivination setup")
        typer.echo("Choose the simplest source path that matches how you want to work.")
        source_profile = _prompt_choice(
            "Source profile",
            choices=("computer", "remote_quantum", "local_hardware"),
            default="computer",
        )

    resolved_profile = source_profile or "computer"
    warnings: list[str] = []
    chosen_source = DEFAULT_ENTROPY_SOURCE

    if resolved_profile == "computer":
        chosen_source = DEFAULT_ENTROPY_SOURCE
    elif resolved_profile == "remote_quantum":
        if interactive and qrng_provider is None:
            qrng_provider = _prompt_choice(
                "Remote QRNG provider",
                choices=("anu", "outshift"),
                default="anu",
            )
        resolved_provider = qrng_provider or "anu"
        if resolved_provider not in {"anu", "outshift"}:
            raise typer.BadParameter(
                "qrng provider must be 'anu' or 'outshift'",
                param_hint="--qrng-provider",
            )
        chosen_source = resolved_provider
        if interactive and api_key is None:
            prompt_text = (
                "Outshift API key"
                if resolved_provider == "outshift"
                else "ANU API key (optional, press enter to skip)"
            )
            entered_key = typer.prompt(prompt_text, default="", hide_input=True, show_default=False)
            api_key = entered_key or None
        if resolved_provider == "outshift" and not api_key:
            raise typer.BadParameter(
                "outshift requires an API key",
                param_hint="--api-key",
            )
        if resolved_provider == "anu":
            config.sources.anu.api_key = api_key or config.sources.anu.api_key
        else:
            config.sources.outshift.api_key = api_key or config.sources.outshift.api_key
    elif resolved_profile == "local_hardware":
        preferred_hardware_source = hardware_source
        if interactive and preferred_hardware_source is None:
            if hardware_candidates:
                default_hardware = (
                    "qcicada" if "qcicada" in hardware_candidates else hardware_candidates[0]
                )
                preferred_hardware_source = _prompt_choice(
                    "Hardware source",
                    choices=tuple(hardware_candidates),
                    default=default_hardware,
                )
            else:
                typer.echo("No local hardware source is currently detected. Keeping csprng.")
        if preferred_hardware_source is None:
            if "qcicada" in hardware_candidates:
                preferred_hardware_source = "qcicada"
            elif hardware_candidates:
                preferred_hardware_source = hardware_candidates[0]
        if preferred_hardware_source is None:
            chosen_source = DEFAULT_ENTROPY_SOURCE
            warnings.append(
                "No local hardware source was detected. Install openentropy on Python 3.13 and "
                "attach supported hardware such as QCicada before switching away from csprng."
            )
        else:
            chosen_source = preferred_hardware_source
            if preferred_hardware_source not in hardware_candidates:
                warnings.append(
                    f"Configured hardware source '{preferred_hardware_source}', but it is not "
                    "currently detected on this machine."
                )
    else:
        raise typer.BadParameter(
            "source profile must be 'computer', 'remote_quantum', or 'local_hardware'",
            param_hint="--source-profile",
        )

    config.sources.default = chosen_source
    written_path = save_config(config, resolved_config_path)
    refreshed_snapshot = _discover_source_snapshot()
    selected_available = any(
        entry["name"] == chosen_source and bool(entry["available"]) for entry in refreshed_snapshot
    )
    if not selected_available and not warnings:
        warnings.append(
            f"Configured source '{chosen_source}', but it is not currently "
            "available on this machine."
        )

    payload = {
        "config_path": str(written_path),
        "source_profile": resolved_profile,
        "default_source": chosen_source,
        "selected_source_available": selected_available,
        "available_hardware_sources": hardware_candidates,
        "saved_remote_keys": {
            "anu": config.sources.anu.api_key is not None,
            "outshift": config.sources.outshift.api_key is not None,
        },
        "resonance_defaults": {
            "provider": config.defaults.resonance.provider,
            "model": config.defaults.resonance.model,
        },
        "warnings": warnings,
    }

    if output_json:
        typer.echo(json.dumps(payload, indent=2))
        return

    typer.echo(f"Config written: {written_path}")
    typer.echo(f"Default source: {chosen_source}")
    typer.echo(f"Source available now: {'yes' if selected_available else 'no'}")
    if hardware_candidates:
        typer.echo("Detected hardware sources: " + ", ".join(hardware_candidates))
    if resolved_profile == "remote_quantum":
        typer.echo("Remote QRNG credentials are now stored in your OpenDivination config.")
    if warnings:
        for warning in warnings:
            typer.echo(f"Warning: {warning}")
    typer.echo("Next step: run `opendivination sources --json` to verify the active source list.")


@draw_app.command("tarot")
def draw_tarot_cmd(
    source: str | None = typer.Option(
        None,
        help=(
            "Entropy source name. Defaults to your configured source, or csprng if unset; "
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
    embedding_provider: str | None = typer.Option(
        None,
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

    config = _load_cli_config(config_path)
    resolved_source = _resolve_cli_source(source, config)
    resolved_embedding_provider = _resolve_cli_embedding_provider(embedding_provider, config)
    resolved_embedding_model = _resolve_cli_embedding_model(embedding_model, config)

    provider_instance: EmbeddingProvider | None = None
    if question is not None or mode == "resonance":
        provider_instance = create_embedding_provider(
            resolved_embedding_provider,
            model=resolved_embedding_model,
        )

    result: TarotDraw | TarotResonanceDraw
    if mode == "selection":
        result = draw_tarot_sync(
            source=resolved_source,
            question=question,
            provider=provider_instance,
            config=config if question else None,
        )
    elif mode == "resonance":
        if provider_instance is None:
            raise RuntimeError("resonance mode requires an embedding provider")
        cache = _build_embedding_cache(
            use_embedding_cache=use_embedding_cache,
            embedding_cache_dir=embedding_cache_dir,
        )
        result = draw_tarot_by_resonance_sync(
            provider=provider_instance,
            source=resolved_source,
            entropy_bytes=entropy_bytes,
            shortlist_size=shortlist_size,
            cache=cache,
            config=config,
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
    embedding_provider: str | None = typer.Option(
        None,
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

    config = _load_cli_config(config_path)
    provider = create_embedding_provider(
        _resolve_cli_embedding_provider(embedding_provider, config),
        model=_resolve_cli_embedding_model(embedding_model, config),
    )
    cache = _build_embedding_cache(
        use_embedding_cache=use_embedding_cache,
        embedding_cache_dir=embedding_cache_dir,
    )
    result = prepare_tarot_resonance_corpus_embeddings_sync(
        provider=provider,
        cache=cache,
        config=config,
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
    source: str | None = typer.Option(
        None,
        help=(
            "Entropy source name. Defaults to your configured source, or csprng if unset; "
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
    config_path: str | None = typer.Option(
        None,
        "--config",
        help="Optional JSON config path for source and resonance defaults",
    ),
    embedding_provider: str | None = typer.Option(
        None,
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

    config = _load_cli_config(config_path)
    resolved_source = _resolve_cli_source(source, config)
    resolved_embedding_provider = _resolve_cli_embedding_provider(embedding_provider, config)
    resolved_embedding_model = _resolve_cli_embedding_model(embedding_model, config)

    provider_instance = None
    if question is not None:
        from opendivination.embeddings.providers import create_embedding_provider

        provider_instance = create_embedding_provider(
            resolved_embedding_provider,
            model=resolved_embedding_model,
        )

    result = draw_iching_sync(
        method=ICMethod(method),
        source=resolved_source,
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
