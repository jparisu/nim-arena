"""Tests that the admitted players obey the contract and rank as expected."""

from __future__ import annotations

import pytest

from nimarena import game
from nimarena.manifest import load_players
from nimarena.tournament import build_roster, play_match, run_tournament

#: The difficulty ladder, weakest first. One place to edit when a player is added.
LADDER = ["random", "easy", "medium", "hard"]


@pytest.fixture(scope="module")
def registry():
    return load_players(strict=True)


def test_all_manifest_players_load(registry):
    assert set(registry.names()) == set(LADDER)


@pytest.mark.parametrize("name", LADDER)
def test_every_player_declares_its_identity(registry, name):
    cls = type(registry.get(name))
    assert cls.get_name() == name
    authors = cls.get_authors()
    assert isinstance(authors, list) and authors and all(a.strip() for a in authors)
    assert cls.get_description().strip()


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
                result = play_match(first, second, board, move_timeout_ms=None)
                hard_wins += result.winner == "hard"
                games += 1
    # Measured well above 90%; assert a loose bound so the test is not brittle.
    assert hard_wins / games > 0.7, f"hard won only {hard_wins}/{games}"


def test_ranking_order_follows_the_difficulty_ladder(registry):
    lb = run_tournament(
        build_roster(registry.all(), 1),
        starting_states=[[3, 5, 7], [1, 3, 5, 7], [7, 9, 11]],
        repetitions=1,
        move_timeout_ms=None,
        use_subprocess=False,
    )
    rank = {row["player"]: row["rank"] for row in lb["standings"]}
    assert rank["hard#0"] < rank["medium#0"], "hard must outrank medium"
    assert rank["medium#0"] < rank["easy#0"], "medium must outrank easy"
    assert rank["medium#0"] < rank["random#0"], "medium must outrank random"
    # `easy` and `random` are deliberately NOT ordered against each other: greedy
    # play is only marginally better than random in NIM, and which one lands ahead
    # depends on the draw. See devs/DESIGN_DECISIONS.md (D5).


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
