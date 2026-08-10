# The tournament

A function in the library — and a matching GitHub Action — runs a tournament
among all registered players and writes a machine-readable results file that the
[web scoreboard](web.md) renders.

## The roster: two copies of every kind

Before any games are played, the roster is built by
[`build_roster`][nimarena.tournament.build_roster], which enters
**`--player-repetition` copies of each player kind** (default **2**). This lets a
kind compete against *itself* (a round-robin never pairs an instance with itself)
and, crucially, makes runs **reproducible**: every copy of a random-dependent bot
(one whose constructor accepts a `seed`) is seeded with `0, 1, …, N-1`. Copies
are named `random_0`, `random_1`, and so on. The web scoreboard renders that
suffix as a subscript and puts each player's own icon in front of it.

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
| exceeds the time budget | forfeit (`forfeit_timeout`) |
| raises an exception | forfeit (`forfeit_error`) |
| returns an illegal move | forfeit (`forfeit_illegal`) |

In every case the reason is logged and the run **continues**. One bad player
never aborts the tournament.

## Why timeouts live here (and not in the player)

The contract a stranger implements must stay tiny — see the
[Player API](player-api.md). Time control is a property of the *match*, so the
caller owns it. This keeps the player a pure function of the board.

### How the hard timeout works

Each move runs in a **separate process**. If a bot hangs in an infinite loop, the
process is **terminated** and the bot forfeits — the tournament moves on. (Python
threads cannot be force-killed, so a thread-based timeout could not honor this
guarantee.) A single-process "soft timeout" mode (`--no-subprocess`) is available
for fast local runs; it still measures elapsed time and forfeits over-budget
moves, but cannot interrupt a true infinite loop.

!!! warning "Timing is measured in CI"
    The graded tournament runs on **GitHub's runners**, which are slower and more
    variable than a laptop. A bot that passes on a fast machine can still time out
    in the graded run. That is a stated rule, not a surprise — choose a generous
    budget and write efficient code.

## Running it

```bash
# Default: a "simple" tournament, 0.5s/move, 2 copies per kind, 10 games/board.
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
| `--board` | built-in set | a starting board, e.g. `--board 3,5,7`; repeatable |
| `--group-size` | `4` | championship only: players per group |
| `--advance-per-group` | `2` | championship only: who advances |
| `--player-repetition` | `2` | copies of each kind (seeded `0..N-1`) |
| `--repetitions` | `10` | games per (board, first-mover) in a match |
| `--elo` / `--no-elo` | on | use Elo for the league classification |
| `--no-subprocess` | off | soft, single-process timeout (fast, local) |

## The results file

The tournament writes `results/leaderboard.json`. Its shape adapts to the format
(the `structure` block differs), but the top-level keys are stable:

```json
{
  "generated_at": "2026-03-01T12:00:00Z",
  "config": {
    "tournament": "league", "starting_states": [[3,5,7],[1,3,5,7]],
    "repetitions": 10, "game_budget_ms": 2000, "build_budget_ms": 2000,
    "elo": true, "hard_timeout": true,
    "time_limit_s": 2.0, "player_repetition": 2
  },
  "standings":  [ /* ranked classification: rank, player, points, elo?, W/L, ... */ ],
  "matches":    [ /* one entry per match, averaged over its games */ ],
  "player_stats": [ /* per player: timing, win rate, head-to-head opponents */ ],
  "totals":     { /* players, matches, games, total moves, think time, ... */ },
  "structure":  { /* mode-specific: groups + bracket for championship */ }
}
```

The [web scoreboard](web.md) reads `config.tournament` and renders the matching
blocks: a right-hand **classification** column plus collapsible **Tournament
structure** (bracket/groups for a championship), **Match summary**, **Player
stats** and **Total stats** panels.

## Ranking and the expected order

`simple` and `championship` rank by **points** (one per win); `league` ranks by
**Elo**. All fall back to fewer forfeits, then faster average move, then name (so
the order is fully deterministic). Across enough games the reference players land
in the expected order:

```
hard  >  medium  >  easy  ≈  random
```

`hard` searches 4 plies with alpha-beta and recognises several endgames outright,
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

::: nimarena.tournament.run_tournament

::: nimarena.tournament.build_roster

::: nimarena.tournament.play_match

## Elo ratings

::: nimarena.elo
