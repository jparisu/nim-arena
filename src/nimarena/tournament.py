"""Tournament runner: formats, per-move timing, timeouts, forfeits.

**Robustness (not security) is the goal.** Even accepted, well-meaning bots can
hang, crash, or return an illegal move on some edge case. This runner must
survive all of it and never abort:

* a player that **exceeds the time budget** -> forfeits that game;
* a player that **raises an exception** -> forfeits that game;
* a player that **returns an illegal move** -> forfeits that game;

in every case the reason is logged into the results and the run continues.

Why the timeout lives here (and not in the player or the game): the contract a
stranger implements must stay tiny. Time control is a property of the *match*,
so the caller owns it. Timing is measured in CI on GitHub's runners, which are
slower and more variable than a laptop — choose a generous budget.

Formats
-------
Three tournament formats are supported (``--tournament``):

* ``simple`` — every pair plays one match; players are ranked by points (wins).
* ``league`` — every pair plays one match; players are ranked by an
  :mod:`Elo rating <nimarena.elo>` (per game) when enabled, else by points.
* ``championship`` — a group phase (round-robin in groups of four, top two
  advance) followed by a seeded single-elimination bracket.

A **match** between two players is played identically in every format: for each
starting board, and for each player going first once, ``repetitions`` games are
played. So a match spans ``len(boards) * 2 * repetitions`` games.

Timeout implementation
----------------------
A move is executed in a **separate process** so a truly hung bot (infinite loop)
can be killed and the tournament can move on. Threads cannot be force-killed in
Python, so they cannot honor this guarantee. If the platform cannot fork/spawn a
process, we fall back to running in-process (soft timeout: elapsed time is still
measured and over-budget moves still forfeit, but a genuine infinite loop cannot
be interrupted). The web page runs neither path — it calls ``choose_move``
directly and enforces no timeout, by design.
"""

from __future__ import annotations

import multiprocessing as mp
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import game
from .elo import DEFAULT_INITIAL_RATING, updated_ratings
from .game import Move, State
from .player import Player

#: Boards every match is played on, unless the caller overrides them.
#:
#: ``[7, 9, 11]`` is deliberately larger than the two classic boards. On small
#: boards a depth-4 search with endgame knowledge plays *optimally*, so every
#: strong player ties and the top of the ranking stops discriminating. This board
#: is big enough that the search cannot reach the endgame from the opening, which
#: is what keeps the leaderboard meaningful at the top. It costs ~120 ms for the
#: slowest move, well inside the per-move budget.
DEFAULT_STARTING_STATES: list[State] = [[3, 5, 7], [1, 3, 5, 7], [7, 9, 11]]
#: Per-move time budget, in milliseconds, used by the low-level match runner.
DEFAULT_MOVE_TIMEOUT_MS = 1000
#: Per-move time budget, in seconds, used as the CLI default.
DEFAULT_TIME_LIMIT_S = 0.5
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


# --------------------------------------------------------------------------- #
# Move execution with timeout                                                  #
# --------------------------------------------------------------------------- #

def _move_worker(queue: mp.Queue, player: Player, state: State) -> None:  # pragma: no cover
    """Child-process entry point: compute one move and report it back."""
    t0 = time.perf_counter()
    try:
        move = player.choose_move(list(state))
        elapsed_ms = (time.perf_counter() - t0) * _MS_PER_SECOND
        queue.put(("ok", move, elapsed_ms))
    except BaseException as exc:  # noqa: BLE001 - any failure becomes a forfeit
        elapsed_ms = (time.perf_counter() - t0) * _MS_PER_SECOND
        queue.put(("error", repr(exc), elapsed_ms))


def call_move(
    player: Player,
    state: State,
    timeout_ms: int | None,
    *,
    use_subprocess: bool = True,
) -> tuple[str, object, float]:
    """Ask ``player`` for a move under a time budget.

    Returns a ``(status, value, elapsed_ms)`` tuple where ``status`` is one of:

    * ``"ok"``      -> ``value`` is the returned move ``(row, count)``;
    * ``"timeout"`` -> ``value`` is ``None``;
    * ``"error"``   -> ``value`` is a ``repr`` of the exception.

    This does not check legality; :func:`play_match` does that on ``"ok"``.
    """
    if timeout_ms is None or not use_subprocess:
        return _call_in_process(player, state, timeout_ms)

    try:
        ctx = mp.get_context("fork")
    except ValueError:  # pragma: no cover - non-fork platforms
        ctx = mp.get_context("spawn")

    queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(target=_move_worker, args=(queue, player, state), daemon=True)
    proc.start()
    proc.join(timeout_ms / _MS_PER_SECOND)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return ("timeout", None, float(timeout_ms))

    try:
        status, value, elapsed_ms = queue.get_nowait()
    except Exception:  # noqa: BLE001 - crashed before reporting
        return ("error", "worker produced no result", float(timeout_ms))
    return (status, value, float(elapsed_ms))


def _call_in_process(
    player: Player, state: State, timeout_ms: int | None
) -> tuple[str, object, float]:
    """Soft-timeout fallback: run in-process, forfeit if the clock is exceeded."""
    t0 = time.perf_counter()
    try:
        move = player.choose_move(list(state))
    except BaseException as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - t0) * _MS_PER_SECOND
        return ("error", repr(exc), elapsed_ms)
    elapsed_ms = (time.perf_counter() - t0) * _MS_PER_SECOND
    if timeout_ms is not None and elapsed_ms > timeout_ms:
        return ("timeout", None, elapsed_ms)
    return ("ok", move, elapsed_ms)


# --------------------------------------------------------------------------- #
# Data structures                                                             #
# --------------------------------------------------------------------------- #

@dataclass
class MoveRecord:
    """One move played in a game, as recorded for the results log.

    Attributes:
        player: name of the player that moved.
        state_before: board seen by the player before moving.
        move: the ``(row, count)`` played, or ``None`` if the player forfeited
            (timeout, exception, or illegal move) instead of moving.
        elapsed_ms: wall-clock time the player took, in milliseconds.
    """

    player: str
    state_before: State
    move: Move | None
    elapsed_ms: float


@dataclass
class MatchResult:
    """Outcome of a single game between two players.

    Attributes:
        player_first: name of the player that moved first.
        player_second: name of the player that moved second.
        start_state: board the game started from.
        winner: name of the winning player.
        result: how the game ended — one of ``"normal"``, ``"forfeit_timeout"``,
            ``"forfeit_illegal"`` or ``"forfeit_error"``.
        moves: the moves played, in order.
        detail: human-readable explanation, populated on forfeits.
    """

    player_first: str
    player_second: str
    start_state: State
    winner: str
    result: str  # "normal" | "forfeit_timeout" | "forfeit_illegal" | "forfeit_error"
    moves: list[MoveRecord] = field(default_factory=list)
    detail: str = ""

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
    of moves played — there is nothing being estimated. Returns 0.0 for fewer than
    two values, where spread is undefined rather than infinite.
    """
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


# --------------------------------------------------------------------------- #
# Playing a single game and a whole match                                      #
# --------------------------------------------------------------------------- #

def play_match(
    first: Player,
    second: Player,
    start_state: State,
    move_timeout_ms: int | None = DEFAULT_MOVE_TIMEOUT_MS,
    *,
    use_subprocess: bool = True,
) -> MatchResult:
    """Play one game; ``first`` moves first. Never raises on bot misbehavior.

    The player who removes the last stick wins (normal play). A timeout, an
    exception, or an illegal move makes the offending player forfeit — the
    opponent is declared the winner and the game ends.
    """
    players = [first, second]
    state: State = list(start_state)
    moves: list[MoveRecord] = []
    turn = 0  # index into `players`

    while not game.is_terminal(state):
        current = players[turn]
        opponent = players[1 - turn]
        status, value, elapsed_ms = call_move(
            current, state, move_timeout_ms, use_subprocess=use_subprocess
        )

        if status == "timeout":
            moves.append(MoveRecord(current.name, list(state), None, elapsed_ms))
            return MatchResult(
                first.name, second.name, list(start_state), opponent.name,
                "forfeit_timeout", moves,
                detail=f"{current.name} exceeded {move_timeout_ms} ms",
            )
        if status == "error":
            moves.append(MoveRecord(current.name, list(state), None, elapsed_ms))
            return MatchResult(
                first.name, second.name, list(start_state), opponent.name,
                "forfeit_error", moves,
                detail=f"{current.name} raised: {value}",
            )

        move = value  # status == "ok"
        if not game.is_legal(state, move):  # type: ignore[arg-type]
            moves.append(MoveRecord(current.name, list(state), None, elapsed_ms))
            return MatchResult(
                first.name, second.name, list(start_state), opponent.name,
                "forfeit_illegal", moves,
                detail=f"{current.name} returned illegal move {move!r} for {state}",
            )

        moves.append(MoveRecord(current.name, list(state), move, elapsed_ms))  # type: ignore[arg-type]
        state = game.apply_move(state, move)  # type: ignore[arg-type]
        turn = 1 - turn

    # The player who made the last move (now `1 - turn`) took the last stick.
    winner = players[1 - turn]
    return MatchResult(
        first.name, second.name, list(start_state), winner.name, "normal", moves
    )


def play_matchup(
    a: Player,
    b: Player,
    starting_states: list[State],
    repetitions: int,
    move_timeout_ms: int | None,
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
        move_timeout_ms: per-move budget; ``None`` disables timing/forfeits.
        use_subprocess: run each move in a subprocess (hard timeout).
        phase: label recorded on the resulting :class:`Matchup`.

    Returns:
        The completed :class:`Matchup`.
    """
    games: list[MatchResult] = []
    for state in starting_states:
        for first, second in ((a, b), (b, a)):
            for _ in range(repetitions):
                games.append(
                    play_match(
                        first, second, state, move_timeout_ms,
                        use_subprocess=use_subprocess,
                    )
                )
    return Matchup(a.name, b.name, games, phase)


# --------------------------------------------------------------------------- #
# Roster construction                                                          #
# --------------------------------------------------------------------------- #

def build_roster(
    players: list[Player],
    repetition: int = DEFAULT_PLAYER_REPETITION,
) -> list[Player]:
    """Expand each player *kind* into ``repetition`` seeded copies.

    A round-robin never lets a player face itself, so to make each *kind* of bot
    compete against its own kind we enter ``repetition`` independent copies of
    each, built through :meth:`~nimarena.player.Player.create` with the seeds
    ``0, 1, ..., repetition - 1``. Every player accepts a seed, so this needs no
    inspection of constructor signatures; a deterministic bot simply ignores it
    but is still duplicated so its kind plays itself.

    Each copy is renamed ``"<name>#<seed>"`` so the copies stay distinct in the
    registry key space and the standings.

    Args:
        players: one instance per kind (typically ``registry.all()``).
        repetition: number of copies to build per kind (must be ``>= 1``).

    Returns:
        A new list of ``len(players) * repetition`` freshly constructed players.

    Raises:
        ValueError: if ``repetition`` is less than 1.
    """
    if repetition < 1:
        raise ValueError(f"repetition must be >= 1, got {repetition}")
    roster: list[Player] = []
    for player in players:
        cls = type(player)
        base_name = cls.get_name()
        for seed in range(repetition):
            copy = cls.create(seed=seed)
            copy.name = f"{base_name}#{seed}"
            roster.append(copy)
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
        opponents: head-to-head ``opponent name -> [wins, losses]`` breakdown.
        elo: current Elo rating (only meaningful when Elo is enabled).
    """

    wins: int = 0
    losses: int = 0
    forfeits: int = 0
    move_ms: list[float] = field(default_factory=list)
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
    def win_rate(self) -> float:
        """Fraction of games won in ``[0.0, 1.0]`` (0.0 if none played)."""
        return self.wins / self.games if self.games else 0.0


def _new_stats(names: list[str]) -> dict[str, _Stats]:
    """Return a fresh ``name -> _Stats`` map for every name in ``names``."""
    return {name: _Stats() for name in names}


def _tally_game(stats: dict[str, _Stats], result: MatchResult) -> None:
    """Fold one game ``result`` into the running ``stats`` (mutates ``stats``)."""
    for rec in result.moves:
        if rec.move is not None:
            stats[rec.player].move_ms.append(rec.elapsed_ms)
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

    League with Elo ranks by rating; otherwise by points (wins). Both fall back
    to fewer forfeits, faster average move, then name — the last key makes the
    order fully deterministic even when everything else ties (average move time
    is measured, so the name tie-break keeps standings reproducible).
    """
    def key(name: str) -> tuple:
        s = stats[name]
        primary = -s.elo if use_elo else -s.points
        return (primary, s.forfeits, s.avg_move_ms, name)

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
            "total_move_ms": round(sum(s.move_ms), _ROUND_DIGITS),
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
    total_time_ms = sum(
        rec.elapsed_ms for g in all_games for rec in g.moves if rec.move is not None
    )
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
    }


# --------------------------------------------------------------------------- #
# Format: round-robin (used by "simple" and "league")                          #
# --------------------------------------------------------------------------- #

def _round_robin(
    roster: list[Player],
    starting_states: list[State],
    repetitions: int,
    move_timeout_ms: int | None,
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
                    a, b, starting_states, repetitions, move_timeout_ms,
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
        key=lambda n: (-stats[n].points, stats[n].forfeits, stats[n].avg_move_ms, n),
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
    roster: list[Player],
    starting_states: list[State],
    repetitions: int,
    move_timeout_ms: int | None,
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
    """
    by_name = {p.name: p for p in roster}
    stats = _new_stats(list(by_name))

    # --- Group phase --------------------------------------------------------
    # Deal players round-robin into groups (rather than slicing sequential
    # chunks) so kinds spread out and no group is stacked with the strongest.
    num_groups = max(1, (len(roster) + group_size - 1) // group_size)
    groups: list[list[Player]] = [[] for _ in range(num_groups)]
    for index, player in enumerate(roster):
        groups[index % num_groups].append(player)
    matchups: list[Matchup] = []
    group_blocks: list[dict[str, object]] = []
    seeds_by_place: list[list[str]] = [[] for _ in range(advance_per_group)]

    for g_index, members in enumerate(groups):
        name = _group_name(g_index)
        group_matchups = _round_robin(
            members, starting_states, repetitions, move_timeout_ms,
            use_subprocess=use_subprocess, phase=name,
        )
        matchups.extend(group_matchups)
        for mu in group_matchups:
            for gm in mu.games:
                _tally_game(stats, gm)
        table = _group_table([p.name for p in members], stats)
        advancers = [row["player"] for row in table[:advance_per_group]]
        group_blocks.append(
            {"name": name, "members": [p.name for p in members],
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
                move_timeout_ms, use_subprocess=use_subprocess, phase=round_name,
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

def run_tournament(
    roster: list[Player],
    *,
    mode: str = "simple",
    starting_states: list[State] | None = None,
    repetitions: int = DEFAULT_REPETITIONS,
    move_timeout_ms: int | None = DEFAULT_MOVE_TIMEOUT_MS,
    elo: bool = True,
    use_subprocess: bool = True,
    group_size: int = DEFAULT_GROUP_SIZE,
    advance_per_group: int = DEFAULT_ADVANCE_PER_GROUP,
    now: Callable[[], datetime] | None = None,
    extra_config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Run a tournament in the requested ``mode`` and return the results dict.

    Args:
        roster: the players to compete (typically :func:`build_roster` output).
        mode: one of :data:`TOURNAMENT_MODES` — ``"simple"``, ``"league"`` or
            ``"championship"``.
        starting_states: boards to play; defaults to
            :data:`DEFAULT_STARTING_STATES`.
        repetitions: games per (board, first-mover) combination in each match.
        move_timeout_ms: per-move budget; ``None`` disables timing/forfeits.
        elo: use Elo ratings for the classification (only in ``"league"`` mode).
        use_subprocess: run each move in a subprocess (hard timeout). Set
            ``False`` for a fast, soft-timeout, single-process run (handy in
            tests).
        group_size: players per group in the championship group phase.
        advance_per_group: players advancing from each championship group.
        now: injectable clock for deterministic ``generated_at`` timestamps.
        extra_config: extra key/values merged into the result ``config`` block
            (used by the CLI to record display-only settings).

    Returns:
        A JSON-serializable results dict with ``config``, ``standings``,
        ``matches`` (per-game-averaged), ``player_stats``, ``totals`` and a
        mode-specific ``structure`` block.

    Raises:
        ValueError: if ``mode`` is not a recognized tournament format.
    """
    if mode not in TOURNAMENT_MODES:
        raise ValueError(f"Unknown tournament mode {mode!r}; expected one of {TOURNAMENT_MODES}")
    if starting_states is None:
        starting_states = [list(s) for s in DEFAULT_STARTING_STATES]
    now = now or (lambda: datetime.now(timezone.utc))
    use_elo = elo and mode == "league"

    if mode == "championship":
        matchups, structure = _run_championship(
            roster, starting_states, repetitions, move_timeout_ms,
            use_subprocess=use_subprocess,
            group_size=group_size, advance_per_group=advance_per_group,
        )
    else:
        matchups = _round_robin(
            roster, starting_states, repetitions, move_timeout_ms,
            use_subprocess=use_subprocess,
        )
        structure = {"type": mode, "elo": use_elo}

    all_games = [g for mu in matchups for g in mu.games]
    stats = _new_stats([p.name for p in roster])
    for mu in matchups:
        for g in mu.games:
            _tally_game(stats, g)
    if use_elo:
        _apply_elo(stats, all_games)

    config: dict[str, object] = {
        "tournament": mode,
        "starting_states": [list(s) for s in starting_states],
        "repetitions": repetitions,
        "move_timeout_ms": move_timeout_ms,
        "elo": use_elo,
    }
    if extra_config:
        config.update(extra_config)

    return {
        "generated_at": now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": config,
        "standings": _standings(stats, use_elo=use_elo),
        "matches": [mu.to_dict() for mu in matchups],
        "player_stats": _player_stats(stats, use_elo=use_elo),
        "totals": _totals(all_games, len(matchups), len(roster)),
        "structure": structure,
    }


# --------------------------------------------------------------------------- #
# CLI entry point                                                             #
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    """CLI: load players from the manifest, run the tournament, write results.

    Usage::

        nim-tournament [--out results/leaderboard.json]
                       [--tournament simple|league|championship]
                       [--time-limit 0.5] [--player-repetition 2]
                       [--repetitions 10] [--no-elo]
    """
    import argparse
    import json
    from pathlib import Path
    from typing import Any, cast

    from .manifest import DEFAULT_MANIFEST, DEFAULT_PLAYERS_DIR, load_players

    parser = argparse.ArgumentParser(description="Run a NIM Arena tournament.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--players-dir", default=str(DEFAULT_PLAYERS_DIR))
    parser.add_argument("--out", default="results/leaderboard.json")
    parser.add_argument(
        "--tournament", choices=TOURNAMENT_MODES, default="simple",
        help="Tournament format (default: simple).",
    )
    parser.add_argument(
        "--time-limit", type=float, default=DEFAULT_TIME_LIMIT_S,
        help="Per-move time budget in seconds (default: 0.5).",
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
        "--elo", action=argparse.BooleanOptionalAction, default=True,
        help="Use Elo ratings for the league classification (default: on).",
    )
    parser.add_argument(
        "--no-subprocess", action="store_true",
        help="Run moves in-process (soft timeout). Faster, but cannot kill a hung bot.",
    )
    args = parser.parse_args(argv)

    timeout_ms = max(1, round(args.time_limit * _MS_PER_SECOND))

    registry = load_players(args.manifest, args.players_dir)
    kinds = registry.all()
    roster = build_roster(kinds, args.player_repetition)
    print(
        f"Loaded {len(kinds)} player kinds; roster of {len(roster)} "
        f"({args.player_repetition} per kind): {', '.join(p.name for p in roster)}"
    )
    print(
        f"Format: {args.tournament} · {args.repetitions} reps/board · "
        f"time limit {args.time_limit}s"
        + (" · Elo" if args.elo and args.tournament == 'league' else "")
    )

    leaderboard = run_tournament(
        roster,
        mode=args.tournament,
        repetitions=args.repetitions,
        move_timeout_ms=timeout_ms,
        elo=args.elo,
        use_subprocess=not args.no_subprocess,
        extra_config={
            "time_limit_s": args.time_limit,
            "player_repetition": args.player_repetition,
        },
    )

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
