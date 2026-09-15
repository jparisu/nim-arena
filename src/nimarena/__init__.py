"""NIM Arena — a parametrized NIM engine, a clean player API, reference AIs,
and a robust round-robin tournament.

The same code powers the graded tournament (in CI) and live play in the browser
(via Pyodide). One source of truth.

Public surface:

* :mod:`nimarena.game` — pure game rules (``legal_moves``, ``apply_move``, ...).
* :class:`nimarena.player.Player` — the interface every AI implements.
* :class:`nimarena.registry.Registry` — the catalogue of players.
* :func:`nimarena.manifest.load_players` — populate the registry from the
  ``players/builtin`` and ``players/custom`` manifests.
* :func:`nimarena.tournament.run_tournament` — the round-robin runner.
"""

from __future__ import annotations

from . import game
from .player import Player
from .registry import REGISTRY, Registry

__all__ = ["game", "Player", "Registry", "REGISTRY", "__version__"]
__version__ = "0.1.0"
