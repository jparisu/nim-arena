"""Minimax plus hand-written endgame knowledge: the "hard" rung.

Two things make this stronger than :class:`~nimarena.bots.basic_minimax.BasicMinimaxBot`
beyond simply searching deeper.

**1. An oracle of positions it knows outright** (:meth:`SmartMinimaxBot.known_value`).
Three structural rules plus a small hand-written table. Every one of them is
*exact*, which is what makes them safe to consult at any node without disturbing
alpha-beta — see the module docstring of :mod:`nimarena.bots.minimax` for why a
cache of search results would not be.

**2. A heuristic that steers toward its own knowledge**
(:meth:`SmartMinimaxBot.evaluate`). Rather than counting sticks, it prefers
positions with fewer *multi-stick* rows, because a board of all-ones is a position
rule 2 below solves exactly. "Move toward positions I understand" is a much better
guide than "make the game shorter".

Why this is still beatable
--------------------------
Every rule here is a special case of the nim-sum (XOR) theorem: a position is lost
for the player to move exactly when the XOR of all rows is zero. Rules 2–4 each
recognise *some* XOR-zero shapes — paired rows cancel, an even number of ones
cancels, and the tabulated triples were chosen because they XOR to zero.

But recognising some shapes is not the same as computing the XOR. From ``[3, 5, 7]``
the only winning move is to ``[3, 5, 6]``, which is neither paired nor tabulated, so
this bot cannot see it and has to rely on its depth-limited search. A player that
actually computes the nim-sum finds it every time, from any position. That gap is
deliberate: it leaves the top of the ladder open.

Note also that ``[1, 3, 5, 7]`` — one of the two default boards — XORs to zero, so
it is a **loss for whoever moves first** under perfect play.
"""

from __future__ import annotations

from collections import Counter

from ..game import State, total_sticks
from .minimax import MinimaxBot

#: Positions known to be lost for the player to move, as canonical tuples
#: (non-empty rows, sorted ascending). Deliberately partial: a handful of classic
#: endgames rather than a generated set, so this bot stays clearly imperfect.
#: Each entry XORs to zero.
_KNOWN_LOSING: frozenset[tuple[int, ...]] = frozenset(
    {
        (1, 2, 3),  # 1^2^3 == 0
        (1, 4, 5),  # 1^4^5 == 0
        (2, 4, 6),  # 2^4^6 == 0
    }
)

#: Penalty per row still holding two or more sticks. Steers play toward all-ones
#: boards, which rule 2 of ``known_value`` decides exactly.
_BIG_ROW_WEIGHT = 1.0
#: Tiny tie-break so that two positions with equally many multi-stick rows still
#: order by size.
_STICK_WEIGHT = 0.01
#: Clamp on the heuristic. Keeps it far inside ``(LOSS, WIN)`` so a proven result
#: always dominates a guess, however large the board.
_HEURISTIC_CAP = 100.0


def _canonical(state: State) -> tuple[int, ...]:
    """Return ``state`` as a comparable key: empty rows dropped, rest sorted.

    Row *order* is irrelevant in NIM and empty rows are dead weight, so
    ``[0, 5, 3]`` and ``[3, 5]`` are the same position. Canonicalising means one
    table entry covers every arrangement of the same multiset of rows.
    """
    return tuple(sorted(s for s in state if s > 0))


class SmartMinimaxBot(MinimaxBot):
    """Negamax + alpha-beta, with hand-written endgame knowledge."""

    def known_value(self, state: State) -> float | None:
        """Return the exact value of ``state`` when a rule recognises it.

        The rules, all from the side-to-move's perspective:

        1. **One non-empty row** — take the whole row, which takes the last
           stick. A win.
        2. **Every row holds one stick** — players alternate taking single
           sticks, so it is a win exactly when the number of rows is odd.
        3. **Every row count appears an even number of times** — a lost
           position: whatever you take from one row, the opponent mirrors it in
           its twin, and the board returns to a paired state until you run out.
        4. **The position is in the hand-written table** — a lost position.

        Returns ``None`` when nothing applies, leaving the search to decide.
        """
        rows = _canonical(state)

        if not rows:
            return None  # terminal; the engine handles it

        if len(rows) == 1:
            return self.WIN

        if all(r == 1 for r in rows):
            return self.WIN if len(rows) % 2 == 1 else self.LOSS

        if all(n % 2 == 0 for n in Counter(rows).values()):
            return self.LOSS

        if rows in _KNOWN_LOSING:
            return self.LOSS

        return None

    def evaluate(self, state: State) -> float:
        """Prefer boards with fewer multi-stick rows.

        Every row reduced to a single stick moves the position closer to the
        all-ones endgame, which :meth:`known_value` decides exactly. So this
        heuristic pushes the search toward the region where the bot stops
        guessing — which is a far better proxy for "good position" than the raw
        stick count.
        """
        big_rows = sum(1 for s in state if s >= 2)
        score = -(_BIG_ROW_WEIGHT * big_rows + _STICK_WEIGHT * total_sticks(state))
        return max(-_HEURISTIC_CAP, min(_HEURISTIC_CAP, score))
