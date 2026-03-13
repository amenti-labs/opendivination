from __future__ import annotations

import asyncio

from opendivine.core.provenance import create_provenance
from opendivine.core.registry import SourceRegistry
from opendivine.core.sampling import rejection_sample, rejection_sample_weighted
from opendivine.corpora.iching import hexagram_by_lines, load_iching_corpus
from opendivine.types import IChingDraw, ICMethod, LineType

_registry: SourceRegistry | None = None
_corpus_loaded = False

_LINE_TYPE_BY_INDEX = [
    LineType.OLD_YIN,
    LineType.YOUNG_YANG,
    LineType.YOUNG_YIN,
    LineType.OLD_YANG,
]


def _get_registry(registry: SourceRegistry | None) -> SourceRegistry:
    global _registry
    if registry is not None:
        return registry
    if _registry is None:
        _registry = SourceRegistry()
    return _registry


def _ensure_corpus_loaded() -> None:
    global _corpus_loaded
    if not _corpus_loaded:
        load_iching_corpus()
        _corpus_loaded = True


def _line_to_yin_yang(line: LineType) -> int:
    if line in (LineType.OLD_YIN, LineType.YOUNG_YIN):
        return 0
    return 1


def _sample_line(entropy: bytes, method: ICMethod) -> tuple[LineType, int]:
    if method == ICMethod.YARROW:
        index, bytes_consumed = rejection_sample_weighted(
            entropy,
            [1 / 16, 5 / 16, 7 / 16, 3 / 16],
        )
    elif method == ICMethod.THREE_COIN:
        index, bytes_consumed = rejection_sample_weighted(
            entropy,
            [1 / 8, 3 / 8, 3 / 8, 1 / 8],
        )
    else:
        index, bytes_consumed = rejection_sample(entropy, 4)

    return _LINE_TYPE_BY_INDEX[index], bytes_consumed


def _split_hexagram_lines(
    lines: list[int],
) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    return (lines[3], lines[4], lines[5]), (lines[0], lines[1], lines[2])


async def draw_iching(
    method: ICMethod = ICMethod.YARROW,
    source: str | None = None,
    registry: SourceRegistry | None = None,
) -> IChingDraw:
    _ensure_corpus_loaded()
    active_registry = _get_registry(registry)

    entropy, source_info = await active_registry.get_bytes(256, source=source)

    line_types: list[LineType] = []
    offset = 0
    for _ in range(6):
        line_type, bytes_consumed = _sample_line(entropy[offset:], method)
        line_types.append(line_type)
        offset += bytes_consumed

    primary_lines = [_line_to_yin_yang(line_type) for line_type in line_types]
    primary_upper, primary_lower = _split_hexagram_lines(primary_lines)
    primary = hexagram_by_lines(primary_upper, primary_lower)

    changing_lines = [
        index
        for index, line_type in enumerate(line_types)
        if line_type in (LineType.OLD_YIN, LineType.OLD_YANG)
    ]

    secondary = None
    if changing_lines:
        secondary_lines = list(primary_lines)
        for index in changing_lines:
            secondary_lines[index] = 1 - secondary_lines[index]
        secondary_upper, secondary_lower = _split_hexagram_lines(secondary_lines)
        secondary = hexagram_by_lines(secondary_upper, secondary_lower)

    secondary_label = secondary.number if secondary is not None else "none"
    summary = (
        f"primary=#{primary.number};secondary={secondary_label};changing={len(changing_lines)}"
    )
    receipt = create_provenance(
        source_info=source_info,
        raw_entropy=entropy[:offset],
        mode=method.value,
        corpus="iching",
        result_summary=summary,
    )

    return IChingDraw(
        primary=primary,
        lines=line_types,
        changing_lines=changing_lines,
        secondary=secondary,
        method=method,
        provenance=receipt,
    )


def draw_iching_sync(
    method: ICMethod = ICMethod.YARROW,
    source: str | None = None,
) -> IChingDraw:
    return asyncio.run(draw_iching(method=method, source=source))


__all__ = ["draw_iching", "draw_iching_sync"]
