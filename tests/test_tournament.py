"""Tests for tournament robustness: timeouts, errors, illegal moves -> forfeits."""

from __future__ import annotations

import pytest

from nimarena.player import Player
from nimarena.tournament import build_roster, play_match, run_tournament


class _Stub(Player):
    """Base for test players: derives the required identity from the class name.

    Keeps each stub below to just its ``choose_move``, which is the behaviour
    under test.
    """

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["tests"]

    @classmethod
    def get_description(cls) -> str:
        return f"Test stub {cls.__name__}."


class OneStickBot(_Stub):
    """Always removes one stick from the first non-empty row (legal, simple)."""

    def choose_move(self, state):
        for row, sticks in enumerate(state):
            if sticks > 0:
                return (row, 1)
        raise AssertionError("called on terminal board")


class AllRowBot(_Stub):
    """Empties the first non-empty row (legal, simple, distinct from OneStickBot)."""

    def choose_move(self, state):
        for row, sticks in enumerate(state):
            if sticks > 0:
                return (row, sticks)
        raise AssertionError("called on terminal board")


class CrashBot(_Stub):
    def choose_move(self, state):
        raise RuntimeError("boom")


class CheatBot(_Stub):
    def choose_move(self, state):
        return (0, 999)  # illegal: too many sticks


class SlowBot(_Stub):
    def choose_move(self, state):
        while True:  # never returns -> must be killed by the subprocess timeout
            pass


def test_normal_game_has_a_winner():
    result = play_match(OneStickBot(), OneStickBot(), [1, 1, 1], move_timeout_ms=None)
    assert result.result == "normal"
    assert result.winner in {"OneStickBot"}
    # 3 sticks, one removed per turn -> first player takes the last (odd count).
    assert result.winner == result.player_first


def test_exception_forfeits_and_opponent_wins():
    result = play_match(CrashBot(), OneStickBot(), [3, 5, 7], move_timeout_ms=None)
    assert result.result == "forfeit_error"
    assert result.winner == "OneStickBot"


def test_illegal_move_forfeits():
    result = play_match(CheatBot(), OneStickBot(), [3, 5, 7], move_timeout_ms=None)
    assert result.result == "forfeit_illegal"
    assert result.winner == "OneStickBot"


def test_hung_bot_is_killed_and_forfeits():
    # Uses the process-based hard timeout; the infinite loop must be terminated.
    result = play_match(SlowBot(), OneStickBot(), [3, 5, 7], move_timeout_ms=300)
    assert result.result == "forfeit_timeout"
    assert result.winner == "OneStickBot"


def test_run_tournament_survives_a_bad_bot():
    players = [OneStickBot(), CrashBot(), CheatBot()]
    lb = run_tournament(
        players, starting_states=[[1, 2, 3]], repetitions=1,
        move_timeout_ms=None, use_subprocess=False,
    )
    # The run completes and produces standings for everyone despite bad bots.
    assert {r["player"] for r in lb["standings"]} == {
        "OneStickBot", "CrashBot", "CheatBot"
    }
    good = next(r for r in lb["standings"] if r["player"] == "OneStickBot")
    assert good["rank"] == 1


def test_build_roster_duplicates_each_kind_with_seed_suffixes():
    # A deterministic bot ignores the seed but is still duplicated so it faces itself.
    roster = build_roster([OneStickBot()])
    assert [p.name for p in roster] == ["OneStickBot#0", "OneStickBot#1"]


def test_build_roster_uses_the_create_factory():
    """The roster must be built through create(), not by calling the class."""
    built_with: list[int] = []

    class Recording(_Stub):
        @classmethod
        def create(cls, seed: int):
            built_with.append(seed)
            return cls()

        def choose_move(self, state):
            return (0, 1)

    build_roster([Recording()], repetition=3)
    assert built_with == [0, 1, 2]


def test_build_roster_seeds_random_bots_reproducibly():
    from players.random import Random

    a, b = build_roster([Random.create(seed=0)])
    assert a.name == "random#0"
    assert b.name == "random#1"
    # Each copy behaves exactly like a fresh instance created with the same seed.
    state = [3, 5, 7]
    assert a.choose_move(list(state)) == Random.create(seed=0).choose_move(list(state))
    assert b.choose_move(list(state)) == Random.create(seed=1).choose_move(list(state))


def test_build_roster_respects_repetition_count():
    roster = build_roster([OneStickBot()], repetition=3)
    assert [p.name for p in roster] == ["OneStickBot#0", "OneStickBot#1", "OneStickBot#2"]


def test_build_roster_rejects_zero_repetition():
    with pytest.raises(ValueError):
        build_roster([OneStickBot()], repetition=0)


def test_build_roster_lets_a_kind_play_itself():
    # Two seeded copies of the same kind are distinct opponents in the roster.
    roster = build_roster([OneStickBot()])
    lb = run_tournament(
        roster, starting_states=[[1, 2, 3]], repetitions=1,
        move_timeout_ms=None, use_subprocess=False,
    )
    assert {r["player"] for r in lb["standings"]} == {"OneStickBot#0", "OneStickBot#1"}
    # They played each other (both ways) -> one win and one loss each.
    assert all(r["games"] == 2 for r in lb["standings"])


def test_leaderboard_schema_shape():
    lb = run_tournament(
        [OneStickBot(), CheatBot()],
        starting_states=[[1, 2]],
        repetitions=2,
        move_timeout_ms=None,
        use_subprocess=False,
        now=lambda: __import__("datetime").datetime(2026, 3, 1, 12, 0, 0),
    )
    assert lb["generated_at"] == "2026-03-01T12:00:00Z"
    assert lb["config"]["starting_states"] == [[1, 2]]
    assert lb["config"]["tournament"] == "simple"
    assert lb["config"]["repetitions"] == 2
    for block in ("standings", "matches", "player_stats", "totals", "structure"):
        assert block in lb
    match = lb["matches"][0]
    assert set(match) >= {"player_a", "player_b", "phase", "games", "a_wins", "b_wins", "winner"}
    # One board, both first-mover orders, 2 reps -> 4 games in the single match.
    assert match["games"] == 4
    assert lb["totals"]["matches"] == 1 and lb["totals"]["players"] == 2


def test_timing_is_aggregated_and_never_per_move():
    """Timing ships as mean/std/max only — never a per-move array (see D1)."""
    lb = run_tournament(
        [OneStickBot(), AllRowBot()],
        starting_states=[[2, 3]], repetitions=2,
        move_timeout_ms=None, use_subprocess=False,
    )
    match = lb["matches"][0]
    for key in ("a_avg_move_ms", "b_avg_move_ms", "a_std_move_ms",
                "b_std_move_ms", "a_max_move_ms", "b_max_move_ms"):
        assert key in match, key
    assert "moves" not in match
    for row in lb["standings"]:
        assert {"avg_move_ms", "std_move_ms", "max_move_ms"} <= set(row)
    for row in lb["player_stats"]:
        assert {"avg_move_ms", "std_move_ms", "max_move_ms"} <= set(row)
    # Nothing anywhere in the payload carries a per-move log.
    assert "state_before" not in repr(lb)


def test_league_mode_ranks_by_elo():
    lb = run_tournament(
        [OneStickBot(), CheatBot()],
        mode="league",
        starting_states=[[1, 2, 3]],
        repetitions=1,
        move_timeout_ms=None,
        use_subprocess=False,
    )
    assert lb["config"]["tournament"] == "league"
    assert lb["config"]["elo"] is True
    assert all("elo" in row for row in lb["standings"])
    # OneStickBot always beats CheatBot (illegal move) -> higher Elo, rank 1.
    top = lb["standings"][0]
    assert top["player"] == "OneStickBot"
    assert top["elo"] > lb["standings"][1]["elo"]


def test_league_without_elo_falls_back_to_points():
    lb = run_tournament(
        [OneStickBot(), CheatBot()],
        mode="league",
        elo=False,
        starting_states=[[1, 2, 3]],
        repetitions=1,
        move_timeout_ms=None,
        use_subprocess=False,
    )
    assert lb["config"]["elo"] is False
    assert all("elo" not in row for row in lb["standings"])


def test_championship_builds_groups_and_bracket():
    # Four kinds x 2 copies = 8 players -> two groups of four, top two advance.
    roster = build_roster([OneStickBot(), AllRowBot(), CheatBot(), CrashBot()])
    lb = run_tournament(
        roster,
        mode="championship",
        starting_states=[[1, 2, 3]],
        repetitions=1,
        move_timeout_ms=None,
        use_subprocess=False,
    )
    structure = lb["structure"]
    assert structure["type"] == "championship"
    assert len(structure["groups"]) == 2
    assert all(len(g["advance"]) == 2 for g in structure["groups"])
    bracket = structure["bracket"]
    assert bracket["rounds"], "expected at least one knockout round"
    assert bracket["champion"] in {p.name for p in roster}


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        run_tournament([OneStickBot()], mode="bogus", use_subprocess=False)
