"""Tournament runner: formats, time budgets, forfeits, results.

**Robustness (not security) is the goal.** Even accepted, well-meaning bots can
hang, crash, or return an illegal move on some edge case. This runner survives all
of it and never aborts:

* a player that **exceeds a time budget** -> forfeits that game;
* a player that **raises an exception** -> forfeits that game;
* a player that **returns an illegal move** -> forfeits that game;
* a player that **hangs forever** -> is killed, and forfeits that game;
* a player that **fails or hangs while being built** -> forfeits that game.

In every case the reason is recorded in the results and the run continues.

## Formats

Three tournament formats are supported (``--tournament``):

* ``simple`` — every pair plays one match; players are ranked by points (wins).
* ``league`` — every pair plays one match; players are ranked by an
  [Elo rating][nimarena.elo] (per game) when enabled, else by points.
* ``championship`` — a group phase (round-robin in groups of four, top two
  advance) followed by a seeded single-elimination bracket.

A **match** between two players is played identically in every format: for each
starting board, and for each player going first once, ``repetitions`` games are
played. So a match spans ``len(boards) * 2 * repetitions`` games.

## Time budgets

Budgets are **per player, per game** — a chess clock, not a per-move limit. A bot
may spend most of its budget on one hard move; that is intended. Two independent
budgets, in [`Budgets`][nimarena.tournament.Budgets]:

* ``build_ms`` covers [`create`][nimarena.player.Player.create] for one player;
* ``game_ms`` covers all of that player's ``choose_move`` calls in one game.

Construction is budgeted separately so that an expensive precomputation cannot be
smuggled past the clock by doing it in ``__init__``.

## Why one process per game

A game runs in **one forked child process**, so a truly hung bot can be killed and
the tournament can move on. (Threads cannot be force-killed in Python, so they
cannot honour that guarantee.)

One fork per *game* rather than per *move* matters for correctness, not just speed:
a child's memory is discarded when it exits, so forking per move would throw away
everything a player learned — its RNG position, any cache, any memo table. Games
would be byte-identical repeats and memoization would be impossible. See
``devs/DESIGN_DECISIONS.md`` (D2).

The child owns the whole game, so the parent never holds a player instance — only a
[`PlayerSpec`][nimarena.tournament.PlayerSpec]. That is also what makes a hanging
constructor survivable.

## Attributing a hang

The child adds a move's time to the clock only *after* ``choose_move`` returns, so a
bot that hangs never records its own time, and a queue's buffered writes can be lost
when the child is killed. The child therefore publishes its progress into **shared
memory** (:class:`multiprocessing.Array`), which is mapped into both processes and
stays readable by the parent after the child is killed. It records which phase it is
in and which player is executing *before* entering any player code, so the parent
can always name the culprit exactly rather than guessing.

If the platform cannot ``fork``, the runner falls back to running in-process with
soft budgets (over-budget games still forfeit, but a genuine infinite loop cannot be
interrupted). The web page runs neither path — it calls ``choose_move`` directly and
enforces no budget, by design.
"""

from __future__ import annotations

import multiprocessing as mp
import queue as queue_mod
import statistics
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import game
from .elo import DEFAULT_INITIAL_RATING, updated_ratings
from .game import Move, State
from .player import Player

#: Boards every match is played on, unless the caller overrides them.
#:
#: Three deliberately different shapes: the classic 3-row board, a 5-row
#: staircase, and a wide 6-row board of 39 sticks. The last one matters because a
#: depth-limited search cannot reach the endgame from its opening, which is what
#: keeps the top of the ranking discriminating instead of every strong player
#: tying. Every match plays ``repetitions`` games on each board, from each side.
DEFAULT_STARTING_STATES: list[State] = [
    [3, 5, 7],
    [1, 2, 3, 4, 5],
    [4, 5, 6, 7, 8, 9],
]
#: Per-player, per-game thinking budget in milliseconds.
DEFAULT_GAME_BUDGET_MS = 2000
#: Per-player budget for :meth:`~nimarena.player.Player.create`, in milliseconds.
DEFAULT_BUILD_BUDGET_MS = 2000
#: Slack added to the wall-clock deadline to cover fork, imports and teardown.
DEFAULT_GRACE_MS = 500
#: Per-player budget in seconds, used as the CLI default for both budgets.
DEFAULT_TIME_LIMIT_S = 2.0
#: Copies of each player kind entered into the roster (see :func:`build_roster`).
DEFAULT_PLAYER_REPETITION = 2
#: Games played per (board, first-mover) pairing within a single match.
DEFAULT_REPETITIONS = 10
#: Players per group in the championship group phase.
DEFAULT_GROUP_SIZE = 4
#: Players that advance from each championship group to the knockout bracket.
DEFAULT_ADVANCE_PER_GROUP = 2
#: The tournament formats understood by :func:`run_tournament`.
TOURNAMENT_MODES = ("simple", "league", "championship")

#: Milliseconds per second, used to convert measured/allotted times.
_MS_PER_SECOND = 1000.0
#: Decimal places used when rounding reported times and rates.
_ROUND_DIGITS = 3
#: How long the parent waits to collect a finished child's result.
_COLLECT_GRACE_S = 5.0


# --------------------------------------------------------------------------- #
# Budgets and player specifications                                            #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Budgets:
    """The time a player is allowed, per game.

    Attributes:
        game_ms: total ``choose_move`` time allowed per player per game, in
            milliseconds. ``None`` disables the thinking budget.
        build_ms: time allowed to build one player, in milliseconds. ``None``
            disables the construction budget.
        grace_ms: slack added to the wall-clock deadline, covering fork, imports
            and process teardown. Without it a legitimately slow game gets killed.
    """

    game_ms: int | None = DEFAULT_GAME_BUDGET_MS
    build_ms: int | None = DEFAULT_BUILD_BUDGET_MS
    grace_ms: int = DEFAULT_GRACE_MS

    @property
    def deadline_ms(self) -> int | None:
        """Wall-clock limit for a whole game, or ``None`` if nothing is budgeted.

        Twice the per-player budgets, because *both* players may legitimately
        consume theirs in full, plus :attr:`grace_ms`.
        """
        if self.game_ms is None and self.build_ms is None:
            return None
        return 2 * ((self.game_ms or 0) + (self.build_ms or 0)) + self.grace_ms


#: Budgets that enforce nothing — used by tests and by ``--no-time-limit``.
UNLIMITED = Budgets(game_ms=None, build_ms=None)


@dataclass(frozen=True)
class PlayerSpec:
    """How to build one competitor, without building it.

    The parent orchestrates with specifications rather than instances: the child
    process is what calls :meth:`~nimarena.player.Player.create`, so a constructor
    that hangs or raises is contained the same way a bad move is. It also means a
    player cannot rename itself out of the standings, and a configured player is
    never silently rebuilt with default arguments.

    Attributes:
        cls: the :class:`~nimarena.player.Player` subclass to build.
        seed: seed handed to :meth:`~nimarena.player.Player.create`.
        name: display name in the results (e.g. ``"hard#1"``).
    """

    cls: type[Player]
    seed: int
    name: str


#: Multiplier used to fold a roster seed and a game index into one game seed. A
#: prime well above any plausible game count, so distinct (roster seed, game index)
#: pairs never collide.
_SEED_STRIDE = 1_000_003


def _seed_for_game(spec: PlayerSpec, game_index: int) -> PlayerSpec:
    """Return ``spec`` re-seeded for game number ``game_index`` of a match.

    Forking per game lets a player's state survive its own game, but every game of
    a match would still be built with the *same* seed — so a stochastic player
    would replay one identical game ``repetitions`` times. Deriving the seed from
    the roster seed *and* the game index is what actually makes repeated games
    differ, while keeping the whole run reproducible: the same match in the same
    order always produces the same seeds.

    The display name is preserved, so the standings are unaffected.
    """
    return PlayerSpec(
        cls=spec.cls,
        seed=spec.seed * _SEED_STRIDE + game_index,
        name=spec.name,
    )


def _as_spec(entry: Player | PlayerSpec, seed: int = 0) -> PlayerSpec:
    """Coerce a player *or* an already-built spec into a :class:`PlayerSpec`.

    Accepting instances keeps ``run_tournament([MyBot(), Other()])`` working for
    tests and quick scripts; the instance is used only for its class and name.
    """
    if isinstance(entry, PlayerSpec):
        return entry
    return PlayerSpec(cls=type(entry), seed=seed, name=entry.name)


# --------------------------------------------------------------------------- #
# Shared progress, written by the child and readable after it is killed        #
# --------------------------------------------------------------------------- #

# Cumulative milliseconds, indexed by player position within the game.
_ACCT_MOVE = (0, 1)
_ACCT_BUILD = (2, 3)
_ACCT_SLOTS = 4

# Progress flags.
_ST_PHASE, _ST_ACTIVE, _ST_MOVES = 0, 1, 2
_ST_SLOTS = 3

_PHASE_BUILD, _PHASE_PLAY, _PHASE_DONE = 0, 1, 2


def _fork_context() -> mp.context.BaseContext | None:
    """Return a ``fork`` context, or ``None`` where forking is unavailable.

    Only ``fork`` is used. Under ``spawn`` the child would have to unpickle the
    player class, which lives in a synthetic module created by the manifest loader
    and does not exist in a fresh interpreter — so every game would forfeit and the
    blame would land on the bot. Falling back to an in-process soft budget is
    honest; silently blaming players is not.
    """
    try:
        return mp.get_context("fork")
    except ValueError:  # pragma: no cover - non-fork platforms
        return None


# --------------------------------------------------------------------------- #
# Data structures                                                             #
# --------------------------------------------------------------------------- #

@dataclass
class MoveRecord:
    """One move played in a game.

    Retained only so the runner can aggregate timing; it is never serialized. See
    ``devs/DESIGN_DECISIONS.md`` (D1).

    Attributes:
        player: name of the player that moved.
        state_before: board seen by the player before moving.
        move: the ``(row, count)`` played, or ``None`` if the player forfeited
            instead of moving.
        elapsed_ms: wall-clock time the player took, in milliseconds.
    """

    player: str
    state_before: State
    move: Move | None
    elapsed_ms: float


#: Every value :attr:`MatchResult.result` may take.
RESULTS = (
    "normal",
    "forfeit_timeout",
    "forfeit_illegal",
    "forfeit_error",
    "forfeit_build_timeout",
    "forfeit_build_error",
)


@dataclass
class MatchResult:
    """Outcome of a single game between two players.

    Attributes:
        player_first: name of the player that moved first.
        player_second: name of the player that moved second.
        start_state: board the game started from.
        winner: name of the winning player.
        result: how the game ended; one of :data:`RESULTS`.
        moves: the moves played, in order.
        detail: human-readable explanation, populated on forfeits.
        spent_ms: total thinking time per player name. Recoverable even when a
            hang lost the per-move detail, which is why it is separate from
            ``moves``.
        build_ms: time spent building each player, by name.
    """

    player_first: str
    player_second: str
    start_state: State
    winner: str
    result: str
    moves: list[MoveRecord] = field(default_factory=list)
    detail: str = ""
    spent_ms: dict[str, float] = field(default_factory=dict)
    build_ms: dict[str, float] = field(default_factory=dict)

    @property
    def loser(self) -> str:
        """Name of the losing player."""
        return self.player_second if self.winner == self.player_first else self.player_first


@dataclass
class Matchup:
    """A whole match between two players: its many games plus quick aggregates.

    Attributes:
        player_a: name of the first player of the pairing.
        player_b: name of the second player of the pairing.
        games: every game played in the match, in play order.
        phase: label describing where the match sits in the tournament (e.g.
            ``"round-robin"``, ``"Group A"``, ``"Semifinals"``).
    """

    player_a: str
    player_b: str
    games: list[MatchResult]
    phase: str = "round-robin"

    @property
    def a_wins(self) -> int:
        """Games won by :attr:`player_a`."""
        return sum(1 for g in self.games if g.winner == self.player_a)

    @property
    def b_wins(self) -> int:
        """Games won by :attr:`player_b`."""
        return sum(1 for g in self.games if g.winner == self.player_b)

    @property
    def forfeits(self) -> int:
        """Games that ended in a forfeit (by either player)."""
        return sum(1 for g in self.games if g.result != "normal")

    @property
    def winner(self) -> str:
        """Name of the player who won more games, or ``""`` if the match is tied."""
        if self.a_wins > self.b_wins:
            return self.player_a
        if self.b_wins > self.a_wins:
            return self.player_b
        return ""

    def _move_times(self, name: str) -> list[float]:
        """Return every completed-move time (ms) played by ``name`` in the match."""
        return [
            rec.elapsed_ms
            for g in self.games
            for rec in g.moves
            if rec.player == name and rec.move is not None
        ]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable, aggregated summary of the match.

        Timing is reported as **aggregates only** — mean, standard deviation and
        maximum per player. There is deliberately no per-move array: see
        ``devs/DESIGN_DECISIONS.md`` (D1).
        """
        a_times = self._move_times(self.player_a)
        b_times = self._move_times(self.player_b)
        return {
            "player_a": self.player_a,
            "player_b": self.player_b,
            "phase": self.phase,
            "games": len(self.games),
            "a_wins": self.a_wins,
            "b_wins": self.b_wins,
            "winner": self.winner,
            "forfeits": self.forfeits,
            "a_avg_move_ms": round(_mean(a_times), _ROUND_DIGITS),
            "b_avg_move_ms": round(_mean(b_times), _ROUND_DIGITS),
            "a_std_move_ms": round(_stdev(a_times), _ROUND_DIGITS),
            "b_std_move_ms": round(_stdev(b_times), _ROUND_DIGITS),
            "a_max_move_ms": round(max(a_times, default=0.0), _ROUND_DIGITS),
            "b_max_move_ms": round(max(b_times, default=0.0), _ROUND_DIGITS),
        }


def _mean(values: list[float]) -> float:
    """Return the arithmetic mean of ``values`` (0.0 for an empty list)."""
    return sum(values) / len(values) if values else 0.0


def _stdev(values: list[float]) -> float:
    """Return the population standard deviation of ``values``.

    Population (not sample) deviation, because the list *is* the whole population
    of moves played — nothing is being estimated. Returns 0.0 for fewer than two
    values, where spread is undefined rather than infinite.
    """
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


# --------------------------------------------------------------------------- #
# Playing one game                                                             #
# --------------------------------------------------------------------------- #

def _normalize_move(raw: object) -> Move | None:
    """Coerce whatever a player returned into a ``(row, count)`` tuple, once.

    Doing this **exactly once**, before any validation, is load-bearing. Legality
    used to be checked with ``is_legal(state, move)`` and then re-checked inside
    ``apply_move(state, move)``, so a player returning a generator passed the first
    check — which consumed it — and then crashed the entire tournament in the
    second. Unpacking here consumes any one-shot iterable a single time.

    Returns:
        The move, or ``None`` if it is not a pair of integers.
    """
    try:
        row, count = raw  # type: ignore[misc]
    except (TypeError, ValueError):
        return None
    if isinstance(row, bool) or isinstance(count, bool):
        return None
    if not isinstance(row, int) or not isinstance(count, int):
        return None
    return (row, count)


def _forfeit(
    specs: Sequence[PlayerSpec],
    start_state: State,
    culprit: int,
    result: str,
    detail: str,
    moves: list[MoveRecord],
    acct: Sequence[float],
) -> MatchResult:
    """Build the :class:`MatchResult` for a game lost by player ``culprit``."""
    return MatchResult(
        player_first=specs[0].name,
        player_second=specs[1].name,
        start_state=list(start_state),
        winner=specs[1 - culprit].name,
        result=result,
        moves=moves,
        detail=detail,
        spent_ms={s.name: float(acct[_ACCT_MOVE[i]]) for i, s in enumerate(specs)},
        build_ms={s.name: float(acct[_ACCT_BUILD[i]]) for i, s in enumerate(specs)},
    )


def _play_game(
    acct: Sequence[float],
    st: Sequence[int],
    specs: Sequence[PlayerSpec],
    start_state: State,
    budgets: Budgets,
) -> MatchResult:
    """Build both players and play one game to completion.

    This is the single game loop: the forked child runs it, and so does the
    in-process fallback. ``acct`` and ``st`` are the shared-progress arrays — plain
    lists in-process, :class:`multiprocessing.Array` in a child — written *before*
    entering player code so the parent can attribute a hang.

    Never raises on player misbehaviour: anything a player does becomes a forfeit.
    """
    players: list[Player] = []
    st[_ST_PHASE] = _PHASE_BUILD

    for i, spec in enumerate(specs):
        st[_ST_ACTIVE] = i
        t0 = time.perf_counter()
        try:
            player = spec.cls.create(seed=spec.seed)
        except BaseException as exc:  # noqa: BLE001 - any failure becomes a forfeit
            acct[_ACCT_BUILD[i]] = (time.perf_counter() - t0) * _MS_PER_SECOND
            return _forfeit(
                specs, start_state, i, "forfeit_build_error",
                f"{spec.name} raised while being created: {exc!r}", [], acct,
            )
        elapsed = (time.perf_counter() - t0) * _MS_PER_SECOND
        acct[_ACCT_BUILD[i]] = elapsed
        if budgets.build_ms is not None and elapsed > budgets.build_ms:
            return _forfeit(
                specs, start_state, i, "forfeit_build_timeout",
                f"{spec.name} took {elapsed:.0f} ms to build, over {budgets.build_ms} ms",
                [], acct,
            )
        # The spec owns the display name; a player may not rename itself into (or
        # out of) the standings.
        player.name = spec.name
        players.append(player)

    st[_ST_PHASE] = _PHASE_PLAY
    state: State = list(start_state)
    moves: list[MoveRecord] = []
    turn = 0

    while not game.is_terminal(state):
        st[_ST_ACTIVE] = turn
        name = specs[turn].name
        t0 = time.perf_counter()
        try:
            # A fresh copy every move: the player now lives for the whole game, so
            # mutating the board in place would corrupt the game rather than a
            # throwaway.
            raw = players[turn].choose_move(list(state))
        except BaseException as exc:  # noqa: BLE001 - any failure becomes a forfeit
            elapsed = (time.perf_counter() - t0) * _MS_PER_SECOND
            acct[_ACCT_MOVE[turn]] += elapsed
            moves.append(MoveRecord(name, list(state), None, elapsed))
            return _forfeit(
                specs, start_state, turn, "forfeit_error",
                f"{name} raised: {exc!r}", moves, acct,
            )

        elapsed = (time.perf_counter() - t0) * _MS_PER_SECOND
        acct[_ACCT_MOVE[turn]] += elapsed
        st[_ST_MOVES] += 1
        move = _normalize_move(raw)

        # The clock is checked first: it is the harder constraint, and it is the
        # one thing we measured rather than inspected.
        if budgets.game_ms is not None and acct[_ACCT_MOVE[turn]] > budgets.game_ms:
            moves.append(MoveRecord(name, list(state), None, elapsed))
            return _forfeit(
                specs, start_state, turn, "forfeit_timeout",
                f"{name} used {acct[_ACCT_MOVE[turn]]:.0f} ms of its "
                f"{budgets.game_ms} ms game budget",
                moves, acct,
            )

        if move is None or not game.is_legal(state, move):
            moves.append(MoveRecord(name, list(state), None, elapsed))
            return _forfeit(
                specs, start_state, turn, "forfeit_illegal",
                f"{name} returned illegal move {raw!r} for {state}", moves, acct,
            )

        moves.append(MoveRecord(name, list(state), move, elapsed))
        state = game.apply_move(state, move)
        turn = 1 - turn

    st[_ST_PHASE] = _PHASE_DONE
    # The player who made the last move (now `1 - turn`) took the last stick.
    return MatchResult(
        player_first=specs[0].name,
        player_second=specs[1].name,
        start_state=list(start_state),
        winner=specs[1 - turn].name,
        result="normal",
        moves=moves,
        spent_ms={s.name: float(acct[_ACCT_MOVE[i]]) for i, s in enumerate(specs)},
        build_ms={s.name: float(acct[_ACCT_BUILD[i]]) for i, s in enumerate(specs)},
    )


def _game_worker(  # pragma: no cover - runs only in a child process
    result_queue: mp.Queue,
    acct: Sequence[float],
    st: Sequence[int],
    specs: Sequence[PlayerSpec],
    start_state: State,
    budgets: Budgets,
) -> None:
    """Child entry point: play one game and hand the result back."""
    try:
        result_queue.put(_play_game(acct, st, specs, start_state, budgets))
    except BaseException as exc:  # noqa: BLE001 - never die silently
        result_queue.put(("__crashed__", repr(exc)))


def _verdict_after_kill(
    specs: Sequence[PlayerSpec],
    start_state: State,
    acct: Sequence[float],
    st: Sequence[int],
    budgets: Budgets,
    detail_suffix: str = "",
) -> MatchResult:
    """Decide a game whose child had to be killed, from shared progress alone.

    The child records its phase and the active player *before* calling into player
    code, so the culprit is a fact rather than a guess:

    * still building -> the active player's constructor hung;
    * playing, and someone is over the game budget -> that player (the larger
      overage wins, for the rare case where both are over);
    * playing, nobody over budget -> the active player stopped responding
      mid-move. Its own time was never added to the clock, which is exactly why
      the fallback has to be the *active* player rather than the clocks.
    """
    phase = st[_ST_PHASE]
    active = st[_ST_ACTIVE] if st[_ST_ACTIVE] in (0, 1) else 0

    if phase == _PHASE_BUILD:
        return _forfeit(
            specs, start_state, active, "forfeit_build_timeout",
            f"{specs[active].name} did not finish being created{detail_suffix}",
            [], acct,
        )

    if budgets.game_ms is not None:
        over = [i for i in (0, 1) if acct[_ACCT_MOVE[i]] > budgets.game_ms]
        if over:
            culprit = max(over, key=lambda i: acct[_ACCT_MOVE[i]])
            return _forfeit(
                specs, start_state, culprit, "forfeit_timeout",
                f"{specs[culprit].name} used "
                f"{acct[_ACCT_MOVE[culprit]]:.0f} ms of its {budgets.game_ms} ms "
                f"game budget{detail_suffix}",
                [], acct,
            )

    return _forfeit(
        specs, start_state, active, "forfeit_timeout",
        f"{specs[active].name} stopped responding after {st[_ST_MOVES]} "
        f"move(s) in the game{detail_suffix}",
        [], acct,
    )


def play_match(
    first: Player | PlayerSpec,
    second: Player | PlayerSpec,
    start_state: State,
    budgets: Budgets | None = None,
    *,
    use_subprocess: bool = True,
) -> MatchResult:
    """Play one game; ``first`` moves first. Never raises on bot misbehavior.

    The player who removes the last stick wins (normal play). Exceeding a budget,
    raising, hanging, or returning an illegal move all make the offending player
    forfeit, and the opponent is declared the winner.

    Args:
        first: the player to move first (an instance or a :class:`PlayerSpec`).
        second: the other player.
        start_state: the board to play from.
        budgets: time budgets; defaults to :class:`Budgets`. Pass
            :data:`UNLIMITED` to enforce nothing.
        use_subprocess: play the game in a forked child so a hung player can be
            killed. ``False`` runs in-process with soft budgets — faster, but an
            infinite loop cannot be interrupted.

    Returns:
        The completed :class:`MatchResult`.
    """
    specs = (_as_spec(first), _as_spec(second))
    budgets = Budgets() if budgets is None else budgets
    deadline_ms = budgets.deadline_ms
    ctx = _fork_context() if use_subprocess else None

    if ctx is None or deadline_ms is None:
        # Soft path: nothing to kill, or nothing to kill it with.
        return _play_game([0.0] * _ACCT_SLOTS, [0] * _ST_SLOTS, specs, start_state, budgets)

    acct = ctx.Array("d", [0.0] * _ACCT_SLOTS, lock=False)
    st = ctx.Array("i", [0] * _ST_SLOTS, lock=False)
    result_queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(
        target=_game_worker,
        args=(result_queue, acct, st, specs, start_state, budgets),
        daemon=True,
    )
    proc.start()
    try:
        # Read *before* joining. A child cannot exit until its queued payload has
        # been drained, so joining first can deadlock on a large result.
        payload = result_queue.get(timeout=deadline_ms / _MS_PER_SECOND)
    except queue_mod.Empty:
        payload = None

    if payload is None:
        proc.terminate()
        proc.join()
        return _verdict_after_kill(specs, start_state, acct, st, budgets)

    proc.join(timeout=_COLLECT_GRACE_S)
    if proc.is_alive():  # pragma: no cover - defensive
        proc.terminate()
        proc.join()

    if isinstance(payload, tuple):  # pragma: no cover - the worker itself failed
        return _verdict_after_kill(
            specs, start_state, acct, st, budgets,
            detail_suffix=f" (runner error: {payload[1]})",
        )
    return payload


def play_matchup(
    a: Player | PlayerSpec,
    b: Player | PlayerSpec,
    starting_states: list[State],
    repetitions: int,
    budgets: Budgets | None = None,
    *,
    use_subprocess: bool = True,
    phase: str = "round-robin",
) -> Matchup:
    """Play a full match between ``a`` and ``b`` and return its :class:`Matchup`.

    The match plays, for every board in ``starting_states`` and for each player
    going first once, ``repetitions`` games — so ``len(starting_states) * 2 *
    repetitions`` games in total. Alternating the first mover matters because
    NIM's first player often has a decisive advantage.

    Args:
        a: one player of the pairing.
        b: the other player of the pairing.
        starting_states: boards to play on.
        repetitions: games per (board, first-mover) combination.
        budgets: time budgets; defaults to :class:`Budgets`.
        use_subprocess: play each game in a forked child (hard kill available).
        phase: label recorded on the resulting :class:`Matchup`.

    Returns:
        The completed :class:`Matchup`.
    """
    spec_a, spec_b = _as_spec(a), _as_spec(b)
    games: list[MatchResult] = []
    # Counted across the whole match, so every game of it gets a distinct seed.
    game_index = 0
    for state in starting_states:
        for first, second in ((spec_a, spec_b), (spec_b, spec_a)):
            for _ in range(repetitions):
                games.append(
                    play_match(
                        _seed_for_game(first, game_index),
                        _seed_for_game(second, game_index),
                        state, budgets,
                        use_subprocess=use_subprocess,
                    )
                )
                game_index += 1
    return Matchup(spec_a.name, spec_b.name, games, phase)


# --------------------------------------------------------------------------- #
# Roster construction                                                          #
# --------------------------------------------------------------------------- #

def build_roster(
    players: Sequence[Player | PlayerSpec],
    repetition: int = DEFAULT_PLAYER_REPETITION,
) -> list[PlayerSpec]:
    """Expand each player *kind* into ``repetition`` seeded specifications.

    A round-robin never lets a player face itself, so to make each *kind* of bot
    compete against its own kind we enter ``repetition`` independent copies of
    each, to be built through :meth:`~nimarena.player.Player.create` with the seeds
    ``0, 1, ..., repetition - 1``. Every player accepts a seed, so no inspection of
    constructor signatures is needed; a deterministic bot ignores it but is still
    duplicated so its kind plays itself.

    Each copy is named ``"<name>_<seed>"`` so the copies stay distinct in the
    standings. The web app renders that suffix as a subscript.

    Args:
        players: one entry per kind (typically ``registry.all()``).
        repetition: number of copies per kind (must be ``>= 1``).

    Returns:
        ``len(players) * repetition`` specifications.

    Raises:
        ValueError: if ``repetition`` is less than 1.
    """
    if repetition < 1:
        raise ValueError(f"repetition must be >= 1, got {repetition}")
    roster: list[PlayerSpec] = []
    for entry in players:
        spec = _as_spec(entry)
        base_name = spec.cls.get_name()
        for seed in range(repetition):
            roster.append(PlayerSpec(cls=spec.cls, seed=seed, name=f"{base_name}_{seed}"))
    return roster


# --------------------------------------------------------------------------- #
# Per-player statistics                                                        #
# --------------------------------------------------------------------------- #

@dataclass
class _Stats:
    """Per-player running tallies used to build the standings and player stats.

    Attributes:
        wins: games won.
        losses: games lost.
        forfeits: games lost by forfeit (a subset of ``losses``).
        move_ms: elapsed time of every completed move, in milliseconds.
        build_ms: time taken to build this player, once per game played.
        spent_ms: total thinking time, including games whose per-move detail was
            lost to a kill.
        opponents: head-to-head ``opponent name -> [wins, losses]`` breakdown.
        elo: current Elo rating (only meaningful when Elo is enabled).
    """

    wins: int = 0
    losses: int = 0
    forfeits: int = 0
    move_ms: list[float] = field(default_factory=list)
    build_ms: list[float] = field(default_factory=list)
    spent_ms: float = 0.0
    opponents: dict[str, list[int]] = field(default_factory=dict)
    elo: float = DEFAULT_INITIAL_RATING

    @property
    def games(self) -> int:
        """Total games played (wins plus losses)."""
        return self.wins + self.losses

    @property
    def points(self) -> int:
        """Tournament points — one per win (NIM cannot draw)."""
        return self.wins

    @property
    def avg_move_ms(self) -> float:
        """Mean time per completed move in milliseconds (0.0 if none)."""
        return _mean(self.move_ms)

    @property
    def std_move_ms(self) -> float:
        """Population standard deviation of completed move times, in ms."""
        return _stdev(self.move_ms)

    @property
    def max_move_ms(self) -> float:
        """Slowest single completed move in milliseconds (0.0 if none)."""
        return max(self.move_ms, default=0.0)

    @property
    def avg_build_ms(self) -> float:
        """Mean time to build this player, in milliseconds."""
        return _mean(self.build_ms)

    @property
    def std_build_ms(self) -> float:
        """Population standard deviation of build times, in ms."""
        return _stdev(self.build_ms)

    @property
    def max_build_ms(self) -> float:
        """Slowest single build, in milliseconds."""
        return max(self.build_ms, default=0.0)

    @property
    def win_rate(self) -> float:
        """Fraction of games won in ``[0.0, 1.0]`` (0.0 if none played)."""
        return self.wins / self.games if self.games else 0.0


def _new_stats(names: list[str]) -> dict[str, _Stats]:
    """Return a fresh ``name -> _Stats`` map for every name in ``names``."""
    return {name: _Stats() for name in names}


def _tally_game(stats: dict[str, _Stats], result: MatchResult) -> None:
    """Fold one game ``result`` into the running ``stats`` (mutates ``stats``).

    A game whose child was killed contributes no per-move samples, because none
    were ever reported — but its total thinking and build times survive in shared
    memory, so they are still counted.
    """
    for rec in result.moves:
        if rec.move is not None and rec.player in stats:
            stats[rec.player].move_ms.append(rec.elapsed_ms)
    for name, value in result.build_ms.items():
        if name in stats:
            stats[name].build_ms.append(value)
    for name, value in result.spent_ms.items():
        if name in stats:
            stats[name].spent_ms += value
    winner, loser = result.winner, result.loser
    stats[winner].wins += 1
    stats[loser].losses += 1
    if result.result != "normal":
        stats[loser].forfeits += 1
    stats[winner].opponents.setdefault(loser, [0, 0])[0] += 1
    stats[loser].opponents.setdefault(winner, [0, 0])[1] += 1


def _apply_elo(stats: dict[str, _Stats], games: list[MatchResult]) -> None:
    """Update every player's Elo rating over ``games`` in play order."""
    for result in games:
        a, b = result.player_first, result.player_second
        score_a = 1.0 if result.winner == a else 0.0
        stats[a].elo, stats[b].elo = updated_ratings(
            stats[a].elo, stats[b].elo, score_a
        )


# --------------------------------------------------------------------------- #
# Result assembly (standings, player stats, totals)                            #
# --------------------------------------------------------------------------- #

def _rank_names(stats: dict[str, _Stats], *, use_elo: bool) -> list[str]:
    """Return the player names best-first under the active ranking rule.

    League with Elo ranks by rating; otherwise by points (wins). Both fall back to
    fewer forfeits, then the name. The name tie-break makes the order fully
    deterministic; average move time is deliberately *not* used, because a player
    that forfeits every move records no move times and would win that tie-break by
    having done nothing.
    """
    def key(name: str) -> tuple[float, int, str]:
        s = stats[name]
        primary = -s.elo if use_elo else float(-s.points)
        return (primary, s.forfeits, name)

    return sorted(stats, key=key)


def _standings(stats: dict[str, _Stats], *, use_elo: bool) -> list[dict[str, object]]:
    """Build the ranked, JSON-serializable classification (right-column data)."""
    standings: list[dict[str, object]] = []
    for rank, name in enumerate(_rank_names(stats, use_elo=use_elo), start=1):
        s = stats[name]
        row: dict[str, object] = {
            "rank": rank,
            "player": name,
            "points": s.points,
            "wins": s.wins,
            "losses": s.losses,
            "forfeits": s.forfeits,
            "games": s.games,
            "win_rate": round(s.win_rate, _ROUND_DIGITS),
            "avg_move_ms": round(s.avg_move_ms, _ROUND_DIGITS),
            "std_move_ms": round(s.std_move_ms, _ROUND_DIGITS),
            "max_move_ms": round(s.max_move_ms, _ROUND_DIGITS),
        }
        if use_elo:
            row["elo"] = round(s.elo, _ROUND_DIGITS)
        standings.append(row)
    return standings


def _player_stats(stats: dict[str, _Stats], *, use_elo: bool) -> list[dict[str, object]]:
    """Build the detailed per-player stats block (with head-to-head breakdown)."""
    rows: list[dict[str, object]] = []
    for name in _rank_names(stats, use_elo=use_elo):
        s = stats[name]
        opponents = [
            {"opponent": opp, "wins": wl[0], "losses": wl[1]}
            for opp, wl in sorted(s.opponents.items())
        ]
        row: dict[str, object] = {
            "player": name,
            "wins": s.wins,
            "losses": s.losses,
            "forfeits": s.forfeits,
            "games": s.games,
            "win_rate": round(s.win_rate, _ROUND_DIGITS),
            "moves_made": len(s.move_ms),
            "avg_move_ms": round(s.avg_move_ms, _ROUND_DIGITS),
            "std_move_ms": round(s.std_move_ms, _ROUND_DIGITS),
            "max_move_ms": round(s.max_move_ms, _ROUND_DIGITS),
            "total_move_ms": round(s.spent_ms, _ROUND_DIGITS),
            "avg_build_ms": round(s.avg_build_ms, _ROUND_DIGITS),
            "std_build_ms": round(s.std_build_ms, _ROUND_DIGITS),
            "max_build_ms": round(s.max_build_ms, _ROUND_DIGITS),
            "opponents": opponents,
        }
        if use_elo:
            row["elo"] = round(s.elo, _ROUND_DIGITS)
        rows.append(row)
    return rows


def _totals(
    all_games: list[MatchResult], num_matches: int, num_players: int
) -> dict[str, object]:
    """Build the overview totals block for the whole tournament."""
    total_moves = sum(len(g.moves) for g in all_games)
    total_time_ms = sum(sum(g.spent_ms.values()) for g in all_games)
    total_build_ms = sum(sum(g.build_ms.values()) for g in all_games)
    forfeits = sum(1 for g in all_games if g.result != "normal")
    longest = max((len(g.moves) for g in all_games), default=0)
    return {
        "players": num_players,
        "matches": num_matches,
        "games": len(all_games),
        "total_moves": total_moves,
        "avg_game_moves": round(_mean([float(len(g.moves)) for g in all_games]), _ROUND_DIGITS),
        "longest_game_moves": longest,
        "forfeits": forfeits,
        "total_move_time_ms": round(total_time_ms, _ROUND_DIGITS),
        "total_build_time_ms": round(total_build_ms, _ROUND_DIGITS),
    }


# --------------------------------------------------------------------------- #
# Format: round-robin (used by "simple" and "league")                          #
# --------------------------------------------------------------------------- #

def _round_robin(
    roster: list[PlayerSpec],
    starting_states: list[State],
    repetitions: int,
    budgets: Budgets,
    *,
    use_subprocess: bool,
    phase: str = "round-robin",
) -> list[Matchup]:
    """Play every unordered pair once and return the matchups, in pair order."""
    matchups: list[Matchup] = []
    for i, a in enumerate(roster):
        for b in roster[i + 1:]:
            matchups.append(
                play_matchup(
                    a, b, starting_states, repetitions, budgets,
                    use_subprocess=use_subprocess, phase=phase,
                )
            )
    return matchups


# --------------------------------------------------------------------------- #
# Format: championship (group phase + single-elimination bracket)              #
# --------------------------------------------------------------------------- #

def _group_name(index: int) -> str:
    """Return a human-friendly group name (``"Group A"``, ``"Group B"``, ...)."""
    return f"Group {chr(ord('A') + index)}" if index < 26 else f"Group {index + 1}"


def _round_name(num_participants: int) -> str:
    """Return the conventional name of a knockout round of ``num_participants``."""
    known = {2: "Final", 4: "Semifinals", 8: "Quarterfinals", 16: "Round of 16"}
    return known.get(num_participants, f"Round of {num_participants}")


def _group_table(
    members: list[str], stats: dict[str, _Stats]
) -> list[dict[str, object]]:
    """Rank a group's members by points and return a JSON-serializable table."""
    ordered = sorted(
        members,
        key=lambda n: (-stats[n].points, stats[n].forfeits, n),
    )
    return [
        {
            "rank": rank,
            "player": name,
            "points": stats[name].points,
            "wins": stats[name].wins,
            "losses": stats[name].losses,
            "forfeits": stats[name].forfeits,
            "games": stats[name].games,
            "avg_move_ms": round(stats[name].avg_move_ms, _ROUND_DIGITS),
        }
        for rank, name in enumerate(ordered, start=1)
    ]


def _seed_bracket_pairs(seeds: list[str]) -> list[tuple[str, str | None]]:
    """Pair a seed-ordered (best-first) list into first-round ties with byes.

    The bracket is padded to the next power of two; the top seeds receive byes
    (``None`` opponents). Seed ``i`` is paired with seed ``size - 1 - i`` so the
    strongest meets the weakest, as in standard single-elimination seeding.

    Called afresh for every round. That looks like a bug — it re-seeds winners
    rather than pairing adjacent ones — but ``winners`` stays in bracket-position
    order, so the ``size - 1 - i`` pairing reproduces exactly the standard fixed
    bracket, byes included.
    """
    size = 1
    while size < len(seeds):
        size *= 2
    pairs: list[tuple[str, str | None]] = []
    for i in range(size // 2):
        high = seeds[i] if i < len(seeds) else None
        low_index = size - 1 - i
        low = seeds[low_index] if low_index < len(seeds) else None
        # `high` is always the better (or equal) seed; a missing `high` cannot
        # happen for the top half, so treat `low` as the bye opponent.
        if high is None:  # pragma: no cover - only if seeds is empty
            continue
        pairs.append((high, low))
    return pairs


def _run_championship(
    roster: list[PlayerSpec],
    starting_states: list[State],
    repetitions: int,
    budgets: Budgets,
    *,
    use_subprocess: bool,
    group_size: int,
    advance_per_group: int,
) -> tuple[list[Matchup], dict[str, object]]:
    """Run a group phase then a knockout bracket.

    Returns:
        ``(matchups, structure)`` where ``matchups`` is every match played (group
        and knockout) and ``structure`` is the JSON-serializable championship
        layout (groups, their tables and advancers, and the bracket rounds with
        the eventual champion) for the page to draw.

    Raises:
        ValueError: if ``group_size`` or ``advance_per_group`` is less than 1.
    """
    if group_size < 1:
        raise ValueError(f"group_size must be >= 1, got {group_size}")
    if advance_per_group < 1:
        raise ValueError(f"advance_per_group must be >= 1, got {advance_per_group}")

    by_name = {spec.name: spec for spec in roster}
    stats = _new_stats(list(by_name))

    # --- Group phase --------------------------------------------------------
    # Deal players round-robin into groups (rather than slicing sequential
    # chunks) so kinds spread out and no group is stacked with the strongest.
    num_groups = max(1, (len(roster) + group_size - 1) // group_size)
    groups: list[list[PlayerSpec]] = [[] for _ in range(num_groups)]
    for index, spec in enumerate(roster):
        groups[index % num_groups].append(spec)
    matchups: list[Matchup] = []
    group_blocks: list[dict[str, object]] = []
    seeds_by_place: list[list[str]] = [[] for _ in range(advance_per_group)]

    for g_index, members in enumerate(groups):
        name = _group_name(g_index)
        group_matchups = _round_robin(
            members, starting_states, repetitions, budgets,
            use_subprocess=use_subprocess, phase=name,
        )
        matchups.extend(group_matchups)
        for mu in group_matchups:
            for gm in mu.games:
                _tally_game(stats, gm)
        table = _group_table([spec.name for spec in members], stats)
        advancers = [row["player"] for row in table[:advance_per_group]]
        group_blocks.append(
            {"name": name, "members": [spec.name for spec in members],
             "table": table, "advance": advancers}
        )
        # Collect advancers by finishing place so seeding favors group winners.
        for place, player_name in enumerate(advancers):
            seeds_by_place[place].append(str(player_name))

    # Seed order: every 1st place (in group order), then every 2nd place, ...
    seeds: list[str] = [name for place in seeds_by_place for name in place]

    # --- Knockout bracket ---------------------------------------------------
    rounds: list[dict[str, object]] = []
    champion = seeds[0] if seeds else ""
    current = seeds
    while len(current) > 1:
        round_name = _round_name(len(current))
        pairs = _seed_bracket_pairs(current)
        ties: list[dict[str, object]] = []
        winners: list[str] = []
        for high, low in pairs:
            if low is None:  # bye: the seed advances unopposed
                ties.append(
                    {"a": high, "b": None, "a_wins": 0, "b_wins": 0, "winner": high}
                )
                winners.append(high)
                continue
            mu = play_matchup(
                by_name[high], by_name[low], starting_states, repetitions,
                budgets, use_subprocess=use_subprocess, phase=round_name,
            )
            matchups.append(mu)
            winner = mu.winner or high  # ties broken in favor of the higher seed
            ties.append(
                {"a": high, "b": low, "a_wins": mu.a_wins,
                 "b_wins": mu.b_wins, "winner": winner}
            )
            winners.append(winner)
        rounds.append({"name": round_name, "ties": ties})
        champion = winners[0] if len(winners) == 1 else champion
        current = winners

    structure: dict[str, object] = {
        "type": "championship",
        "group_size": group_size,
        "advance_per_group": advance_per_group,
        "groups": group_blocks,
        "bracket": {"rounds": rounds, "champion": champion},
    }
    return matchups, structure


# --------------------------------------------------------------------------- #
# Top-level tournament runner                                                  #
# --------------------------------------------------------------------------- #

def validate_starting_states(states: Sequence[State]) -> list[State]:
    """Return ``states`` as clean boards, or explain why they are unplayable.

    Nothing downstream can cope with a nonsense board: an all-zero board is
    already over, so the game would end with nobody having taken the last stick,
    and a negative row makes ``legal_moves`` return nothing so the first player
    forfeits for no reason.

    Raises:
        ValueError: if any board is empty, holds a non-integer or negative row, or
            has no sticks at all.
    """
    if not states:
        raise ValueError("at least one starting board is required")
    cleaned: list[State] = []
    for board in states:
        rows = list(board)
        if not rows:
            raise ValueError("a starting board must have at least one row")
        for value in rows:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"board {rows} has a non-integer row: {value!r}")
            if value < 0:
                raise ValueError(f"board {rows} has a negative row: {value}")
        if not any(rows):
            raise ValueError(f"board {rows} has no sticks, so the game is already over")
        cleaned.append(rows)
    return cleaned


def _player_directory(specs: Sequence[PlayerSpec]) -> list[dict[str, object]]:
    """Return one identity entry per player *kind* in the roster.

    Keyed by the kind's own name (``"hard"``), not by roster entry (``"hard_0"``),
    so this stays O(kinds) rather than O(roster) and nothing is repeated on every
    standings row. The scoreboard strips the ``_<n>`` suffix to look a player up.
    """
    seen: dict[str, dict[str, object]] = {}
    for spec in specs:
        name = spec.cls.get_name()
        if name not in seen:
            seen[name] = {
                "name": name,
                "icon": spec.cls.get_icon(),
                "authors": list(spec.cls.get_authors()),
                "description": spec.cls.get_description(),
            }
    return [seen[k] for k in sorted(seen)]


def run_tournament(
    roster: Sequence[Player | PlayerSpec],
    *,
    mode: str = "simple",
    starting_states: list[State] | None = None,
    repetitions: int = DEFAULT_REPETITIONS,
    budgets: Budgets | None = None,
    elo: bool = True,
    use_subprocess: bool = True,
    group_size: int = DEFAULT_GROUP_SIZE,
    advance_per_group: int = DEFAULT_ADVANCE_PER_GROUP,
    now: Callable[[], datetime] | None = None,
    extra_config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Run a tournament in the requested ``mode`` and return the results dict.

    Args:
        roster: the competitors — :class:`PlayerSpec` objects (typically
            :func:`build_roster` output) or plain players, which are coerced.
        mode: one of :data:`TOURNAMENT_MODES` — ``"simple"``, ``"league"`` or
            ``"championship"``.
        starting_states: boards to play; defaults to
            :data:`DEFAULT_STARTING_STATES`.
        repetitions: games per (board, first-mover) combination in each match.
        budgets: time budgets; defaults to :class:`Budgets`. Pass
            :data:`UNLIMITED` to enforce nothing.
        elo: use Elo ratings for the classification (only in ``"league"`` mode).
        use_subprocess: play each game in a forked child. Set ``False`` for a
            fast, soft-budget, single-process run (handy in tests).
        group_size: players per group in the championship group phase.
        advance_per_group: players advancing from each championship group.
        now: injectable clock for deterministic ``generated_at`` timestamps.
        extra_config: extra key/values merged into the result ``config`` block.

    Returns:
        A JSON-serializable results dict with ``config``, ``standings``,
        ``matches`` (aggregated), ``player_stats``, ``totals`` and a mode-specific
        ``structure`` block.

    Raises:
        ValueError: if ``mode`` is unknown, the roster is empty, player names are
            not unique, ``repetitions`` is less than 1, or a board is unplayable.
    """
    if mode not in TOURNAMENT_MODES:
        raise ValueError(f"Unknown tournament mode {mode!r}; expected one of {TOURNAMENT_MODES}")
    if repetitions < 1:
        raise ValueError(f"repetitions must be >= 1, got {repetitions}")

    specs = [_as_spec(entry) for entry in roster]
    if not specs:
        raise ValueError("the roster is empty; there is nothing to play")
    names = [s.name for s in specs]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        # Two entries sharing a name would collapse into one standings row, with
        # both its wins and its losses credited to the same entity.
        raise ValueError(f"roster names must be unique; duplicated: {duplicates}")

    starting_states = validate_starting_states(
        DEFAULT_STARTING_STATES if starting_states is None else starting_states
    )
    budgets = Budgets() if budgets is None else budgets
    now = now or (lambda: datetime.now(timezone.utc))
    use_elo = elo and mode == "league"

    if mode == "championship":
        matchups, structure = _run_championship(
            specs, starting_states, repetitions, budgets,
            use_subprocess=use_subprocess,
            group_size=group_size, advance_per_group=advance_per_group,
        )
    else:
        matchups = _round_robin(
            specs, starting_states, repetitions, budgets,
            use_subprocess=use_subprocess,
        )
        structure = {"type": mode, "elo": use_elo}

    all_games = [g for mu in matchups for g in mu.games]
    stats = _new_stats(names)
    for mu in matchups:
        for g in mu.games:
            _tally_game(stats, g)
    if use_elo:
        _apply_elo(stats, all_games)

    config: dict[str, object] = {
        "tournament": mode,
        "starting_states": [list(s) for s in starting_states],
        "repetitions": repetitions,
        "game_budget_ms": budgets.game_ms,
        "build_budget_ms": budgets.build_ms,
        "elo": use_elo,
        "hard_timeout": use_subprocess and _fork_context() is not None,
    }
    if extra_config:
        config.update(extra_config)

    return {
        "generated_at": now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": config,
        "players": _player_directory(specs),
        "standings": _standings(stats, use_elo=use_elo),
        "matches": [mu.to_dict() for mu in matchups],
        "player_stats": _player_stats(stats, use_elo=use_elo),
        "totals": _totals(all_games, len(matchups), len(specs)),
        "structure": structure,
    }


# --------------------------------------------------------------------------- #
# CLI entry point                                                             #
# --------------------------------------------------------------------------- #

def _parse_board(text: str) -> State:
    """Parse a ``--board`` value like ``"3,5,7"`` into a list of ints."""
    try:
        return [int(part) for part in text.replace(" ", "").split(",") if part]
    except ValueError as exc:
        raise ValueError(f"bad --board {text!r}: expected comma-separated integers") from exc


def _build_arg_parser() -> object:
    """Build the ``nim-tournament`` argument parser."""
    import argparse

    from .manifest import DEFAULT_MANIFEST, DEFAULT_PLAYERS_DIR

    parser = argparse.ArgumentParser(
        prog="nim-tournament", description="Run a NIM Arena tournament."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--players-dir", default=str(DEFAULT_PLAYERS_DIR))
    parser.add_argument("--out", default="results/leaderboard.json")
    parser.add_argument(
        "--tournament", choices=TOURNAMENT_MODES, default="simple",
        help="Tournament format (default: simple).",
    )
    parser.add_argument(
        "--time-limit", type=float, default=DEFAULT_TIME_LIMIT_S,
        help="Per-player budget in seconds, for a whole game AND for building "
             f"(default: {DEFAULT_TIME_LIMIT_S}).",
    )
    parser.add_argument(
        "--game-time-limit", type=float, default=None,
        help="Override the per-player, per-game thinking budget, in seconds.",
    )
    parser.add_argument(
        "--build-time-limit", type=float, default=None,
        help="Override the per-player construction budget, in seconds.",
    )
    parser.add_argument(
        "--no-time-limit", action="store_true",
        help="Disable all budgets. Never use with untrusted players: a hung bot "
             "hangs the run.",
    )
    parser.add_argument(
        "--board", action="append", metavar="R1,R2,...",
        help="A starting board, e.g. --board 3,5,7. Repeat for several boards. "
             "Defaults to the built-in set.",
    )
    parser.add_argument(
        "--player-repetition", type=int, default=DEFAULT_PLAYER_REPETITION,
        help="Copies of each player kind to enter; seeds them 0..N-1 (default: 2).",
    )
    parser.add_argument(
        "--repetitions", type=int, default=DEFAULT_REPETITIONS,
        help="Games per (board, first-mover) combination in a match (default: 10).",
    )
    parser.add_argument(
        "--group-size", type=int, default=DEFAULT_GROUP_SIZE,
        help="Championship only: players per group (default: 4).",
    )
    parser.add_argument(
        "--advance-per-group", type=int, default=DEFAULT_ADVANCE_PER_GROUP,
        help="Championship only: players advancing per group (default: 2).",
    )
    parser.add_argument(
        "--elo", action=argparse.BooleanOptionalAction, default=True,
        help="Use Elo ratings for the league classification (default: on).",
    )
    parser.add_argument(
        "--no-subprocess", action="store_true",
        help="Play games in-process (soft budgets). Faster, but cannot kill a "
             "hung bot.",
    )
    return parser


def _budgets_from_args(args: object) -> Budgets:
    """Turn the parsed time-limit flags into a :class:`Budgets`."""
    if args.no_time_limit:  # type: ignore[attr-defined]
        return UNLIMITED

    def to_ms(seconds: float, label: str) -> int:
        if seconds <= 0:
            raise ValueError(f"{label} must be greater than 0, got {seconds}")
        return max(1, round(seconds * _MS_PER_SECOND))

    shared = args.time_limit  # type: ignore[attr-defined]
    game = args.game_time_limit  # type: ignore[attr-defined]
    build = args.build_time_limit  # type: ignore[attr-defined]
    return Budgets(
        game_ms=to_ms(game if game is not None else shared, "--game-time-limit"),
        build_ms=to_ms(build if build is not None else shared, "--build-time-limit"),
    )


def main(argv: list[str] | None = None) -> int:
    """CLI: load players from the manifest, run the tournament, write results.

    Usage::

        nim-tournament [--out results/leaderboard.json]
                       [--tournament simple|league|championship]
                       [--time-limit 2.0] [--board 3,5,7] [--repetitions 10]
                       [--player-repetition 2] [--no-elo] [--no-subprocess]

    Returns:
        ``0`` on success, ``1`` on a configuration or manifest error.
    """
    import json
    from pathlib import Path
    from typing import Any, cast

    from .manifest import ManifestError, load_players

    args = _build_arg_parser().parse_args(argv)  # type: ignore[attr-defined]

    try:
        budgets = _budgets_from_args(args)
        boards = (
            [_parse_board(b) for b in args.board] if args.board else None
        )
        if boards is not None:
            boards = validate_starting_states(boards)
        registry = load_players(args.manifest, args.players_dir)
        kinds = registry.all()
        if not kinds:
            # Writing an empty leaderboard here would let the tournament workflow
            # commit it over a good one.
            print(
                "error: no players loaded from the manifest; refusing to write an "
                "empty leaderboard.",
                file=__import__("sys").stderr,
            )
            return 1
        roster = build_roster(kinds, args.player_repetition)
    except (ManifestError, ValueError) as exc:
        print(f"error: {exc}", file=__import__("sys").stderr)
        return 1

    print(
        f"Loaded {len(kinds)} player kinds; roster of {len(roster)} "
        f"({args.player_repetition} per kind): {', '.join(s.name for s in roster)}"
    )
    limits = (
        "no time limit"
        if budgets.game_ms is None
        else f"{budgets.game_ms} ms/game + {budgets.build_ms} ms/build per player"
    )
    print(
        f"Format: {args.tournament} · {args.repetitions} reps/board · {limits}"
        + (" · Elo" if args.elo and args.tournament == "league" else "")
    )

    try:
        leaderboard = run_tournament(
            roster,
            mode=args.tournament,
            starting_states=boards,
            repetitions=args.repetitions,
            budgets=budgets,
            elo=args.elo,
            use_subprocess=not args.no_subprocess,
            group_size=args.group_size,
            advance_per_group=args.advance_per_group,
            extra_config={
                "time_limit_s": args.time_limit,
                "player_repetition": args.player_repetition,
            },
        )
    except ValueError as exc:
        print(f"error: {exc}", file=__import__("sys").stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(leaderboard, indent=2) + "\n", encoding="utf-8")

    standings = cast("list[dict[str, Any]]", leaderboard["standings"])
    use_elo = bool(cast("dict[str, Any]", leaderboard["config"])["elo"])
    print(f"\nClassification (written to {out_path}):")
    for row in standings:
        score = f"elo {row['elo']}" if use_elo else f"{row['points']} pts"
        print(
            f"  {row['rank']}. {row['player']:<18} {score:<12} "
            f"W {row['wins']:<4} L {row['losses']:<4} forfeits {row['forfeits']}"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
