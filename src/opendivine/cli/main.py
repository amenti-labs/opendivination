"""OpenDivine CLI entry point."""

import dataclasses
import json
from enum import Enum

import typer

app = typer.Typer(name="opendivine", help="Quantum-entropy oracle SDK")
draw_app = typer.Typer(help="Draw from oracle corpora")
app.add_typer(draw_app, name="draw")


def _json_default(obj: object) -> object:
    """JSON serializer for Enum values in dataclass trees."""
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


@draw_app.command("tarot")
def draw_tarot_cmd(
    source: str | None = typer.Option(None, help="Entropy source name"),
    output_json: bool = typer.Option(False, "--json/--no-json", help="Output as JSON"),
) -> None:
    """Draw a tarot card."""
    from opendivine.oracles.tarot import draw_tarot_sync

    result = draw_tarot_sync(source=source)

    if output_json:
        data = dataclasses.asdict(result)
        typer.echo(json.dumps(data, indent=2, default=_json_default))
    else:
        typer.echo(
            f"Card: {result.card.name} ({result.orientation.value})\n"
            f"Source: {result.provenance.source_id} "
            f"(quantum: {result.provenance.is_quantum})"
        )


@draw_app.command("iching")
def draw_iching_cmd(
    method: str = typer.Option("yarrow", help="yarrow|three_coin|uniform"),
    source: str | None = typer.Option(None, help="Entropy source name"),
    output_json: bool = typer.Option(False, "--json/--no-json", help="Output as JSON"),
) -> None:
    """Draw an I Ching hexagram."""
    from opendivine.oracles.iching import draw_iching_sync
    from opendivine.types import ICMethod

    ic_method = ICMethod(method)
    result = draw_iching_sync(method=ic_method, source=source)

    if output_json:
        data = dataclasses.asdict(result)
        typer.echo(json.dumps(data, indent=2, default=_json_default))
    else:
        lines = [f"Hexagram #{result.primary.number}: {result.primary.name}"]
        if result.changing_lines:
            lines.append(f"Changing lines: {result.changing_lines}")
            if result.secondary:
                lines.append(f"Secondary: #{result.secondary.number} {result.secondary.name}")
        else:
            lines.append("No changing lines")
        typer.echo("\n".join(lines))


@app.command("sources")
def sources_cmd(
    output_json: bool = typer.Option(False, "--json/--no-json", help="Output as JSON"),
) -> None:
    """List available entropy sources."""
    from opendivine.core.registry import SourceRegistry

    registry = SourceRegistry()
    source_list = registry.list_sources()

    if output_json:
        data = [
            {
                "name": s.name,
                "type": s.source_type,
                "is_quantum": s.is_quantum,
                "description": s.description,
                "available": s.available,
            }
            for s in source_list
        ]
        typer.echo(json.dumps(data, indent=2))
    else:
        typer.echo(f"{'Name':<15} {'Type':<12} {'Quantum':<10}")
        typer.echo("-" * 37)
        for s in source_list:
            quantum_str = "yes" if s.is_quantum else "no"
            typer.echo(f"{s.name:<15} {s.source_type:<12} {quantum_str:<10}")


@app.command("version")
def version_cmd() -> None:
    """Show OpenDivine version."""
    from opendivine import __version__

    typer.echo(f"OpenDivine {__version__}")


if __name__ == "__main__":
    app()
