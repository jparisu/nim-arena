"""Tests that the admitted players obey the contract and rank as expected."""

from __future__ import annotations

import pytest

from nimarena import game
from nimarena.manifest import BUILTIN, BUILTIN_MANIFEST, load_players
from nimarena.registry import Registry
from nimarena.tournament import UNLIMITED, build_roster, play_match, run_tournament

#: The reference difficulty ladder that ships with the repository, weakest first.
#:
#: Every assertion below is scoped to these four **on purpose**. The manifest is
#: an open admission list: any merged pull request adds a player to it. A test
#: that pinned the *exact* roster would therefore turn CI red on every single
#: submission — so the roster is only ever checked for what must be present,
#: never for what must be absent. A submitted bot proves itself in the
#: tournament, which is built to survive a bad one; it is not this suite's job.
LADDER = ["random", "easy", "medium", "hard"]


@pytest.fixture(scope="module")
def registry():
    # Only the built-in manifest. A submission is an outsider's code: loading it
    # strictly here would let one broken bot fail the whole suite, and so every
    # unrelated pull request. Submissions are checked by tests/test_custom_players.py.
    return load_players({BUILTIN: BUILTIN_MANIFEST}, registry=Registry(), strict=True)


def test_the_manifest_loads_without_error(registry):
    """Whatever ``players/builtin/players.yaml`` admits must load; the fixture is ``strict``."""
    assert registry.names(), "the manifest admitted no players at all"


def test_the_reference_ladder_is_admitted(registry):
    """The four built-in players must always be there. Others may join them."""
    assert set(LADDER) <= set(registry.names())


@pytest.mark.parametrize("name", LADDER)
def test_every_player_declares_its_identity(registry, name):
    cls = type(registry.get(name))
    assert cls.get_name() == name
    authors = cls.get_authors()
    assert isinstance(authors, list) and authors and all(a.strip() for a in authors)
    assert cls.get_description().strip()
    icon = cls.get_icon()
    assert isinstance(icon, str) and icon.strip(), f"{name} declares no icon"


@pytest.mark.parametrize("name", LADDER)
def test_create_accepts_a_seed_and_returns_a_player(registry, name):
    cls = type(registry.get(name))
    player = cls.create(seed=7)
    assert isinstance(player, cls)
    assert player.name == name


@pytest.mark.parametrize("name", LADDER)
def test_players_return_legal_moves_and_do_not_mutate(registry, name):
    player = type(registry.get(name)).create(seed=0)
    # Sweep a handful of boards, playing each out to the end.
    for start in ([3, 5, 7], [1, 3, 5, 7], [1], [0, 2, 0], [4, 4]):
        state = list(start)
        guard = 0
        while not game.is_terminal(state):
            before = list(state)
            move = player.choose_move(state)
            assert state == before, f"{name} mutated the state"
            assert game.is_legal(state, move), f"{name} returned illegal move {move}"
            state = game.apply_move(state, move)
            guard += 1
            assert guard < 200


def test_random_varies_with_the_seed(registry):
    """Different seeds must give a different game, or repetitions are wasted."""
    cls = type(registry.get("random"))
    board = [7, 9, 11]
    sequences = []
    for seed in (0, 1, 2, 3):
        player = cls.create(seed=seed)
        state, moves = list(board), []
        while not game.is_terminal(state):
            move = player.choose_move(state)
            moves.append(move)
            state = game.apply_move(state, move)
        sequences.append(tuple(moves))
    assert len(set(sequences)) > 1, "seeding had no effect on play"


def test_same_seed_reproduces_the_same_play(registry):
    cls = type(registry.get("random"))
    state = [3, 5, 7]
    assert cls.create(seed=42).choose_move(list(state)) == (
        cls.create(seed=42).choose_move(list(state))
    )


def test_hard_beats_medium_head_to_head(registry):
    hard = type(registry.get("hard"))
    medium = type(registry.get("medium"))
    hard_wins = 0
    games = 0
    for board in ([3, 5, 7], [7, 9, 11]):
        for seed in range(3):
            for hard_first in (True, False):
                a, b = hard.create(seed=seed), medium.create(seed=seed + 100)
                first, second = (a, b) if hard_first else (b, a)
                result = play_match(first, second, board, UNLIMITED)
                hard_wins += result.winner == "hard"
                games += 1
    # Measured well above 90%; assert a loose bound so the test is not brittle.
    assert hard_wins / games > 0.7, f"hard won only {hard_wins}/{games}"


def test_ranking_order_follows_the_difficulty_ladder(registry):
    # Only the reference ladder: the claim under test is about *their* relative
    # strength, and a full-roster round-robin would grow with every submission.
    lb = run_tournament(
        build_roster([registry.get(n) for n in LADDER], 1),
        starting_states=[[3, 5, 7], [1, 3, 5, 7], [7, 9, 11]],
        repetitions=1,
        budgets=UNLIMITED,
        use_subprocess=False,
    )
    rank = {row["player"]: row["rank"] for row in lb["standings"]}
    assert rank["hard_0"] < rank["medium_0"], "hard must outrank medium"
    assert rank["medium_0"] < rank["easy_0"], "medium must outrank easy"
    assert rank["medium_0"] < rank["random_0"], "medium must outrank random"
    # `easy` and `random` are deliberately NOT ordered against each other: greedy
    # play is only marginally better than random in NIM, and which one lands ahead
    # depends on the draw.


def test_hard_recognises_the_endgames_it_claims_to(registry):
    """The oracle rules must fire, and must agree with NIM theory."""
    hard = type(registry.get("hard")).create(seed=0)
    # A single non-empty row: take it all and win.
    assert hard.choose_move([0, 5, 0]) == (1, 5)
    # Mirrored rows are lost for the mover, so from [3, 3, 5] the winning move is
    # to remove all of the odd row and hand back a mirrored board.
    assert hard.choose_move([3, 3, 5]) == (2, 5)
    # An odd number of single sticks is a win; take one and leave an even count.
    row, count = hard.choose_move([1, 1, 1])
    assert count == 1


def test_every_player_has_a_distinct_icon(registry):
    """Icons are how a player is recognised at a glance, so they must not collide."""
    icons = [type(registry.get(n)).get_icon() for n in LADDER]
    assert len(set(icons)) == len(icons), f"duplicate icons: {icons}"


def test_leaderboard_carries_a_player_directory(registry):
    """The scoreboard reads identity from the leaderboard, not the live registry."""
    lb = run_tournament(
        build_roster([registry.get(n) for n in LADDER], 2),
        starting_states=[[1, 2, 3]], repetitions=1,
        budgets=UNLIMITED, use_subprocess=False,
    )
    directory = {p["name"]: p for p in lb["players"]}
    assert set(directory) == set(LADDER), "one entry per kind, not per roster copy"
    for entry in directory.values():
        assert entry["icon"].strip()
        assert entry["authors"]
        assert entry["description"].strip()
    # Roster names carry an underscore suffix the web app renders as a subscript.
    assert all("_" in r["player"] for r in lb["standings"])
