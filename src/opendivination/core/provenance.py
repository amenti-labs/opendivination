"""Provenance receipt generation for OpenDivination draws."""

import dataclasses
import datetime
import json
import uuid
from typing import Any

from opendivination.types import ProvenanceReceipt, SourceInfo


def create_provenance(
    source_info: SourceInfo,
    raw_entropy: bytes,
    mode: str,
    corpus: str,
    result_summary: str,
    details: dict[str, Any] | None = None,
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
    detail_payload: dict[str, Any] = {}
    if source_info.backend is not None:
        detail_payload["source_backend"] = source_info.backend
    if source_info.selector is not None:
        detail_payload["source_selector"] = source_info.selector
    if source_info.selection_mode is not None:
        detail_payload["source_selection_mode"] = source_info.selection_mode
    if source_info.conditioning is not None:
        detail_payload["source_conditioning"] = source_info.conditioning
    if source_info.device_mode is not None:
        detail_payload["source_device_mode"] = source_info.device_mode
    if details:
        detail_payload.update(details)

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
        details=detail_payload or None,
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
