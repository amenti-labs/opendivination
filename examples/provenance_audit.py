"""Provenance audit example — draw tarot and print full receipt as JSON."""

from opendivination.oracles.tarot import draw_tarot_sync
from opendivination.core.provenance import receipt_to_json

result = draw_tarot_sync(source="csprng")

print(f"Card: {result.card.name} ({result.orientation.value})")
print()
print("Full provenance receipt:")
print(receipt_to_json(result.provenance))
