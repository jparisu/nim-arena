from functools import reduce

from nimarena.game import State, Move
from nimarena.game import legal_moves, apply_move
from nimarena.player import Player

class NimSumBot(Player):
    @classmethod
    def get_name(cls) -> str:
        return "NimSumBot"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["tu nombre"]

    @classmethod
    def get_description(cls) -> str:
        return "It would always win if possible using XOR rule."

    @classmethod
    def get_icon(cls) -> str:
        return "🥷"

    def __calculate_nimsum(self, state: State) -> int:
        """Calculate whether current XOR."""
        return int(reduce(lambda x, y: x ^ y, state))

    def __choose_first_move(self, state: State) -> Move:
        """If XOR is not favorable, play the first valid move."""
        for row, sticks in enumerate(state):
            if sticks > 0:
                return (row, 1)
        raise AssertionError("never called on an empty board")

    def __choose_xor_move(self, state: State) -> Move:
        """Check every move and use the one that makes XOR = 0."""
        for move in legal_moves(state):
            next_state = apply_move(state, move)
            if self.__calculate_nimsum(next_state) == 0:
                return move

        return self.__choose_first_move(state)

    def choose_move(self, state: State) -> Move:
        """Calculate nim-sum by XOR and play accordingly."""
        return self.__choose_xor_move(state)
