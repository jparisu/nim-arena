"""Reusable strategy implementations that the shipped players are built from.

These are **public API**: a submitted player is free to import one and configure
or subclass it. Writing a bot from scratch is the real exercise, but starting from
a working search — and beating it by improving only the heuristic — is a
legitimate and instructive first submission.

The split throughout this package is between *searching* and *knowing*:

* :class:`~nimarena.bots.minimax.MinimaxBot` searches. It holds no NIM knowledge
  whatsoever, only negamax with alpha-beta plus two hooks.
* :class:`~nimarena.bots.basic_minimax.BasicMinimaxBot` and
  :class:`~nimarena.bots.smart_minimax.SmartMinimaxBot` know things. They override
  the hooks and add nothing to the search.

The players in ``players/`` add only *identity* — a name, authors, a description
and a depth. See ``players/hard.py`` for the shortest complete example.
"""

from __future__ import annotations

from .basic_minimax import BasicMinimaxBot
from .greedy_bot import GreedyBot
from .minimax import MinimaxBot
from .random_bot import RandomBot
from .smart_minimax import SmartMinimaxBot

__all__ = [
    "BasicMinimaxBot",
    "GreedyBot",
    "MinimaxBot",
    "RandomBot",
    "SmartMinimaxBot",
]
