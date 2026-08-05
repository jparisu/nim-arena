"""A generic depth-limited minimax search, with **no domain knowledge at all**.

This module knows how to *search*. It does not know anything about what makes a
NIM position good — that is supplied by a subclass through two hooks:

* :meth:`MinimaxBot.evaluate` — score a position once the depth limit is hit;
* :meth:`MinimaxBot.known_value` — return the *exact* value of a position that is
  already known, so the search can stop there.

Keeping the two apart matters, because they have different soundness rules.

Why an "exact value" oracle is safe but a result cache is not
-------------------------------------------------------------
It is tempting to memoize search results. Under alpha-beta that is **unsound**: a
pruned search returns a *bound*, not a value, so a cached number may be wrong for
a later lookup with a different window. Doing it correctly requires storing
``EXACT``/``LOWER``/``UPPER`` flags plus the depth each entry was proved to, and
checking both on every hit.

:meth:`known_value` sidesteps all of that. It returns values that are known
*independently of the search* — from a hand-written table of positions, or from a
structural rule about the board. Those are exact by construction, they do not
depend on the current window or remaining depth, and so they compose with
alpha-beta for free.

Negamax sign convention
-----------------------
Every value is from the perspective of the **side to move**. A position with no
legal move means the opponent just took the last stick, so the side to move has
already lost: that is :attr:`MinimaxBot.LOSS`. A child's value is negated when it
is brought back to the parent.
"""

from __future__ import annotations

import random
from typing import Any

from ..game import Move, State, apply_move, is_terminal, legal_moves
from ..player import Player

_INF = float("inf")


class MinimaxBot(Player):
    """Depth-limited negamax with alpha-beta pruning.

    Subclass it and override :meth:`evaluate` (and optionally
    :meth:`known_value`) to build a player. Left alone, the search finds a forced
    win or loss within ``depth`` plies and is indifferent to everything else.

    Like every class in this package it stays abstract until a subclass declares
    its identity (:meth:`~nimarena.player.Player.get_name` and friends), so it
    cannot be entered in a tournament by accident.
    """

    #: Value of a position the side to move has already won.
    WIN = 10_000.0
    #: Value of a position the side to move has already lost.
    LOSS = -10_000.0

    def __init__(self, depth: int = 3, seed: int | None = None) -> None:
        """Create the searcher.

        Args:
            depth: plies to search before falling back to :meth:`evaluate`.
                Must be at least 1.
            seed: seed for the private RNG used only to break ties between
                equally-valued moves. A private RNG keeps the bot reproducible
                without touching global random state.

        Raises:
            ValueError: if ``depth`` is less than 1.
        """
        if depth < 1:
            raise ValueError(f"depth must be >= 1, got {depth}")
        self.depth = depth
        self._rng = random.Random(seed)
        #: Populated after each search, for the web "Why did it do that?" panel.
        #: An optional extra, not part of the Player contract. ``Any`` because it
        #: is serialised straight to JSON and crosses into JavaScript.
        self.last_info: dict[str, Any] = {}
        self._nodes = 0

    # ------------------------------------------------------------------ #
    # Hooks for subclasses                                               #
    # ------------------------------------------------------------------ #

    def known_value(self, state: State) -> float | None:
        """Return the exact value of ``state``, or ``None`` if it is not known.

        Consulted at every node *before* the depth limit, so a known position
        stops the search immediately at any depth. Whatever is returned is taken
        as exact and final, from the perspective of the side to move — so return
        ``None`` unless you are certain.

        The default knows nothing.
        """
        return None

    def evaluate(self, state: State) -> float:
        """Score ``state`` from the side-to-move's perspective at the depth limit.

        Return a value strictly between :attr:`LOSS` and :attr:`WIN`, so that a
        proven win or loss always dominates a heuristic guess.

        The default is indifferent (``0.0``): with no heuristic, the search still
        finds forced wins and losses inside ``depth`` plies.
        """
        return 0.0

    # ------------------------------------------------------------------ #
    # Search                                                             #
    # ------------------------------------------------------------------ #

    def choose_move(self, state: State) -> Move:
        """Return the best move found, breaking ties randomly.

        Each root move is searched with a **full window**. Tightening alpha at
        the root would make later moves return bounds rather than values, which
        would corrupt the set of equally-best moves used for tie-breaking.
        """
        self._nodes = 0
        best_value = -_INF
        best_moves: list[Move] = []

        for move in legal_moves(state):
            value = -self._negamax(apply_move(state, move), self.depth - 1, -_INF, _INF)
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
            "note": self._explain(best_value),
        }
        return chosen

    def _negamax(self, state: State, depth: int, alpha: float, beta: float) -> float:
        """Return the negamax value of ``state`` searched ``depth`` more plies.

        Args:
            state: board to evaluate, from the side-to-move's perspective.
            depth: remaining plies before falling back to :meth:`evaluate`.
            alpha: best value the side to move can already guarantee.
            beta: best value the opponent can already guarantee.

        Returns:
            The value of ``state``; higher is better for the side to move.
        """
        self._nodes += 1

        if is_terminal(state):
            # No legal move: the opponent took the last stick, so we have lost.
            return self.LOSS

        known = self.known_value(state)
        if known is not None:
            return known

        # `<= 0`, not `== 0`: choose_move enters the recursion at `depth - 1`, so
        # a depth of 0 would otherwise skip the cutoff and search the whole tree.
        if depth <= 0:
            return self.evaluate(state)

        value = -_INF
        for move in legal_moves(state):
            child = apply_move(state, move)
            value = max(value, -self._negamax(child, depth - 1, -beta, -alpha))
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # alpha-beta cutoff
        return value

    def _explain(self, score: float) -> str:
        """Return a human-readable note about a root ``score``, for the web panel."""
        if score >= self.WIN:
            return f"Found a forced win within {self.depth} plies."
        if score <= self.LOSS:
            return (
                f"Every move loses against perfect play within {self.depth} plies; "
                "playing on in the hope of a mistake."
            )
        return f"No forced result within {self.depth} plies; went with the heuristic."
