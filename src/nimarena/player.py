"""The player API — the spine of the whole project.

Everything (the tournament, the web page, and every externally submitted bot)
depends on this one small interface. It is deliberately **minimal**: a player
carries a ``name`` and implements a single method, :meth:`Player.choose_move`.

Keeping the contract tiny is a feature: every extra parameter is one more thing
an outsider can get wrong. Concerns that belong to the *caller* — timeouts,
move history, opponent identity — deliberately live in the tournament, not here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .game import State


class Player(ABC):
    """A NIM player. Implement :meth:`choose_move` to build an AI.

    A player receives the current board (the number of rows is ``len(state)``,
    and ``state[i]`` is the number of sticks in row ``i``) and must return the
    move it wants to make as a tuple ``(row_index, sticks_to_remove)``.

    Attributes:
        name: Human-readable, unique player name. Shown in the UI and the
            scoreboard. Override it in your subclass.
    """

    #: Human-readable, unique player name. Shown in the UI and the scoreboard.
    name: str = "unnamed"

    @abstractmethod
    def choose_move(self, state: State) -> tuple[int, int]:
        """Choose a move for the given board.

        Args:
            state: list of ints; ``state[i]`` = sticks remaining in row ``i``.
                Treat it as **read-only**: do not mutate it.

        Returns:
            ``(row, count)`` where ``0 <= row < len(state)`` and
            ``1 <= count <= state[row]``. The move **must** be legal — an
            illegal move forfeits the game in the tournament.
        """
        ...

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<{type(self).__name__} name={self.name!r}>"
