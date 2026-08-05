"""Thin Python bridge exposed to the browser (via Pyodide).

The web page calls into this module so that the *same* Python game rules and AI
players run in the browser exactly as they do in the CI tournament — there is no
duplicated game logic in JavaScript.

Everything crosses the Python<->JS boundary as **JSON strings** (state is a list
of ints, moves are ``[row, count]``). That keeps the boundary dumb and avoids
fragile object marshalling. JavaScript ``JSON.stringify``/``JSON.parse`` on its
side; we ``json.loads``/``json.dumps`` on ours.

No timeouts are enforced here — live play is best-effort, by design.
"""

from __future__ import annotations

import json
import time

from nimarena import game
from nimarena.manifest import load_players
from nimarena.registry import Registry

#: Milliseconds per second, used to report per-move timing.
_MS_PER_SECOND = 1000.0

_REGISTRY: Registry | None = None


def _require_registry() -> Registry:
    """Return the loaded registry, or fail with an actionable message.

    Every entry point below goes through this rather than touching the global
    directly: an un-awaited ``init`` otherwise surfaced as
    ``AttributeError: 'NoneType' object has no attribute 'all'``, which says
    nothing about what actually went wrong.
    """
    if _REGISTRY is None:
        raise RuntimeError("webglue.init(base_dir) must be called before using the bridge")
    return _REGISTRY


def init(base_dir: str) -> str:
    """Load players from the manifest under ``base_dir`` and return them as JSON."""
    global _REGISTRY
    _REGISTRY = load_players(f"{base_dir}/players.yaml", f"{base_dir}/players")
    return players_json()


def players_json() -> str:
    """Return the registered players as JSON, with their declared identity.

    Each entry is ``{"name", "authors", "description"}``, read from the player's
    class rather than from any instance, so the UI can label and describe an
    opponent without playing a game.
    """
    return json.dumps(
        [
            {
                "name": type(p).get_name(),
                "authors": type(p).get_authors(),
                "description": type(p).get_description(),
            }
            for p in _require_registry().all()
        ]
    )


# --- pure game rules (single source of truth) ------------------------------ #

def legal_moves(state_json: str) -> str:
    """Return the legal moves for a JSON-encoded state, as a JSON list."""
    return json.dumps(game.legal_moves(json.loads(state_json)))


def apply_move(state_json: str, move_json: str) -> str:
    """Apply a JSON-encoded move to a JSON-encoded state; return the new state."""
    state = json.loads(state_json)
    move = tuple(json.loads(move_json))
    return json.dumps(game.apply_move(state, move))


def is_terminal(state_json: str) -> bool:
    """Return ``True`` if the JSON-encoded state has no sticks left."""
    return game.is_terminal(json.loads(state_json))


def nim_sum(state_json: str) -> int:
    """Return the nim-sum (XOR of all rows) of a JSON-encoded state."""
    return game.nim_sum(json.loads(state_json))


def total_sticks(state_json: str) -> int:
    """Return the total number of sticks in a JSON-encoded state."""
    return game.total_sticks(json.loads(state_json))


# --- AI moves -------------------------------------------------------------- #

def ask_move(name: str, state_json: str) -> str:
    """Ask the registered player ``name`` for its move on ``state``.

    Returns JSON ``{"move": [row, count], "elapsed_ms": float, "info": {...}|null}``
    where ``info`` is the player's optional ``last_info`` (used by the "Why did
    it do that?" panel).
    """
    player = _require_registry().get(name)
    state = json.loads(state_json)
    if game.is_terminal(state):
        # No legal move exists. Reference bots raise here rather than returning
        # something illegal, and the tournament never asks — but the browser can,
        # so give the UI a clear error instead of a bot-shaped crash.
        raise ValueError(f"no move to make: {state} is terminal")
    t0 = time.perf_counter()
    move = player.choose_move(list(state))
    elapsed_ms = (time.perf_counter() - t0) * _MS_PER_SECOND
    info = getattr(player, "last_info", None)
    return json.dumps({"move": list(move), "elapsed_ms": elapsed_ms, "info": info})


def perfect_analysis(state_json: str) -> str:
    """Compute the perfect (nim-sum) analysis for X-ray mode and hints.

    Returns JSON with the current nim-sum and, when the position is winning, the
    optimal move and the row it touches::

        {"nim_sum": int, "winning": bool,
         "move": [row, count]|null, "target_row": int|null}
    """
    state = json.loads(state_json)
    total_xor = game.nim_sum(state)
    result = {"nim_sum": total_xor, "winning": total_xor != 0,
              "move": None, "target_row": None}
    if total_xor != 0:
        for row, sticks in enumerate(state):
            target = sticks ^ total_xor
            if target < sticks:
                result["move"] = [row, sticks - target]
                result["target_row"] = row
                break
    return json.dumps(result)
