"""The `hard` player — difficulty level 3: deeper search plus endgame knowledge.

The same search as `medium`, given twice the depth and a much better idea of what
it is looking at. Still not perfect: see
:mod:`nimarena.bots.smart_minimax` for exactly which positions it can and cannot
recognise, and why that gap is deliberate.
"""

from __future__ import annotations

from nimarena.bots import SmartMinimaxBot

#: Plies searched before the heuristic takes over. Affordable at this depth only
#: because of alpha-beta pruning.
DEPTH = 4


class Hard(SmartMinimaxBot):
    """Depth-4 minimax with alpha-beta, a known-position oracle and endgame rules."""

    @classmethod
    def get_name(cls) -> str:
        return "hard"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["jparisu"]

    @classmethod
    def get_icon(cls) -> str:
        return "⚔️"

    @classmethod
    def get_description(cls) -> str:
        return (
            f"Minimax with alpha-beta pruning, searching {DEPTH} plies. Recognises "
            "several endgames outright — a single row, all-ones boards by parity, "
            "mirrored rows, and a few tabulated positions — and steers play toward "
            "the endgames it knows. Strong, but it cannot see every losing position."
        )

    @classmethod
    def create(cls, seed: int) -> Hard:
        return cls(depth=DEPTH, seed=seed)
