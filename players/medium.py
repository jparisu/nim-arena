"""The `medium` player — difficulty level 2: shallow search, weak heuristic."""

from __future__ import annotations

from nimarena.bots import BasicMinimaxBot

#: Plies searched before the heuristic takes over. Shallow on purpose: this is
#: what keeps `medium` clearly weaker than `hard`, which searches the same way.
DEPTH = 2


class Medium(BasicMinimaxBot):
    """Depth-2 minimax with alpha-beta and a total-sticks heuristic."""

    @classmethod
    def get_name(cls) -> str:
        return "medium"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["jparisu"]

    @classmethod
    def get_icon(cls) -> str:
        return "🧠"

    @classmethod
    def get_description(cls) -> str:
        return (
            f"Minimax with alpha-beta pruning, searching {DEPTH} plies and then "
            "guessing from the number of sticks left. Solid right at the end of a "
            "game, unreliable before that."
        )

    @classmethod
    def create(cls, seed: int) -> Medium:
        return cls(depth=DEPTH, seed=seed)
