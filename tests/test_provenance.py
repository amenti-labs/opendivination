from __future__ import annotations

import json
from dataclasses import asdict

from opendivine.core.provenance import create_provenance, receipt_to_json
from opendivine.types import SourceInfo


def test_create_provenance_and_json_serialization() -> None:
    source_info = SourceInfo(
        name="csprng",
        source_type="software",
        is_quantum=False,
        description="OS cryptographic PRNG",
        available=True,
        quality_score=0.5,
    )

    receipt = create_provenance(
        source_info=source_info,
        raw_entropy=bytes.fromhex("deadbeef"),
        mode="selection",
        corpus="tarot",
        result_summary="The Fool (upright)",
    )

    payload = asdict(receipt)
    required_fields = {
        "id",
        "timestamp",
        "source_id",
        "source_type",
        "is_quantum",
        "raw_entropy_hex",
        "entropy_bits",
        "quality_score",
        "mode",
        "corpus",
        "result_summary",
    }
    assert required_fields.issubset(payload)
    assert payload["source_id"] == "csprng"
    assert payload["raw_entropy_hex"] == "deadbeef"
    assert payload["entropy_bits"] == 32

    json_payload = receipt_to_json(receipt)
    decoded = json.loads(json_payload)
    assert decoded == payload
