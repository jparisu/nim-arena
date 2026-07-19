"""Tests that reference players obey the contract and rank as expected."""

from __future__ import annotations

import pytest

from nimarena import game
from nimarena.manifest import load_players
from nimarena.tournament import play_match, run_tournament


@pytest.fixture(scope="module")
def registry():
    return load_players(strict=True)


def test_all_manifest_players_load(registry):
    assert set(registry.names()) == {"RandomBot", "GreedyBot", "MinimaxBot", "PerfectBot"}


@pytest.mark.parametrize("name", ["RandomBot", "GreedyBot", "MinimaxBot", "PerfectBot"])
def test_players_return_legal_moves_and_do_not_mutate(registry, name):
    player = registry.get(name)
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


def test_perfect_bot_moves_to_zero_nim_sum(registry):
    perfect = registry.get("PerfectBot")
    state = [3, 5, 7]  # nim-sum != 0 -> winning
    move = perfect.choose_move(state)
    after = game.apply_move(state, move)
    assert game.nim_sum(after) == 0


def test_perfect_bot_never_loses_from_won_position(registry):
    perfect = registry.get("PerfectBot")
    greedy = registry.get("GreedyBot")
    # [3,5,7] has non-zero nim-sum; the player to move (perfect, going first) wins.
    result = play_match(perfect, greedy, [3, 5, 7], move_timeout_ms=None)
    assert result.winner == "PerfectBot"
    assert result.result == "normal"


def test_ranking_order_is_perfect_gt_minimax_gt_random(registry):
    lb = run_tournament(
        registry.all(),
        starting_states=[[3, 5, 7], [1, 3, 5, 7]],
        repetitions=1,
        move_timeout_ms=None,
        use_subprocess=False,
    )
    rank = {row["player"]: row["rank"] for row in lb["standings"]}
    assert rank["PerfectBot"] < rank["MinimaxBot"]
    assert rank["MinimaxBot"] < rank["RandomBot"]
    # PerfectBot should win every game it plays.
    perfect = next(r for r in lb["standings"] if r["player"] == "PerfectBot")
    assert perfect["losses"] == 0
