"""Level 3 (hard): the provably optimal player, using the nim-sum (XOR).

Normal-play NIM is a solved game. The strategy:

1. Compute ``nim_sum = XOR of all rows``.
2. If ``nim_sum != 0``: there is a row ``i`` with ``(state[i] ^ nim_sum) <
   state[i]``. Reduce that row to ``state[i] ^ nim_sum``. The resulting position
   has nim-sum 0, handing the opponent a losing position. Such a move always
   exists when the nim-sum is non-zero.
3. If ``nim_sum == 0``: the position is theoretically lost. Play any legal move
   (here: remove one stick from the first non-empty row) and hope the opponent
   errs.

Against any imperfect opponent that ever leaves a non-zero nim-sum on this
player's turn, it wins. From a winning starting position, played out fully, it
never loses.

Like the minimax bot, it records ``self.last_info`` (nim-sum before/after) for
the web explanation panel. That attribute is an optional extra, not part of the
Player contract.
"""

from __future__ import annotations

from nimarena.game import State, legal_moves, nim_sum
from nimarena.player import Player


class PerfectBot(Player):
    """Plays optimally via the nim-sum; never loses from a won position."""

    name = "PerfectBot"

    def __init__(self) -> None:
        """Create the bot with an empty explanation record."""
        self.last_info: dict[str, object] = {}

    def choose_move(self, state: State) -> tuple[int, int]:
        """Return the nim-sum-optimal move, or a stalling move if lost."""
        total_xor = nim_sum(state)

        if total_xor != 0:
            for row, sticks in enumerate(state):
                target = sticks ^ total_xor
                if target < sticks:
                    move = (row, sticks - target)
                    self._record(state, move, total_xor, winning=True)
                    return move

        # nim_sum == 0 (lost position): stall with a minimal legal move.
        move = self._first_legal(state)
        self._record(state, move, total_xor, winning=False)
        return move

    @staticmethod
    def _first_legal(state: State) -> tuple[int, int]:
        """Return a minimal legal move: remove one stick from the first row."""
        for row, sticks in enumerate(state):
            if sticks > 0:
                return (row, 1)
        # Only reachable if called on a terminal board (never happens in play).
        return legal_moves(state)[0]

    def _record(
        self, state: State, move: tuple[int, int], nim_before: int, *, winning: bool
    ) -> None:
        """Store an explanation of ``move`` in ``self.last_info`` for the web panel."""
        row, count = move
        after = list(state)
        after[row] -= count
        self.last_info = {
            "player": self.name,
            "nim_sum_before": nim_before,
            "nim_sum_after": nim_sum(after),
            "winning": winning,
            "chosen": [row, count],
            "note": (
                "Non-zero nim-sum: moved to a zero-nim-sum position (a forced win)."
                if winning
                else "Zero nim-sum: theoretically lost, stalling and hoping for a mistake."
            ),
        }
