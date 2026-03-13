"""Basic draw example — tarot and I Ching with CSPRNG fallback."""

from opendivine.oracles.tarot import draw_tarot_sync
from opendivine.oracles.iching import draw_iching_sync

result = draw_tarot_sync(source="csprng")
print(f"Tarot: {result.card.name} ({result.orientation.value})")
print(f"Source: {result.provenance.source_id} (quantum: {result.provenance.is_quantum})")

result = draw_iching_sync(source="csprng")
print(f"I Ching: #{result.primary.number}: {result.primary.name}")
if result.secondary:
    print(f"  -> #{result.secondary.number}: {result.secondary.name}")
