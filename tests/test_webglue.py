"""Tests for the browser bridge — including the Tournament page's entrants.

``web/webglue.py`` is shipped code: it is what the page calls into for every rule
query and every AI move. Its forfeit handling matters especially, because the
browser enforces no timeout and a page must never be taken down by one bad player.
"""

from __future__ import annotations

import json

import pytest
import webglue

from nimarena.player import Player

#: The reference players that ship with the repository. ``players.yaml`` is an
#: open admission list, so the page may legitimately offer more than these — a
#: test may check that they are *present*, never that they are all there is.
REFERENCE_PLAYERS = {"random", "easy", "medium", "hard"}


@pytest.fixture(autouse=True)
def loaded():
    """Load the real manifest once per test and start from a clean entrant table."""
    webglue.init(".")
    webglue.reset_entrants()
    yield
    webglue.reset_entrants()


class Boom(Player):
    """Raises instead of moving."""

    @classmethod
    def get_name(cls):
        return "boom"

    @classmethod
    def get_authors(cls):
        return ["tests"]

    @classmethod
    def get_description(cls):
        return "Always raises."

    @classmethod
    def get_icon(cls):
        return "💥"

    def choose_move(self, state):
        raise RuntimeError("kaboom")


class Cheat(Boom):
    """Returns a move that is never legal."""

    @classmethod
    def get_name(cls):
        return "cheat"

    def choose_move(self, state):
        return (0, 999)


# --------------------------------------------------------------------------- #
# Rules and identity                                                          #
# --------------------------------------------------------------------------- #

def test_players_json_carries_identity():
    entries = json.loads(webglue.players_json())
    assert REFERENCE_PLAYERS <= {e["name"] for e in entries}
    for e in entries:
        assert e["icon"].strip() and e["authors"] and e["description"].strip()


def test_rules_come_from_the_engine():
    assert json.loads(webglue.legal_moves("[1,2]")) == [[0, 1], [1, 1], [1, 2]]
    assert json.loads(webglue.apply_move("[1,2]", "[1,2]")) == [1, 0]
    assert webglue.is_terminal("[0,0]") is True
    assert webglue.nim_sum("[1,2,3]") == 0
    assert webglue.total_sticks("[1,2,3]") == 6


def test_ask_move_refuses_a_terminal_board():
    with pytest.raises(ValueError, match="terminal"):
        webglue.ask_move("hard", "[0,0]")


def test_perfect_analysis_is_computed_not_delegated():
    """X-ray/hint must work even though no nim-sum player ships."""
    an = json.loads(webglue.perfect_analysis("[3,5,7]"))
    assert an["winning"] is True and an["nim_sum"] == 1
    assert an["move"] is not None
    row, count = an["move"]
    after = json.loads(webglue.apply_move("[3,5,7]", json.dumps([row, count])))
    assert webglue.nim_sum(json.dumps(after)) == 0


# --------------------------------------------------------------------------- #
# Tournament entrants                                                         #
# --------------------------------------------------------------------------- #

def test_the_same_kind_can_enter_twice_independently():
    webglue.create_entrant("a", "random", 1)
    webglue.create_entrant("b", "random", 2)
    assert webglue._ENTRANTS["a"] is not webglue._ENTRANTS["b"]


def test_an_unknown_entrant_says_what_to_do():
    with pytest.raises(KeyError, match="create_entrant"):
        webglue.entrant_move("nobody", "[1,3]")


def test_reset_entrants_clears_the_table():
    webglue.create_entrant("a", "hard", 0)
    webglue.reset_entrants()
    assert not webglue._ENTRANTS


def test_play_auto_returns_a_complete_game():
    webglue.create_entrant("a", "hard", 0)
    webglue.create_entrant("b", "easy", 1)
    res = json.loads(webglue.play_auto("a", "b", "[1,3,5,7]"))
    assert res["result"] == "normal"
    assert res["winner_seat"] in (0, 1)
    # Replaying the moves must empty the board, and the last mover must have won.
    state = [1, 3, 5, 7]
    for row, count in res["moves"]:
        state = json.loads(webglue.apply_move(json.dumps(state), json.dumps([row, count])))
    assert state == [0, 0, 0, 0]
    assert res["winner_seat"] == (len(res["moves"]) - 1) % 2


def test_play_auto_is_reproducible_for_a_seed():
    def run():
        webglue.reset_entrants()
        webglue.create_entrant("a", "random", 7)
        webglue.create_entrant("b", "random", 8)
        return json.loads(webglue.play_auto("a", "b", "[1,3,5,7]"))["moves"]

    assert run() == run()


@pytest.mark.parametrize(
    ("cls", "expected"),
    [(Boom, "forfeit_error"), (Cheat, "forfeit_illegal")],
)
def test_a_misbehaving_entrant_forfeits_instead_of_breaking_the_page(cls, expected):
    webglue._ENTRANTS["bad"] = cls.create(seed=0)
    webglue.create_entrant("good", "hard", 0)
    res = json.loads(webglue.play_auto("bad", "good", "[1,3,5,7]"))
    assert res["result"] == expected
    assert res["winner_seat"] == 1, "the opponent wins"
    assert res["detail"]


def test_play_auto_caps_a_runaway_game():
    """A bot that never reduces the board must not loop forever in the browser."""

    class Stubborn(Boom):
        @classmethod
        def get_name(cls):
            return "stubborn"

        def choose_move(self, state):
            return (0, 0)  # illegal: removes nothing

    webglue._ENTRANTS["s"] = Stubborn.create(seed=0)
    webglue.create_entrant("good", "hard", 0)
    res = json.loads(webglue.play_auto("s", "good", "[1,3,5,7]", 10))
    assert res["result"] == "forfeit_illegal"
