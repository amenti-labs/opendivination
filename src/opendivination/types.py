"""Core type definitions for OpenDivination."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

DEFAULT_ENTROPY_SOURCE = "csprng"


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
    backend: str | None = None
    selector: str | None = None
    selection_mode: str | None = None
    conditioning: str | None = None
    device_mode: str | None = None
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
    details: dict[str, Any] | None = None


@dataclass
class TarotCard:
    number: int  # 0-77
    name: str
    suit: str | None  # None for Major Arcana
    arcana: str  # "major" | "minor"
    keywords: list[str]
    image_path: str
    description: str | None = None
    reversed_keywords: list[str] | None = None
    element: str | None = None  # "fire" | "water" | "air" | "earth"
    astrological: str | None = None  # zodiac/planet correspondence
    visual_caption: str | None = None


@dataclass
class CoherenceResult:
    """Semantic similarity between a user question and a drawn symbol."""

    score: float  # 0.0-1.0 cosine similarity
    question_hash: str  # SHA-256 of the question (privacy-safe)
    provider: str  # embedding provider id
    model: str  # embedding model name


class Orientation(Enum):
    UPRIGHT = "upright"
    REVERSED = "reversed"


@dataclass
class TarotDraw:
    card: TarotCard
    orientation: Orientation
    provenance: ProvenanceReceipt
    coherence: CoherenceResult | None = None


class EmbeddingModality(Enum):
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"


class EmbeddingMultimodalSurface(Enum):
    TEXT_ONLY = "text_only"
    SHARED_VECTOR = "shared_vector"
    SPLIT_CHANNELS = "split_channels"


class EmbeddingTaskType(Enum):
    SIMILARITY = "similarity"
    RETRIEVAL_QUERY = "retrieval_query"
    RETRIEVAL_DOCUMENT = "retrieval_document"
    CODE_RETRIEVAL_QUERY = "code_retrieval_query"
    QUESTION_ANSWERING = "question_answering"
    FACT_VERIFICATION = "fact_verification"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"


@dataclass(frozen=True)
class EmbeddingImage:
    data: bytes
    mime_type: str


@dataclass(frozen=True)
class EmbeddingContent:
    text: str | None = None
    image: EmbeddingImage | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def modality(self) -> EmbeddingModality:
        if self.text and self.image:
            return EmbeddingModality.MULTIMODAL
        if self.image:
            return EmbeddingModality.IMAGE
        return EmbeddingModality.TEXT


@dataclass(frozen=True)
class EmbeddingCapabilities:
    supports_text: bool = True
    supports_image: bool = False
    supports_multimodal: bool = False
    supports_task_type: bool = False
    supports_output_dimensions: bool = False


@dataclass
class EmbeddingProviderInfo:
    provider_id: str
    model: str
    space_id: str
    dimensions: int
    normalized: bool = True
    capabilities: EmbeddingCapabilities = field(default_factory=EmbeddingCapabilities)
    multimodal_surface: EmbeddingMultimodalSurface = EmbeddingMultimodalSurface.TEXT_ONLY
    vendor: str | None = None


@runtime_checkable
class EmbeddingProvider(Protocol):
    info: EmbeddingProviderInfo

    async def embed(
        self,
        contents: list[EmbeddingContent],
        *,
        task_type: EmbeddingTaskType = EmbeddingTaskType.SIMILARITY,
        output_dimensions: int | None = None,
    ) -> list[list[float]]: ...


class ResonanceAssetTextProfile(Enum):
    AUTO = "auto"
    DESCRIPTIVE = "descriptive"


class ResonanceEntropyTextProfile(Enum):
    AUTO = "auto"
    BARE_HEX_SPACED = "bare_hex_spaced"
    BARE_HEX_COMPACT = "bare_hex_compact"


@dataclass
class TarotResonanceDraw:
    card: TarotCard
    score: float
    distance: float
    provider: str
    model: str
    space_id: str
    entropy_bytes: int
    asset_text_profile: ResonanceAssetTextProfile
    entropy_text_profile: ResonanceEntropyTextProfile
    shortlist_size: int
    provenance: ProvenanceReceipt
    coherence: CoherenceResult | None = None


@dataclass
class TarotResonanceCorpusPreparation:
    corpus: str
    provider: str
    model: str
    space_id: str
    asset_text_profile: ResonanceAssetTextProfile
    prepared_cards: int
    cache_hit: bool
    cache_variant: str
    cache_path: str


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
    character: str  # Chinese character (e.g. 乾)
    upper_trigram: str  # trigram name
    lower_trigram: str  # trigram name
    judgment: str  # brief public-domain description
    image_path: str  # SVG filename
    image_text: str | None = None  # Da Xiang (Image) commentary
    description: str | None = None  # expanded meaning for interpretation
    line_texts: dict[str, str] | None = None  # changing line texts, keys "1"-"6"
    symbol: str = ""  # Unicode hexagram symbol (e.g. ䷀), set by __post_init__

    def __post_init__(self) -> None:
        if not self.symbol:
            self.symbol = chr(0x4DC0 + self.number - 1)


@dataclass
class IChingDraw:
    primary: Hexagram
    lines: list[LineType]  # always 6 lines, bottom to top
    changing_lines: list[int]  # 0-indexed positions of changing lines
    secondary: Hexagram | None  # None if no changing lines
    method: ICMethod
    provenance: ProvenanceReceipt
    coherence: CoherenceResult | None = None
