"""The plain minimax bot: a deliberately weak heuristic, no board knowledge.

This is the "medium" rung. It is genuinely imperfect, and the reason is the
heuristic: at the depth limit it looks only at **how many sticks are left**. That
carries essentially no information about who is winning — which is the point. If
it evaluated with the nim-sum it would be perfect, and the whole difficulty ladder
would collapse into a single unbeatable bot.

The practical effect is that it plays well **near the endgame**, where the search
reaches real terminal positions and the heuristic never gets consulted, and errs
in the opening and midgame, where every leaf is a guess.
"""

from __future__ import annotations

from ..game import State, total_sticks
from .minimax import MinimaxBot

#: Weight of the total-sticks heuristic. Deliberately tiny, so that a proven
#: WIN/LOSS from the search always dominates a heuristic preference.
_HEURISTIC_WEIGHT = 0.01


class BasicMinimaxBot(MinimaxBot):
    """Negamax + alpha-beta, evaluating leaves by total sticks remaining."""

    def evaluate(self, state: State) -> float:
        """Prefer positions with fewer sticks left.

        This is a *bad* heuristic on purpose: the number of sticks remaining says
        almost nothing about who wins a NIM position. It only nudges the bot
        towards shortening the game, which at least keeps it decisive.
        """
        return -_HEURISTIC_WEIGHT * total_sticks(state)
