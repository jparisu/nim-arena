"""Tests for tournament robustness: timeouts, errors, illegal moves -> forfeits."""

from __future__ import annotations

import time

import pytest

from nimarena.player import Player
from nimarena.tournament import (
    BUILTIN_COPIES,
    CUSTOM_COPIES,
    UNLIMITED,
    Budgets,
    PlayerSpec,
    build_roster,
    copies_for,
    play_match,
    run_tournament,
    validate_starting_states,
)


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

    @classmethod
    def get_icon(cls) -> str:
        return "🧪"


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
    result = play_match(OneStickBot(), OneStickBot(), [1, 1, 1], UNLIMITED)
    assert result.result == "normal"
    assert result.winner in {"OneStickBot"}
    # 3 sticks, one removed per turn -> first player takes the last (odd count).
    assert result.winner == result.player_first


def test_exception_forfeits_and_opponent_wins():
    result = play_match(CrashBot(), OneStickBot(), [3, 5, 7], UNLIMITED)
    assert result.result == "forfeit_error"
    assert result.winner == "OneStickBot"


def test_illegal_move_forfeits():
    result = play_match(CheatBot(), OneStickBot(), [3, 5, 7], UNLIMITED)
    assert result.result == "forfeit_illegal"
    assert result.winner == "OneStickBot"


def test_hung_bot_is_killed_and_forfeits():
    # Uses the process-based hard timeout; the infinite loop must be terminated.
    result = play_match(SlowBot(), OneStickBot(), [3, 5, 7], Budgets(game_ms=300, build_ms=300))
    assert result.result == "forfeit_timeout"
    assert result.winner == "OneStickBot"


def test_run_tournament_survives_a_bad_bot():
    players = [OneStickBot(), CrashBot(), CheatBot()]
    lb = run_tournament(
        players, starting_states=[[1, 2, 3]], repetitions=1,
        budgets=UNLIMITED, use_subprocess=False,
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
    assert [p.name for p in roster] == ["OneStickBot_0", "OneStickBot_1"]


def test_build_roster_takes_a_per_kind_copy_count():
    """The count is per kind, and the caller decides it — see `copies_for`."""
    roster = build_roster(
        [OneStickBot(), AllRowBot()], repetition=1, copies={"AllRowBot": 3}
    )
    assert [p.name for p in roster] == [
        "OneStickBot_0", "AllRowBot_0", "AllRowBot_1", "AllRowBot_2",
    ]


def test_build_roster_ignores_copies_for_kinds_not_entered():
    """A stale name in the mapping is harmless: only the given players are built."""
    roster = build_roster([OneStickBot()], repetition=1, copies={"NotEntered": 5})
    assert [p.name for p in roster] == ["OneStickBot_0"]


def test_build_roster_rejects_a_zero_copy_count():
    with pytest.raises(ValueError):
        build_roster([OneStickBot()], copies={"OneStickBot": 0})


def test_copies_follow_the_manifest_that_admitted_the_player():
    """Roster copies are a tournament decision, taken from a player's origin."""
    from nimarena.manifest import BUILTIN, CUSTOM
    from nimarena.registry import Registry

    reg = Registry()
    reg.register(OneStickBot(), origin=BUILTIN)
    reg.register(AllRowBot(), origin=CUSTOM)
    assert copies_for(reg) == {
        "OneStickBot": BUILTIN_COPIES,
        "AllRowBot": CUSTOM_COPIES,
    }


def test_build_roster_assigns_one_seed_per_copy():
    roster = build_roster([OneStickBot()], repetition=3)
    assert [s.seed for s in roster] == [0, 1, 2]
    assert all(s.cls is OneStickBot for s in roster)


def test_players_are_built_through_the_create_factory():
    """Construction must go through create(), and happen once per game."""
    built_with: list[int] = []

    class Recording(_Stub):
        @classmethod
        def create(cls, seed: int):
            built_with.append(seed)
            return cls()

        def choose_move(self, state):
            for row, sticks in enumerate(state):
                if sticks > 0:
                    return (row, 1)
            raise AssertionError

    # In-process, so the recording list is visible to the test.
    play_match(Recording(), OneStickBot(), [1, 2], UNLIMITED, use_subprocess=False)
    assert built_with == [0], "create() should be called exactly once per game"


def test_build_roster_seeds_random_bots_reproducibly():
    from players.builtin.random import Random

    a, b = build_roster([Random.create(seed=0)])
    assert (a.name, a.seed) == ("random_0", 0)
    assert (b.name, b.seed) == ("random_1", 1)
    # A copy built from its spec behaves exactly like a fresh instance with that seed.
    state = [3, 5, 7]
    assert a.cls.create(seed=a.seed).choose_move(list(state)) == (
        Random.create(seed=0).choose_move(list(state))
    )


def test_build_roster_respects_repetition_count():
    roster = build_roster([OneStickBot()], repetition=3)
    assert [p.name for p in roster] == ["OneStickBot_0", "OneStickBot_1", "OneStickBot_2"]


def test_build_roster_rejects_zero_repetition():
    with pytest.raises(ValueError):
        build_roster([OneStickBot()], repetition=0)


def test_build_roster_lets_a_kind_play_itself():
    # Two seeded copies of the same kind are distinct opponents in the roster.
    roster = build_roster([OneStickBot()])
    lb = run_tournament(
        roster, starting_states=[[1, 2, 3]], repetitions=1,
        budgets=UNLIMITED, use_subprocess=False,
    )
    assert {r["player"] for r in lb["standings"]} == {"OneStickBot_0", "OneStickBot_1"}
    # They played each other (both ways) -> one win and one loss each.
    assert all(r["games"] == 2 for r in lb["standings"])


def test_leaderboard_schema_shape():
    lb = run_tournament(
        [OneStickBot(), CheatBot()],
        starting_states=[[1, 2]],
        repetitions=2,
        budgets=UNLIMITED,
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
        budgets=UNLIMITED, use_subprocess=False,
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
        budgets=UNLIMITED,
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
        budgets=UNLIMITED,
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
        budgets=UNLIMITED,
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


# --------------------------------------------------------------------------- #
# Time budgets, hangs, and attribution (D2)                                    #
# --------------------------------------------------------------------------- #

class SlowBuildBot(_Stub):
    """Hangs while being constructed, not while playing."""

    def __init__(self):
        while True:
            pass

    def choose_move(self, state):
        return (0, 1)


class BadBuildBot(_Stub):
    """Raises while being constructed."""

    def __init__(self):
        raise RuntimeError("bad build")

    def choose_move(self, state):
        return (0, 1)


class GeneratorBot(_Stub):
    """Returns a single-use iterable instead of a tuple."""

    def choose_move(self, state):
        return (x for x in (0, 1))


class RenamerBot(_Stub):
    """Tries to rename itself mid-game."""

    def choose_move(self, state):
        self.name = "somethingElse"
        for row, sticks in enumerate(state):
            if sticks > 0:
                return (row, 1)
        raise AssertionError


def test_a_hung_constructor_is_attributed_to_its_own_player():
    """The build phase must be killable, and blamed on the player being built."""
    # Passed as a spec and never instantiated here: constructing it would hang the
    # test process itself. That is exactly why the child does the building.
    result = play_match(
        PlayerSpec(SlowBuildBot, 0, "SlowBuildBot"), OneStickBot(), [3, 5, 7],
        Budgets(game_ms=200, build_ms=200),
    )
    assert result.result == "forfeit_build_timeout"
    assert result.winner == "OneStickBot"
    assert "SlowBuildBot" in result.detail


def test_a_raising_constructor_forfeits():
    result = play_match(
        PlayerSpec(BadBuildBot, 0, "BadBuildBot"), OneStickBot(), [3, 5, 7], UNLIMITED
    )
    assert result.result == "forfeit_build_error"
    assert result.winner == "OneStickBot"


def test_build_time_is_measured_and_reported():
    result = play_match(OneStickBot(), AllRowBot(), [2, 3], UNLIMITED)
    assert set(result.build_ms) == {"OneStickBot", "AllRowBot"}
    assert all(v >= 0.0 for v in result.build_ms.values())


def test_a_generator_move_forfeits_instead_of_crashing_the_run():
    """Regression: the move used to be evaluated twice, so a generator aborted all.

    is_legal() consumed it, then apply_move() re-checked an exhausted iterable and
    raised straight out of the tournament.
    """
    result = play_match(GeneratorBot(), OneStickBot(), [3, 5, 7], UNLIMITED)
    assert result.result == "forfeit_illegal"
    assert result.winner == "OneStickBot"
    # And it must not abort a whole run either.
    lb = run_tournament(
        [GeneratorBot(), OneStickBot()], starting_states=[[1, 2]], repetitions=1,
        budgets=UNLIMITED, use_subprocess=False,
    )
    assert lb["totals"]["games"] == 2


def test_a_player_renaming_itself_cannot_corrupt_the_standings():
    """Regression: names came from the player, so a rename raised KeyError."""
    lb = run_tournament(
        [RenamerBot(), OneStickBot()], starting_states=[[1, 2, 3]], repetitions=1,
        budgets=UNLIMITED, use_subprocess=False,
    )
    assert {r["player"] for r in lb["standings"]} == {"RenamerBot", "OneStickBot"}


def test_game_budget_is_cumulative_across_moves_not_per_move():
    """A chess clock: many cheap moves must not each get the full budget."""

    class Dawdler(_Stub):
        def choose_move(self, state):
            time.sleep(0.05)
            for row, sticks in enumerate(state):
                if sticks > 0:
                    return (row, 1)
            raise AssertionError

    # Each move is well inside 120 ms, but four of them are not.
    result = play_match(
        Dawdler(), OneStickBot(), [6], Budgets(game_ms=120, build_ms=2000),
        use_subprocess=False,
    )
    assert result.result == "forfeit_timeout"
    assert result.winner == "OneStickBot"
    assert "game budget" in result.detail


def test_spent_time_survives_a_kill():
    """The orchestrator must recover per-player time even when the child is killed."""
    result = play_match(
        SlowBot(), OneStickBot(), [3, 5, 7], Budgets(game_ms=200, build_ms=200)
    )
    assert result.result == "forfeit_timeout"
    assert set(result.spent_ms) == {"SlowBot", "OneStickBot"}
    assert set(result.build_ms) == {"SlowBot", "OneStickBot"}


def test_deadline_is_twice_the_budgets_plus_grace():
    b = Budgets(game_ms=1000, build_ms=500, grace_ms=250)
    assert b.deadline_ms == 2 * (1000 + 500) + 250
    assert UNLIMITED.deadline_ms is None


def test_player_state_survives_across_moves_in_one_game():
    """Fork-per-game, not per move: a counter must advance through the game."""

    class Counter(_Stub):
        def __init__(self):
            self.seen = 0

        def choose_move(self, state):
            self.seen += 1
            if self.seen > 1 and not self._ok:
                raise AssertionError("state was discarded between moves")
            self._ok = True
            for row, sticks in enumerate(state):
                if sticks > 0:
                    return (row, 1)
            raise AssertionError

        _ok = False

    result = play_match(Counter(), Counter(), [4], Budgets())
    assert result.result == "normal"


def test_repeated_games_differ_when_the_player_is_stochastic():
    """The whole point of D2: repetitions must not be byte-identical."""
    from players.builtin.random import Random

    from nimarena.tournament import play_matchup

    mu = play_matchup(
        PlayerSpec(Random, 0, "random_0"),
        PlayerSpec(Random, 1, "random_1"),
        [[7, 9, 11]], repetitions=6, budgets=Budgets(),
    )
    signatures = {
        tuple(tuple(m.move) for m in g.moves if m.move is not None) for g in mu.games
    }
    assert len(signatures) > 2, f"only {len(signatures)} distinct games out of {len(mu.games)}"


# --------------------------------------------------------------------------- #
# Input validation                                                             #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "boards",
    [[], [[]], [[0, 0, 0]], [[-1, 3]], [[1, "x"]]],
)
def test_unplayable_boards_are_rejected(boards):
    with pytest.raises(ValueError):
        validate_starting_states(boards)


def test_valid_boards_are_returned_as_clean_lists():
    assert validate_starting_states([[3, 5, 7], (1, 0, 2)]) == [[3, 5, 7], [1, 0, 2]]


def test_empty_roster_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        run_tournament([], use_subprocess=False)


def test_duplicate_roster_names_are_rejected():
    """Two same-named entries would collapse into one standings row."""
    with pytest.raises(ValueError, match="unique"):
        run_tournament(
            [OneStickBot(), OneStickBot()], starting_states=[[1, 2]],
            repetitions=1, budgets=UNLIMITED, use_subprocess=False,
        )


def test_zero_repetitions_is_rejected():
    with pytest.raises(ValueError):
        run_tournament([OneStickBot(), AllRowBot()], repetitions=0, use_subprocess=False)


@pytest.mark.parametrize(("group_size", "advance"), [(0, 2), (4, 0)])
def test_championship_rejects_degenerate_group_settings(group_size, advance):
    """group_size=0 used to raise ZeroDivisionError."""
    with pytest.raises(ValueError):
        run_tournament(
            build_roster([OneStickBot(), AllRowBot()], repetition=1), mode="championship",
            starting_states=[[1, 2]], repetitions=1, budgets=UNLIMITED,
            use_subprocess=False, group_size=group_size, advance_per_group=advance,
        )


def test_a_whole_run_is_reproducible_despite_varying_games():
    """Games within a match differ, yet the run repeats byte-for-byte."""
    from players.builtin.random import Random

    from nimarena.tournament import play_matchup

    def signatures():
        mu = play_matchup(
            PlayerSpec(Random, 0, "random_0"),
            PlayerSpec(Random, 1, "random_1"),
            [[7, 9, 11]], repetitions=4, budgets=UNLIMITED, use_subprocess=False,
        )
        return [tuple(tuple(m.move) for m in g.moves if m.move) for g in mu.games]

    first, second = signatures(), signatures()
    assert first == second, "the same match must replay identically"
    assert len(set(first)) > 2, "but its games must not be identical to each other"
