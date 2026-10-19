"""Perfect-play Nim bot based on the nim-sum (XOR of all rows)."""

from __future__ import annotations

from functools import reduce
from operator import xor

from nimarena.game import Move, State
from nimarena.player import Player


class XorMaster(Player):
    """Leaves the nim-sum at zero whenever it can."""

    @classmethod
    def get_name(cls) -> str:
        return "XorMaster"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["Antonio Orteu", "mariasanzm"]

    @classmethod
    def get_description(cls) -> str:
        return (
            "Plays the nim-sum strategy: always moves to a position whose XOR "
            "is zero. When already losing, it stalls by taking one stick from "
            "the largest row to give the opponent more chances to err."
        )

    @classmethod
    def get_icon(cls) -> str:
        return "🧮"

    def choose_move(self, state: State) -> Move:
        nim_sum = reduce(xor, state, 0)

        if nim_sum != 0:
            # Winning position: find the row we can reduce to make XOR zero.
            for row, sticks in enumerate(state):
                target = sticks ^ nim_sum
                if target < sticks:
                    return (row, sticks - target)

        # Losing position (nim-sum 0): stall with the smallest legal move.
        row = max(range(len(state)), key=lambda i: state[i])
        return (row, 1)
