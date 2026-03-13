"""Core type definitions for OpenDivine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


@runtime_checkable
class EntropySource(Protocol):
    """Protocol for all entropy sources."""

    name: str
    source_type: str  # "hardware" | "network" | "software"
    is_quantum: bool
    description: str

    async def get_bytes(self, n: int) -> bytes: ...
    async def is_available(self) -> bool: ...
    async def health_check(self) -> SourceHealth: ...


@dataclass
class SourceHealth:
    available: bool
    quality_score: float  # 0.0-1.0
    last_error: str | None = None
    bytes_served: int = 0


@dataclass
class SourceInfo:
    name: str
    source_type: str  # "hardware" | "network" | "software"
    is_quantum: bool
    description: str
    physics: str | None = None
    available: bool = False
    quality_score: float = 0.0


@dataclass
class ProvenanceReceipt:
    id: str
    timestamp: str  # ISO 8601
    source_id: str
    source_type: str
    is_quantum: bool
    raw_entropy_hex: str
    entropy_bits: int
    quality_score: float
    mode: str
    corpus: str
    result_summary: str


@dataclass
class TarotCard:
    number: int  # 0-77
    name: str
    suit: str | None  # None for Major Arcana
    arcana: str  # "major" | "minor"
    keywords: list[str]
    image_path: str


class Orientation(Enum):
    UPRIGHT = "upright"
    REVERSED = "reversed"


@dataclass
class TarotDraw:
    card: TarotCard
    orientation: Orientation
    provenance: ProvenanceReceipt


@dataclass
class Trigram:
    name: str
    character: str
    attribute: str
    image: str  # natural image (e.g., "Heaven", "Earth")
    lines: tuple[int, int, int]  # 0=yin, 1=yang, bottom to top


class LineType(Enum):
    OLD_YIN = 6  # changing yin → yang (moving line)
    YOUNG_YANG = 7  # stable yang
    YOUNG_YIN = 8  # stable yin
    OLD_YANG = 9  # changing yang → yin (moving line)


class ICMethod(Enum):
    YARROW = "yarrow"
    THREE_COIN = "three_coin"
    UNIFORM = "uniform"


@dataclass
class Hexagram:
    number: int  # 1-64 (King Wen sequence)
    name: str  # English name
    pinyin: str
    character: str  # Chinese character
    upper_trigram: str  # trigram name
    lower_trigram: str  # trigram name
    judgment: str  # brief public-domain description
    image_path: str  # SVG filename


@dataclass
class IChingDraw:
    primary: Hexagram
    lines: list[LineType]  # always 6 lines, bottom to top
    changing_lines: list[int]  # 0-indexed positions of changing lines
    secondary: Hexagram | None  # None if no changing lines
    method: ICMethod
    provenance: ProvenanceReceipt
