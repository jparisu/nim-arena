from functools import reduce

from nimarena.game import Move, State
from nimarena.player import Player


class DanielaBot(Player):
    @classmethod
    def get_name(cls) -> str:
        return "DanielaBot"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["Daniela González"]

    @classmethod
    def get_description(cls) -> str:
        return "Plays perfect Nim: always leaves a nim-sum of 0 when possible."

    @classmethod
    def get_icon(cls) -> str:
        return "🌸"

    def choose_move(self, state: State) -> Move:
        nim_sum = reduce(lambda a, b: a ^ b, state)

        # Winning position: leave the nim-sum at 0.
        if nim_sum != 0:
            for row, sticks in enumerate(state):
                target = sticks ^ nim_sum
                if target < sticks:
                    return (row, sticks - target)

        # Losing position: take a single stick from the largest row and wait for a mistake.
        row = max(range(len(state)), key=lambda r: state[r])
        return (row, 1)
