"""The `easy` player — difficulty level 1, a greedy rule of thumb."""

from __future__ import annotations

from nimarena.bots import GreedyBot


class Easy(GreedyBot):
    """Always empties the largest row."""

    @classmethod
    def get_name(cls) -> str:
        return "easy"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["jparisu"]

    @classmethod
    def get_icon(cls) -> str:
        return "🌱"

    @classmethod
    def get_description(cls) -> str:
        return (
            "Always empties the largest row. A plausible-looking rule that is "
            "barely better than random: taking as much as possible just hands the "
            "opponent a simpler position."
        )
