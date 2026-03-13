"""Provenance receipt generation for OpenDivine draws."""

import dataclasses
import datetime
import json
import uuid
from typing import Any

from opendivine.types import ProvenanceReceipt, SourceInfo


def create_provenance(
    source_info: SourceInfo,
    raw_entropy: bytes,
    mode: str,
    corpus: str,
    result_summary: str,
) -> ProvenanceReceipt:
    """Create a provenance receipt for a draw.

    Args:
        source_info: SourceInfo object with entropy source metadata
        raw_entropy: Raw entropy bytes used for the draw
        mode: Draw mode (e.g., "selection", "method")
        corpus: Corpus name (e.g., "tarot", "iching")
        result_summary: Human-readable summary of the result

    Returns:
        ProvenanceReceipt with complete audit trail
    """
    return ProvenanceReceipt(
        id=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_id=source_info.name,
        source_type=source_info.source_type,
        is_quantum=source_info.is_quantum,
        raw_entropy_hex=raw_entropy.hex(),
        entropy_bits=len(raw_entropy) * 8,
        quality_score=source_info.quality_score,
        mode=mode,
        corpus=corpus,
        result_summary=result_summary,
    )


def receipt_to_json(receipt: ProvenanceReceipt) -> str:
    """Convert a provenance receipt to pretty-printed JSON.

    Args:
        receipt: ProvenanceReceipt to serialize

    Returns:
        JSON string with 2-space indentation
    """
    return json.dumps(dataclasses.asdict(receipt), indent=2)


def receipt_to_dict(receipt: ProvenanceReceipt) -> dict[str, Any]:
    """Convert a provenance receipt to a dictionary.

    Args:
        receipt: ProvenanceReceipt to convert

    Returns:
        Dictionary representation for embedding in API responses
    """
    return dataclasses.asdict(receipt)
