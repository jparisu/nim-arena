from nimarena.game import Move, State
from nimarena.player import Player


class ManuelPlayer(Player):
    @classmethod
    def get_name(cls) -> str:
        return "ManuelBotUsopp"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["Manuel Martin"]

    @classmethod
    def get_description(cls) -> str:
        return (
            "Perfect nim-sum player: always leaves the XOR of the rows at zero. "
            "From a lost position it removes as little as possible, leaving the "
            "opponent the fewest winning replies so any slip can be punished."
        )

    @classmethod
    def get_icon(cls) -> str:
        return "🤥"

    def choose_move(self, state: State) -> Move:
        """Leave a zero nim-sum if possible; otherwise make the hardest position."""
        nim_sum = 0
        for sticks in state:
            nim_sum ^= sticks

        if nim_sum != 0:
            # Winning position: shrink a row so the XOR of every row becomes zero.
            for row, sticks in enumerate(state):
                target = sticks ^ nim_sum
                if target < sticks:
                    return (row, sticks - target)

        # Losing position against perfect play: stall, and leave the opponent
        # as few winning replies as possible so a mistake is more likely.
        best_move: Move | None = None
        best_key: tuple[int, int] | None = None
        for row, sticks in enumerate(state):
            for count in range(1, sticks + 1):
                after = list(state)
                after[row] -= count
                new_sum = nim_sum ^ sticks ^ after[row]
                winning_replies = sum(1 for s in after if s ^ new_sum < s)
                key = (winning_replies, count)
                if best_key is None or key < best_key:
                    best_key = key
                    best_move = (row, count)
        if best_move is None:
            raise AssertionError("never called on an empty board")
        return best_move
