"""Level 2 (medium): depth-limited minimax with a deliberately weak heuristic.

Why this is *genuinely* imperfect (and therefore beatable):

* It searches only a fixed number of plies (``depth``, ~5), so from the opening
  it cannot see the whole game tree.
* At the cutoff it evaluates with a **trivial, non-nim-sum heuristic** (total
  sticks remaining). If it used the nim-sum it would be perfect — that is
  exactly what we must avoid here, or the ranking would collapse.

Because it only looks ~5 plies ahead with a weak heuristic, it plays well **near
the endgame** (where 5 plies reach real terminal states) but errs in the
opening/midgame. That makes it stronger than random and weaker than the perfect
XOR player — the correct middle of the ranking.

Implementation notes:

* Uses **negamax** with **alpha-beta pruning** (optional per the spec, but it
  keeps depth-5 searches fast).
* Ties are broken **randomly** among equally-valued moves, both to add variety
  (so games don't degenerate into identical repeats) and to avoid a fixed bias.
* It records its last search into ``self.last_info`` so the web "Why did it do
  that?" panel can show the searched depth, the evaluated score and node count.
  This attribute is an *optional extra*, not part of the Player contract.
"""

from __future__ import annotations

import random

from nimarena.game import State, apply_move, is_terminal, legal_moves, total_sticks
from nimarena.player import Player

_WIN = 10_000
_LOSS = -10_000
#: Weight of the (deliberately weak) total-sticks heuristic. Kept tiny so the
#: exact win/loss signals (``_WIN``/``_LOSS``) always dominate the search.
_HEURISTIC_WEIGHT = 0.01


class MinimaxBot(Player):
    """Depth-limited minimax (negamax + alpha-beta), weak heuristic."""

    name = "MinimaxBot"

    def __init__(self, depth: int = 5, seed: int | None = None) -> None:
        """Create the bot.

        Args:
            depth: number of plies to search before applying the heuristic.
            seed: optional seed for the private RNG used to break ties among
                equally-valued moves; keeps games reproducible in tests.
        """
        self.depth = depth
        self._rng = random.Random(seed)
        self.last_info: dict[str, object] = {}
        #: Nodes visited during the most recent search (for the web panel).
        self._nodes: int = 0

    def choose_move(self, state: State) -> tuple[int, int]:
        """Return the best move found by a depth-limited negamax search.

        Ties among equally-valued moves are broken with the private RNG.
        """
        self._nodes = 0
        best_value = -float("inf")
        best_moves: list[tuple[int, int]] = []

        for move in legal_moves(state):
            child = apply_move(state, move)
            value = -self._negamax(child, self.depth - 1, -float("inf"), float("inf"))
            if value > best_value:
                best_value = value
                best_moves = [move]
            elif value == best_value:
                best_moves.append(move)

        chosen = self._rng.choice(best_moves)
        self.last_info = {
            "player": self.name,
            "depth": self.depth,
            "score": best_value,
            "nodes": self._nodes,
            "chosen": list(chosen),
            "note": "Depth-limited minimax with a total-sticks heuristic "
            "(no nim-sum), so it is strong near the endgame but errs earlier.",
        }
        return chosen

    def _negamax(self, state: State, depth: int, alpha: float, beta: float) -> float:
        """Return the negamax value of ``state`` searched ``depth`` more plies.

        Args:
            state: board to evaluate (from the side-to-move's perspective).
            depth: remaining plies to search before falling back to the
                heuristic.
            alpha: best value the maximizer can already guarantee.
            beta: best value the minimizer can already guarantee.

        Returns:
            The negamax score; higher is better for the side to move.
        """
        self._nodes += 1
        if is_terminal(state):
            # No move available: the side to move already lost (opponent took
            # the last stick). This is the only *exact* signal minimax gets.
            return _LOSS
        if depth == 0:
            return self._heuristic(state)

        value = -float("inf")
        for move in legal_moves(state):
            child = apply_move(state, move)
            value = max(value, -self._negamax(child, depth - 1, -beta, -alpha))
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # alpha-beta cutoff
        return value

    @staticmethod
    def _heuristic(state: State) -> float:
        """Return the (deliberately weak) leaf evaluation of ``state``."""
        # Deliberately weak: prefer positions with fewer sticks remaining.
        # This carries no real information about who wins — that is the point.
        return -_HEURISTIC_WEIGHT * total_sticks(state)
