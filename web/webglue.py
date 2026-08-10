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
from nimarena.player import Player
from nimarena.registry import Registry

#: Milliseconds per second, used to report per-move timing.
_MS_PER_SECOND = 1000.0

_REGISTRY: Registry | None = None

#: Independent player instances for the bracket on the Tournament page, keyed by
#: slot id. A kind may enter a bracket several times, and each entrant must have
#: its own instance and seed — sharing one would make two `random` entrants
#: correlated, and let one entrant's cache leak into another's game.
_ENTRANTS: dict[str, Player] = {}


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
                "icon": type(p).get_icon(),
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


# --- tournament entrants --------------------------------------------------- #

def reset_entrants() -> str:
    """Discard every entrant. Called when a new bracket is configured."""
    _ENTRANTS.clear()
    return "ok"


def create_entrant(entrant_id: str, kind: str, seed: int) -> str:
    """Build an independent instance of ``kind`` for one bracket slot.

    Uses :meth:`~nimarena.player.Player.create`, the same factory the real
    tournament uses, so a bot may configure itself from the seed.

    Raises:
        KeyError: if ``kind`` is not a registered player.
    """
    cls = type(_require_registry().get(kind))
    _ENTRANTS[entrant_id] = cls.create(seed=seed)
    return entrant_id


def _entrant(entrant_id: str) -> Player:
    """Return a built entrant, or explain that the bracket was not set up."""
    try:
        return _ENTRANTS[entrant_id]
    except KeyError:
        raise KeyError(f"unknown entrant {entrant_id!r}; call create_entrant first") from None


def entrant_move(entrant_id: str, state_json: str) -> str:
    """Ask one bracket entrant for its move. Same payload as :func:`ask_move`."""
    return _timed_move(_entrant(entrant_id), json.loads(state_json))


def play_auto(a_id: str, b_id: str, state_json: str, max_moves: int = 400) -> str:
    """Play a whole game between two entrants and return it in one call.

    Running the loop here rather than move-by-move from JavaScript keeps a
    bot-vs-bot match to a single crossing of the Python/JS boundary.

    A player that raises or returns an illegal move **forfeits**, mirroring the
    real tournament: the browser enforces no timeout, so a page must never be
    taken down by one bad player.

    Returns JSON ``{"moves": [[row, count], ...], "winner_seat": 0|1,
    "result": ..., "detail": str, "elapsed_ms": [a_total, b_total]}``.
    """
    state = list(json.loads(state_json))
    players = [_entrant(a_id), _entrant(b_id)]
    moves: list[list[int]] = []
    spent = [0.0, 0.0]
    turn = 0

    while not game.is_terminal(state):
        if len(moves) >= max_moves:  # pragma: no cover - defensive
            return json.dumps({
                "moves": moves, "winner_seat": 1 - turn, "result": "forfeit_error",
                "detail": f"game exceeded {max_moves} moves", "elapsed_ms": spent,
            })
        t0 = time.perf_counter()
        try:
            move = players[turn].choose_move(list(state))
        except BaseException as exc:  # noqa: BLE001 - any failure forfeits
            spent[turn] += (time.perf_counter() - t0) * _MS_PER_SECOND
            return json.dumps({
                "moves": moves, "winner_seat": 1 - turn, "result": "forfeit_error",
                "detail": f"raised: {exc!r}", "elapsed_ms": spent,
            })
        spent[turn] += (time.perf_counter() - t0) * _MS_PER_SECOND

        if not game.is_legal(state, move):
            return json.dumps({
                "moves": moves, "winner_seat": 1 - turn, "result": "forfeit_illegal",
                "detail": f"returned illegal move {move!r} for {state}",
                "elapsed_ms": spent,
            })
        row, count = move
        moves.append([int(row), int(count)])
        state = game.apply_move(state, (int(row), int(count)))
        turn = 1 - turn

    # Whoever moved last took the last stick.
    return json.dumps({
        "moves": moves, "winner_seat": 1 - turn, "result": "normal",
        "detail": "", "elapsed_ms": spent,
    })


# --- AI moves -------------------------------------------------------------- #

def _timed_move(player: Player, state: list[int]) -> str:
    """Ask ``player`` for a move on ``state`` and report it with its timing."""
    if game.is_terminal(state):
        raise ValueError(f"no move to make: {state} is terminal")
    t0 = time.perf_counter()
    move = player.choose_move(list(state))
    elapsed_ms = (time.perf_counter() - t0) * _MS_PER_SECOND
    info = getattr(player, "last_info", None)
    return json.dumps({"move": list(move), "elapsed_ms": elapsed_ms, "info": info})


def ask_move(name: str, state_json: str) -> str:
    """Ask the registered player ``name`` for its move on ``state``.

    Returns JSON ``{"move": [row, count], "elapsed_ms": float, "info": {...}|null}``
    where ``info`` is the player's optional ``last_info`` (used by the "Why did
    it do that?" panel).
    """
    # The terminal guard lives in _timed_move: reference bots raise on an empty
    # board rather than returning something illegal, and the tournament never
    # asks — but the browser can, so the UI gets a clear error either way.
    return _timed_move(_require_registry().get(name), json.loads(state_json))


def perfect_analysis(state_json: str) -> str:
    """Compute the perfect (nim-sum) analysis for X-ray mode and hints.

    Returns JSON with the current nim-sum and, when the position is winning, the
    optimal move and the row it touches::

        {"nim_sum": int, "winning": bool,
         "move": [row, count]|null, "target_row": int|null}
    """
    state = json.loads(state_json)
    total_xor = game.nim_sum(state)
    result: dict[str, object] = {
        "nim_sum": total_xor,
        "winning": total_xor != 0,
        "move": None,
        "target_row": None,
    }
    if total_xor != 0:
        for row, sticks in enumerate(state):
            target = sticks ^ total_xor
            if target < sticks:
                result["move"] = [row, sticks - target]
                result["target_row"] = row
                break
    return json.dumps(result)
