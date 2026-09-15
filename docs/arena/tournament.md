# The tournament

A function in the library — and a matching GitHub Action — runs a tournament
among all registered players and writes a machine-readable results file that the
[web scoreboard](web.md) renders.

## The roster

Before any games are played, the roster is built by
[`build_roster`][nimarena.tournament.build_roster]. A player kind can be entered
**more than once**, which is what lets a kind compete against *itself* — a
round-robin never pairs an instance with itself. Each copy gets its own seed
(`0, 1, …`), so a bot that depends on randomness plays a different game each time
and the run still repeats exactly. Copies are named `random_0`, `random_1`, and so
on; the web scoreboard renders that suffix as a subscript, with the player's icon
in front.

How many copies each kind gets is decided by the tournament, in
[`copies_for`][nimarena.tournament.copies_for], from the manifest that admitted
the player: `BUILTIN_COPIES` for the reference ladder in `players/builtin`, and
`CUSTOM_COPIES` for a submission in `players/custom`. Both are **2** today, and
they are two constants precisely so the submitted side can be lowered on its own
if the roster ever outgrows the tournament's time budget. `--player-repetition`
overrides every kind at once.

## A "match" is many games

In every format, a **match** between two players is played the same way: for each
starting board, and for each player going first once, `--repetitions` games are
played. So a match spans `len(boards) * 2 * repetitions` games. Alternating the
first mover matters because in NIM the first player often has a decisive
advantage.

## Formats (`--tournament`)

| Format | Pairings | Classification |
|--------|----------|----------------|
| `simple` (default) | round-robin, every pair once | points (one per win) |
| `league` | round-robin, every pair once | Elo rating (per game) |
| `championship` | group phase + knockout bracket | points (overall) + a champion |

- **simple** — the lightweight default: an all-play-all ranked by wins.
- **league** — the same all-play-all, but ranked by an
  [Elo rating][nimarena.elo] updated one game at a time (K=32, start 1500). Turn
  it off with `--no-elo` to fall back to points.
- **championship** — players are dealt into balanced **groups of four**; each
  group plays a round-robin and its **top two advance** to a **seeded
  single-elimination bracket** (byes for the top seeds when the count is not a
  power of two). Every knockout tie is a full match.

## Robustness, not security

Even well-meaning bots can hang, crash, or return an illegal move on some edge
case. The tournament survives all of it:

| Failure | Result |
|---------|--------|
| exceeds its game budget, or hangs | forfeit (`forfeit_timeout`) |
| raises an exception while playing | forfeit (`forfeit_error`) |
| returns an illegal or malformed move | forfeit (`forfeit_illegal`) |
| `create()` exceeds the build budget | forfeit (`forfeit_build_timeout`) |
| `create()` raises | forfeit (`forfeit_build_error`) |

In every case the reason is logged and the run **continues**. One bad player
never aborts the tournament.

## Why timeouts live here (and not in the player)

The contract a stranger implements must stay tiny — see the
[Player API](player-api.md). Time control is a property of the *match*, so the
caller owns it. This keeps the player a pure function of the board.

### How the hard timeout works

Each **game** runs in a separate process — one fork per game, not per move. If a
bot hangs in an infinite loop the process is **terminated** and the bot forfeits;
the tournament moves on. (Python threads cannot be force-killed, so a
thread-based timeout could not honor this guarantee.)

Forking per game rather than per move is deliberate: a player's RNG position, its
caches and its memo tables have to survive from one move to the next *within its
own game*. A fork per move would reset all of it and quietly punish any bot that
remembers anything.

A single-process "soft timeout" mode (`--no-subprocess`) is available for fast
local runs; it still measures elapsed time and forfeits over-budget players, but
cannot interrupt a true infinite loop.

### The budgets are chess clocks

Each player gets **two** budgets *per game*, not per move:

- a **game budget** (`--game-time-limit`, default 2 s) that its thinking time is
  charged against, cumulatively across all its moves. A bot may legitimately burn
  most of it on one hard position and play the rest instantly;
- a **build budget** (`--build-time-limit`, default 2 s) for `create()`, kept
  separate so precomputation cannot be smuggled into the constructor for free.

Because both players may legitimately spend their whole budget, the process is
killed only after `2 × (game + build) + grace`. When that happens the runner still
knows *who* to blame: the child records its phase, the active player and its
running totals in shared memory **before** entering any player code, so the parent
can read them after the kill. A constructor that hangs is attributed to its own
player (`forfeit_build_timeout`), not to its opponent.

!!! warning "Timing is measured in CI"
    The graded tournament runs on **GitHub's runners**, which are slower and more
    variable than a laptop. A bot that passes on a fast machine can still time out
    in the graded run. That is a stated rule, not a surprise — choose a generous
    budget and write efficient code.

## Running it

```bash
# Default: a "simple" tournament, 2 s per player per game, 3 games per board
# and first-mover.
nim-tournament --out results/leaderboard.json

# A league ranked by Elo, with a generous 2-second budget.
nim-tournament --tournament league --time-limit 2.0

# A championship with a single, fast game per board (soft timeout).
nim-tournament --tournament championship --repetitions 1 --no-subprocess
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--tournament` | `simple` | `simple`, `league` or `championship` |
| `--time-limit` | `2.0` | per-player budget in **seconds**, for a whole game *and* for construction |
| `--game-time-limit` | — | override just the thinking budget |
| `--build-time-limit` | — | override just the construction budget |
| `--no-time-limit` | off | enforce nothing (never use with untrusted players) |
| `--board` | `3,5,7` · `1,2,3,4,5` · `4,5,6,7,8,9` | a starting board, e.g. `--board 3,5,7`; repeatable, and replaces the defaults |
| `--group-size` | `4` | championship only: players per group |
| `--advance-per-group` | `2` | championship only: who advances |
| `--player-repetition` | *each kind's own* | override the copies entered for every kind |
| `--repetitions` | `3` | games per (board, first-mover) in a match |
| `--elo` / `--no-elo` | on | use Elo for the league classification |
| `--no-subprocess` | off | soft, single-process timeout (fast, local) |

## The results file

The tournament writes `results/leaderboard.json`. Its structure — and how the web
page turns it into a scoreboard — has its own page:
**[The scoreboard](scoreboard.md)**.

## Ranking and the expected order

`simple` and `championship` rank by **points** (one per win); `league` ranks by
**Elo**. Ties break on **fewer forfeits**, then on **name**, so the order is fully
deterministic.

!!! note "Average move time is deliberately *not* a tie-break"
    It would reward the wrong thing. A player that forfeits every game records no
    move times at all, so it would win any tie-break on speed. Forfeits come
    first for exactly that reason.

Across enough games the reference players land in the expected order:

```
hard  >  medium  >  easy  ≈  random
```

`hard` searches 4 plies with alpha-beta and recognizes several endgames outright,
which makes it strong — but it cannot compute the nim-sum, so it is still
beatable. `medium` runs the same search at 2 plies with a deliberately weak
total-sticks heuristic: solid right at the end of a game, unreliable before that.

`easy` and `random` are deliberately **not** ordered against each other. Emptying
the largest row is barely better than random in NIM, and which of the two lands
ahead depends on the draw. If they swap places between runs, nothing is wrong.

!!! note "Points and rank can disagree"
    In `league` mode the rank comes from Elo while the table also shows points, so
    a player with more points can sit *below* one with fewer. That is Elo working
    as intended — it weights *who* you beat, not just how often.

## Where to go next

- [The scoreboard](scoreboard.md) — what the tournament writes, and how it is
  rendered.
- [Player API](player-api.md) — the contract the tournament calls.
- [Submit a player](submit-a-player.md) — get your bot into the next run.

## API reference

::: nimarena.tournament.run_tournament

::: nimarena.tournament.copies_for

::: nimarena.tournament.build_roster

::: nimarena.tournament.play_match

## Elo ratings

::: nimarena.elo
