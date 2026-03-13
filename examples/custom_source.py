"""Custom entropy source example — implement EntropySource, register, draw."""

import os

from opendivine.core.registry import SourceRegistry
from opendivine.oracles.tarot import draw_tarot
from opendivine.types import SourceHealth
import asyncio


class MyCustomSource:
    """Minimal custom entropy source backed by os.urandom.

    In a real implementation you'd replace get_bytes() with a call to
    your own hardware device, local daemon, or any other entropy provider.
    """

    name: str = "my_custom"
    source_type: str = "software"
    is_quantum: bool = False
    description: str = "Custom os.urandom source (example)"

    async def get_bytes(self, n: int) -> bytes:
        return os.urandom(n)

    async def is_available(self) -> bool:
        return True

    async def health_check(self) -> SourceHealth:
        return SourceHealth(available=True, quality_score=0.5)


async def main():
    registry = SourceRegistry()
    registry.register(MyCustomSource(), priority=1)  # highest priority

    result = await draw_tarot(source="my_custom", registry=registry)
    print(f"Card:   {result.card.name} ({result.orientation.value})")
    print(f"Source: {result.provenance.source_id}")
    print(f"Quantum: {result.provenance.is_quantum}")


asyncio.run(main())
