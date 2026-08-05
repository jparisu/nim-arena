"""Tests for the reusable strategies in :mod:`nimarena.bots`.

These cover the search engine and the endgame oracle directly, rather than through
a tournament, so a regression points at the responsible rule.
"""

from __future__ import annotations

import pytest

from nimarena import game
from nimarena.bots import BasicMinimaxBot, GreedyBot, MinimaxBot, RandomBot, SmartMinimaxBot


class _Meta:
    """Supplies the identity every concrete player must declare."""

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__

    @classmethod
    def get_authors(cls) -> list[str]:
        return ["tests"]

    @classmethod
    def get_description(cls) -> str:
        return f"Test subject {cls.__name__}."

    @classmethod
    def get_icon(cls) -> str:
        return "🧪"


class Plain(_Meta, MinimaxBot):
    pass


class Basic(_Meta, BasicMinimaxBot):
    pass


class Smart(_Meta, SmartMinimaxBot):
    pass


class Greedy(_Meta, GreedyBot):
    pass


class Rand(_Meta, RandomBot):
    pass


# --------------------------------------------------------------------------- #
# The library classes stay abstract until a subclass names them                #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "cls", [MinimaxBot, BasicMinimaxBot, SmartMinimaxBot, GreedyBot, RandomBot]
)
def test_library_bots_cannot_be_entered_without_an_identity(cls):
    with pytest.raises(TypeError):
        cls()


# --------------------------------------------------------------------------- #
# Search engine                                                               #
# --------------------------------------------------------------------------- #

def test_depth_must_be_at_least_one():
    with pytest.raises(ValueError):
        Basic(depth=0)


def test_depth_zero_would_have_searched_the_whole_tree():
    """Regression: the cutoff used `depth == 0` while recursion started at depth-1.

    A depth of 0 therefore never matched and the search ran unbounded. The
    constructor now rejects it, and the cutoff uses `<= 0` as a second guard.
    """
    bot = Basic(depth=1)
    bot.choose_move([3, 5, 7])
    cheap = bot._nodes
    deep = Basic(depth=4)
    deep.choose_move([3, 5, 7])
    assert cheap < deep._nodes


def test_alpha_beta_does_not_change_the_chosen_value():
    """Pruning is a speed optimisation; the root value must be identical."""
    board = [3, 5, 7]
    pruned = Basic(depth=4, seed=0)
    pruned.choose_move(board)

    class NoPrune(Basic):
        def _negamax(self, state, depth, alpha, beta):
            # Same recursion with the cutoff disabled.
            self._nodes += 1
            if game.is_terminal(state):
                return self.LOSS
            known = self.known_value(state)
            if known is not None:
                return known
            if depth <= 0:
                return self.evaluate(state)
            return max(
                -self._negamax(game.apply_move(state, m), depth - 1, -beta, -alpha)
                for m in game.legal_moves(state)
            )

    plain = NoPrune(depth=4, seed=0)
    plain.choose_move(board)
    assert pruned.last_info["score"] == plain.last_info["score"]
    assert pruned._nodes < plain._nodes, "pruning should visit fewer nodes"


def test_search_finds_a_forced_win_in_a_shallow_endgame():
    # [1, 1, 1] is a win for the mover: take one, leaving a lost pair.
    bot = Plain(depth=4, seed=0)
    bot.choose_move([1, 1, 1])
    assert bot.last_info["score"] >= bot.WIN


def test_last_info_is_populated_for_the_web_panel():
    bot = Basic(depth=3, seed=0)
    bot.choose_move([3, 5, 7])
    info = bot.last_info
    assert {"player", "depth", "score", "nodes", "chosen", "note"} <= set(info)
    assert info["depth"] == 3
    assert info["nodes"] > 0


# --------------------------------------------------------------------------- #
# The endgame oracle (hard)                                                   #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ([5], "win"),            # one row: take it all, taking the last stick
        ([0, 4, 0], "win"),      # empty rows are irrelevant
        ([1], "win"),
        ([1, 1], "loss"),        # even number of single sticks
        ([1, 1, 1], "win"),      # odd number of single sticks
        ([1, 1, 1, 1], "loss"),
        ([3, 3], "loss"),        # mirrored
        ([2, 5, 2, 5], "loss"),  # mirrored, interleaved
        ([1, 2, 3], "loss"),     # tabulated
        ([2, 4, 6], "loss"),     # tabulated
        ([1, 4, 5], "loss"),     # tabulated
    ],
)
def test_oracle_verdicts(state, expected):
    bot = Smart(depth=1, seed=0)
    value = bot.known_value(state)
    assert value is not None, f"oracle should recognise {state}"
    assert value == (bot.WIN if expected == "win" else bot.LOSS)


@pytest.mark.parametrize("state", [[3, 5, 7], [7, 9, 11], [2, 5], [3, 5, 6]])
def test_oracle_stays_silent_on_positions_it_does_not_know(state):
    """It must return None rather than guess — the search decides those."""
    assert Smart(depth=1, seed=0).known_value(state) is None


def test_oracle_verdicts_agree_with_nim_theory():
    """Every rule is a special case of 'nim-sum zero means the mover loses'."""
    bot = Smart(depth=1, seed=0)
    for state in ([5], [1], [1, 1], [1, 1, 1], [3, 3], [2, 5, 2, 5],
                  [1, 2, 3], [2, 4, 6], [1, 4, 5], [1, 1, 1, 1]):
        value = bot.known_value(state)
        losing = game.nim_sum(state) == 0
        assert (value == bot.LOSS) is losing, f"{state} disagrees with its nim-sum"


def test_hard_heuristic_stays_inside_the_win_loss_band():
    """A heuristic guess must never outrank a proven result, on any board size."""
    bot = Smart(depth=1, seed=0)
    for state in ([1], [3, 5, 7], [99] * 40, list(range(1, 30))):
        assert bot.LOSS < bot.evaluate(state) < bot.WIN


# --------------------------------------------------------------------------- #
# The simple strategies                                                       #
# --------------------------------------------------------------------------- #

def test_greedy_empties_the_largest_row():
    assert Greedy().choose_move([2, 7, 5]) == (1, 7)
    assert Greedy().choose_move([0, 0, 3]) == (2, 3)


def test_greedy_refuses_a_terminal_board_loudly():
    """It used to return the illegal (0, 0) here, or raise IndexError."""
    with pytest.raises(ValueError):
        Greedy().choose_move([0, 0])


def test_random_only_returns_legal_moves():
    bot = Rand.create(seed=3)
    state = [4, 6]
    for _ in range(30):
        assert game.is_legal(state, bot.choose_move(list(state)))
