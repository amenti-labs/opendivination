"""OpenDivine MCP server — quantum entropy oracle tools."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any, cast

from mcp.server.fastmcp import FastMCP

from opendivine.core.registry import SourceRegistry
from opendivine.oracles.iching import draw_iching_sync
from opendivine.oracles.tarot import draw_tarot_sync
from opendivine.types import ICMethod

mcp = FastMCP("opendivine")


def _sanitize(obj: Any) -> Any:
    """Recursively convert dataclass dicts so Enum values become plain strings/ints."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, tuple):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, Enum):
        return obj.value
    return obj


@mcp.tool()
def draw_tarot(source: str | None = None) -> dict[str, Any]:
    """Draw a tarot card using quantum entropy.

    Returns card name, orientation (upright/reversed), and provenance
    receipt showing entropy source.
    """
    result = draw_tarot_sync(source=source)
    raw = asdict(result)
    return cast(dict[str, Any], _sanitize(raw))


@mcp.tool()
def draw_iching(method: str = "yarrow", source: str | None = None) -> dict[str, Any]:
    """Cast the I Ching using quantum entropy.

    Returns primary hexagram, changing lines, and optional secondary hexagram.
    """
    valid_methods = {m.value for m in ICMethod}
    if method not in valid_methods:
        raise ValueError(
            f"Invalid method '{method}'. Must be one of: {', '.join(sorted(valid_methods))}"
        )

    result = draw_iching_sync(method=ICMethod(method), source=source)
    raw = asdict(result)
    return cast(dict[str, Any], _sanitize(raw))


@mcp.tool()
def entropy_status() -> dict[str, list[dict[str, Any]]]:
    """Check available entropy sources and their quantum status."""
    registry = SourceRegistry()
    sources = registry.list_sources()
    return {
        "sources": [_sanitize(asdict(s)) for s in sources],
    }
