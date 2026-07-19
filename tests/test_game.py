"""Tests for the pure game engine."""

from __future__ import annotations

import pytest

from nimarena import game


def test_legal_moves_enumerates_all():
    moves = game.legal_moves([1, 2])
    assert set(moves) == {(0, 1), (1, 1), (1, 2)}


def test_legal_moves_empty_on_terminal():
    assert game.legal_moves([0, 0, 0]) == []


def test_is_legal_bounds():
    state = [3, 0, 4]
    assert game.is_legal(state, (0, 3))
    assert game.is_legal(state, (2, 1))
    assert not game.is_legal(state, (0, 4))  # too many
    assert not game.is_legal(state, (1, 1))  # empty row
    assert not game.is_legal(state, (0, 0))  # must remove >= 1
    assert not game.is_legal(state, (-1, 1))  # bad row
    assert not game.is_legal(state, (5, 1))  # row out of range


def test_is_legal_rejects_malformed_move():
    assert not game.is_legal([3], "nope")
    assert not game.is_legal([3], (0,))
    assert not game.is_legal([3], (0.5, 1))


def test_apply_move_returns_new_state_and_does_not_mutate():
    state = [3, 5, 7]
    new = game.apply_move(state, (1, 2))
    assert new == [3, 3, 7]
    assert state == [3, 5, 7]  # original untouched
    assert new is not state


def test_apply_illegal_move_raises():
    with pytest.raises(ValueError):
        game.apply_move([1, 2], (0, 5))


def test_is_terminal():
    assert game.is_terminal([0, 0, 0])
    assert not game.is_terminal([0, 1, 0])


def test_nim_sum():
    assert game.nim_sum([1, 2, 3]) == 0
    assert game.nim_sum([3, 5, 7]) == 1
    assert game.nim_sum([0, 0, 0]) == 0


def test_total_sticks():
    assert game.total_sticks([3, 5, 7]) == 15
    assert game.total_sticks([0, 0]) == 0


def test_full_game_reaches_terminal():
    state = [1, 2, 3]
    turns = 0
    while not game.is_terminal(state):
        move = game.legal_moves(state)[0]
        state = game.apply_move(state, move)
        turns += 1
        assert turns < 100  # must terminate
    assert game.is_terminal(state)
