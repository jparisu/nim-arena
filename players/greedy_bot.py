"""A worked example player, referenced by the docs' "submit a player" guide.

GreedyBot always empties the largest row in one move. It is simple, legal, and
clearly beatable — a realistic example of what a newcomer's first submission
looks like. Copy this file to start your own player.
"""

from __future__ import annotations

from nimarena.game import State
from nimarena.player import Player


class GreedyBot(Player):
    """Removes every stick from the currently largest row."""

    name = "GreedyBot"

    def choose_move(self, state: State) -> tuple[int, int]:
        """Return a move that empties the largest row in one go."""
        # Pick the row with the most sticks and take all of them.
        row = max(range(len(state)), key=lambda i: state[i])
        return (row, state[row])
