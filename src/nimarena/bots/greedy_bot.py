"""A greedy player: always empty the largest row.

Simple, legal, deterministic and clearly beatable — a realistic picture of what a
first attempt looks like. It beats :class:`~nimarena.bots.random_bot.RandomBot`
only marginally, because "take as much as possible" is not a strategy in NIM: it
hands the opponent a simpler position every time.
"""

from __future__ import annotations

from ..game import Move, State
from ..player import Player


class GreedyBot(Player):
    """Removes every stick from the currently largest row."""

    def choose_move(self, state: State) -> Move:
        """Return a move that empties the largest non-empty row in one go.

        Raises:
            ValueError: if ``state`` is terminal. No legal move exists on an
                empty board, so there is nothing correct to return; failing
                loudly beats returning the illegal ``(0, 0)``.
        """
        candidates = [(sticks, row) for row, sticks in enumerate(state) if sticks > 0]
        if not candidates:
            raise ValueError(f"no legal move on a terminal board: {state}")
        sticks, row = max(candidates)
        return (row, sticks)
