"""The `random` player — difficulty level 0, the baseline."""

from __future__ import annotations

from nimarena.bots import RandomBot


class Random(RandomBot):
    """Picks a legal move uniformly at random."""

    @classmethod
    def get_name(cls) -> str:
        return "random"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["jparisu"]

    @classmethod
    def get_description(cls) -> str:
        return (
            "Picks uniformly at random among all legal moves. No strategy at all "
            "— the baseline every other player has to beat."
        )
