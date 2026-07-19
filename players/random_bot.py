"""Level 1 (easy): a player that picks a legal move uniformly at random.

This is the essential baseline *and* the template every newcomer copies. It is
the simplest possible correct :class:`~nimarena.player.Player`.
"""

from __future__ import annotations

import random

from nimarena.game import State, legal_moves
from nimarena.player import Player


class RandomBot(Player):
    """Chooses uniformly among all legal moves."""

    name = "RandomBot"

    def __init__(self, seed: int | None = None) -> None:
        """Create the bot.

        Args:
            seed: optional seed for the private RNG. A private RNG keeps this bot
                reproducible in tests without touching global random state.
        """
        self._rng = random.Random(seed)

    def choose_move(self, state: State) -> tuple[int, int]:
        """Return a legal move chosen uniformly at random."""
        return self._rng.choice(legal_moves(state))
