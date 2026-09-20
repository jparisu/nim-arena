"""Contract tests for the submitted players in ``players/custom/``.

Discovery is **automatic**: this module loads ``players/custom/players.yaml`` and
parametrizes every check over whatever it admits, so a new submission is covered
the moment its manifest line lands — there is nothing here to edit per player.

These tests deliberately live **outside** the main suite. ``tests.yml`` skips this
file and a separate workflow runs it alone, so one broken submission fails its own
check instead of turning every other pull request red. Nothing else in ``tests/``
loads the submitted manifest strictly, for the same reason.

What a submitted player must survive here:

* the manifest loads it and its identity accessors return something usable;
* :meth:`~nimarena.player.Player.create` accepts a seed;
* :meth:`~nimarena.player.Player.choose_move` returns a legal move and never
  mutates the board, on every board, played out to the end;
* a full game against the reference ``random`` player, from both sides, ends
  ``normal`` — no crash, no hang, no illegal move.
"""

from __future__ import annotations

import pytest

from nimarena import game
from nimarena.manifest import CUSTOM, CUSTOM_MANIFEST, load_players
from nimarena.player import Player
from nimarena.registry import Registry
from nimarena.tournament import Budgets, PlayerSpec, play_match

#: Boards the contract checks sweep. Small, awkward positions first — a bot that
#: breaks does so on ``[1]`` or on a mirrored board far more often than on a big
#: one, and the zero row is there because a legal board may contain empty rows.
BOARDS = [[1], [1, 1], [2, 2], [0, 3, 0], [3, 5, 7], [1, 3, 5, 7], [4, 4], [7, 9, 11]]

#: Boards used for the games against ``random``. A subset: each one is played from
#: both sides with every seed, so the game count grows quickly.
GAME_BOARDS = [[1, 1], [3, 5, 7], [1, 3, 5, 7], [7, 9, 11]]

#: Seeds handed to :meth:`~nimarena.player.Player.create`. More than one, because a
#: seeded bot may configure itself differently per seed.
SEEDS = (0, 1, 2)

#: Deliberately far more generous than the tournament's own budget: the claim
#: under test is "does not crash or hang", not "is fast enough". Speed is judged by
#: the tournament, on its runners, with its own budget.
BUDGETS = Budgets(game_ms=10_000, build_ms=5_000)

#: Guard against a bot that returns a legal-but-useless move forever.
_MAX_MOVES = 200


def _load_submitted() -> tuple[Registry | None, Exception | None]:
    """Load the submitted manifest, returning either the registry or the failure.

    A failure is returned rather than raised so that it surfaces as one readable
    test failure instead of a collection error naming no player at all.
    """
    try:
        registry = load_players(
            {CUSTOM: CUSTOM_MANIFEST}, registry=Registry(), strict=True
        )
    except Exception as exc:  # noqa: BLE001 - reported by test_the_manifest_loads
        return None, exc
    return registry, None


_REGISTRY, _LOAD_ERROR = _load_submitted()

#: Names discovered in the manifest. Empty when the manifest is empty (no
#: submissions yet) or failed to load; the parametrized tests then have nothing to
#: run and ``test_the_manifest_loads`` reports why.
CUSTOM_NAMES = sorted(_REGISTRY.names()) if _REGISTRY is not None else []


def _kind(name: str) -> type[Player]:
    """Return the submitted class registered under ``name``."""
    assert _REGISTRY is not None
    return type(_REGISTRY.get(name))


def test_the_manifest_loads():
    """Every admitted submission must import, construct and declare an identity."""
    assert _LOAD_ERROR is None, f"players/custom/players.yaml did not load: {_LOAD_ERROR}"


@pytest.mark.parametrize("name", CUSTOM_NAMES)
def test_declares_a_usable_identity(name):
    cls = _kind(name)
    assert cls.get_name() == name
    authors = cls.get_authors()
    assert isinstance(authors, list) and authors and all(a.strip() for a in authors)
    assert cls.get_description().strip(), f"{name} declares no description"
    icon = cls.get_icon()
    assert isinstance(icon, str) and icon.strip(), f"{name} declares no icon"


@pytest.mark.parametrize("name", CUSTOM_NAMES)
def test_create_accepts_a_seed(name):
    cls = _kind(name)
    for seed in SEEDS:
        player = cls.create(seed=seed)
        assert isinstance(player, cls)
        assert player.name == name


@pytest.mark.parametrize("name", CUSTOM_NAMES)
def test_returns_legal_moves_and_never_mutates_the_board(name):
    """Play every board out to the end, with the bot moving for both sides.

    Moving for both sides is what makes one pass cover the whole game tree the bot
    can reach on that board, rather than only its opening move.
    """
    cls = _kind(name)
    for seed in SEEDS:
        player = cls.create(seed=seed)
        for start in BOARDS:
            state = list(start)
            for _ in range(_MAX_MOVES + 1):
                if game.is_terminal(state):
                    break
                before = list(state)
                move = player.choose_move(state)
                assert state == before, f"{name} mutated the board it was given"
                assert game.is_legal(state, move), (
                    f"{name} returned the illegal move {move!r} on {before}"
                )
                state = game.apply_move(state, move)
            else:
                pytest.fail(f"{name} did not finish {start} in {_MAX_MOVES} moves")


@pytest.mark.parametrize("name", CUSTOM_NAMES)
def test_plays_full_games_against_random_without_failing(name):
    """Full games through the tournament runner, which forfeits on any misbehavior.

    Each game runs in a forked child with a hard deadline, so a bot that hangs is
    killed and reported instead of stalling the run. Losing is fine — ``random``
    is allowed to win; forfeiting is not.
    """
    # Imported here, not at module scope: `players` is a namespace package that
    # only conftest.py puts on sys.path, and the import sorter files it as a
    # third-party package if it sits beside `pytest`.
    from players.builtin.random import Random

    cls = _kind(name)
    failures = []
    for board in GAME_BOARDS:
        for seed in SEEDS:
            for goes_first in (True, False):
                mine = PlayerSpec(cls=cls, seed=seed, name=name)
                theirs = PlayerSpec(cls=Random, seed=seed + 100, name="random")
                first, second = (mine, theirs) if goes_first else (theirs, mine)
                result = play_match(first, second, list(board), BUDGETS)
                if result.result != "normal":
                    failures.append(
                        f"board={board} seed={seed} first={first.name}: "
                        f"{result.result} — {result.detail}"
                    )
    assert not failures, f"{name} failed {len(failures)} game(s):\n" + "\n".join(failures)
