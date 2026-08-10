"""Parametrized NIM game engine.

The game is *normal play* NIM: several rows of sticks; on each turn a player
removes one or more sticks from a single row; **the player who removes the last
stick wins**.

Design rules honored by this module:

* The game **state** is a plain, JSON-serializable ``list[int]`` where
  ``state[i]`` is the number of sticks remaining in row ``i``. No custom objects
  ever cross the API boundary.
* A **move** is a plain ``tuple[int, int]`` == ``(row, count)``: remove ``count``
  sticks from row ``row``.
* Every function is **pure**: it never mutates its arguments. In particular
  :func:`apply_move` returns a brand-new state. This matters because minimax
  explores many hypothetical futures, and shared mutable state is a classic
  source of subtle bugs.

There is intentionally **no player/turn concept in here** — the engine only
knows about boards and moves. Turn order, timing and forfeits live in the
tournament (see :mod:`nimarena.tournament`).
"""

from __future__ import annotations

State = list[int]
Move = tuple[int, int]


def legal_moves(state: State) -> list[Move]:
    """Return all legal ``(row, count)`` moves from ``state``.

    A move is legal when ``0 <= row < len(state)`` and
    ``1 <= count <= state[row]``.

    Args:
        state: current board; ``state[i]`` sticks in row ``i``.

    Returns:
        Every legal move, ordered by row then by count. Empty if the board is
        already terminal.
    """
    moves: list[Move] = []
    for row, sticks in enumerate(state):
        for count in range(1, sticks + 1):
            moves.append((row, count))
    return moves


def is_legal(state: State, move: object) -> bool:
    """Return ``True`` if ``move`` is legal from ``state``.

    This is the single source of truth for "what is a legal move", used by the
    tournament to forfeit players that return illegal moves.

    ``move`` is deliberately typed ``object`` rather than :data:`Move`: its whole
    job is to judge what an *untrusted* player handed back, which may be any
    object at all. Annotated as a ``Move``, the shape checks below would be
    provably dead code — and they are the point of the function.
    """
    # Narrowed to tuple/list on purpose. The old form unpacked any iterable,
    # which meant validating a generator silently *consumed* it — the exact bug
    # that used to abort a whole tournament. A move is documented as a pair, and
    # the two callers that matter hand over a tuple (the tournament normalises
    # first) or a list (decoded JSON).
    if not isinstance(move, (tuple, list)) or len(move) != 2:
        return False
    row, count = move
    if not isinstance(row, int) or not isinstance(count, int):
        return False
    if row < 0 or row >= len(state):
        return False
    return 1 <= count <= state[row]


def apply_move(state: State, move: Move) -> State:
    """Return a **new** state with ``move`` applied.

    Does **not** mutate ``state``.

    Args:
        state: current board.
        move: ``(row, count)`` to apply.

    Returns:
        A new board with ``count`` sticks removed from row ``row``.

    Raises:
        ValueError: if ``move`` is not legal from ``state``.
    """
    if not is_legal(state, move):
        raise ValueError(f"Illegal move {move!r} for state {state!r}")
    row, count = move
    new_state = list(state)
    new_state[row] -= count
    return new_state


def is_terminal(state: State) -> bool:
    """Return ``True`` if no sticks remain (the game is over)."""
    return all(sticks == 0 for sticks in state)


def nim_sum(state: State) -> int:
    """Return the nim-sum (bitwise XOR of all rows).

    A position is a loss for the player *to move* (under perfect play) iff its
    nim-sum is zero. This powers the perfect player and the web X-ray mode.
    """
    result = 0
    for sticks in state:
        result ^= sticks
    return result


def total_sticks(state: State) -> int:
    """Return the total number of sticks left on the board."""
    return sum(state)
