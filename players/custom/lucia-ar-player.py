from nimarena.game import Move, State
from nimarena.player import Player


class LuciaBot(Player):
    @classmethod
    def get_name(cls) -> str:
        return "LuciaBot"

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["Lucía Argüello"]

    @classmethod
    def get_description(cls) -> str:
        return "Always removes an entire row: the first one that is not empty."

    @classmethod
    def get_icon(cls) -> str:
        return "🧹"

    def choose_move(self, state: State) -> Move:
        """Take every stick from the first non-empty row."""
        for row, sticks in enumerate(state):
            if sticks > 0:
                return (row, sticks)
        raise AssertionError("never called on an empty board")
