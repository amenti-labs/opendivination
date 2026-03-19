"""I Ching changing lines example — yarrow vs three-coin methods."""

from opendivination.oracles.iching import draw_iching_sync
from opendivination.types import ICMethod, LineType

LINE_SYMBOLS = {
    LineType.OLD_YIN: "-- x --  (old yin, changing)",
    LineType.YOUNG_YANG: "-------  (young yang, stable)",
    LineType.YOUNG_YIN: "--   --  (young yin, stable)",
    LineType.OLD_YANG: "---o---  (old yang, changing)",
}


def show_draw(result, label):
    print(f"\n{label}")
    print(
        f"  Primary:  #{result.primary.number} {result.primary.name} ({result.primary.character})"
    )
    print(f"  Method:   {result.method.value}")
    print(f"  Lines (bottom to top):")
    for i, line in enumerate(result.lines):
        marker = " <-- changing" if i in result.changing_lines else ""
        print(f"    Line {i + 1}: {LINE_SYMBOLS[line]}{marker}")
    if result.changing_lines:
        print(f"  Changing positions: {result.changing_lines}")
        print(
            f"  Secondary: #{result.secondary.number} {result.secondary.name} ({result.secondary.character})"
        )
    else:
        print("  No changing lines — hexagram is stable")


yarrow = draw_iching_sync(method=ICMethod.YARROW, source="csprng")
show_draw(yarrow, "Yarrow stalk method")

three_coin = draw_iching_sync(method=ICMethod.THREE_COIN, source="csprng")
show_draw(three_coin, "Three-coin method")
