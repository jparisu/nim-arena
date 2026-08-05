# Design decisions

Decisions that are **not** derivable from the code, recorded so the next reader
(or the next AI agent) does not re-derive the wrong answer from
[`design_prompt.md`](design_prompt.md). The brief is the original assignment; where
this file disagrees with it, **this file wins** and says why.

Status of each entry: `DECIDED` (agreed, may not be implemented yet) or
`IMPLEMENTED`.

---

## D1 — Timing is reported as aggregates, never per move · `IMPLEMENTED`

The brief asks four times (`design_prompt.md:273, 290-295, 299, 466`) for *"the time
elapsed per player per move"*, and its example schema shows a
`moves: [{player, state_before, move, elapsed_ms}]` array. **Read that as aggregate
timing, not a move-by-move log.**

The requirement is:

- **average** time per player — required;
- **standard deviation** — the ceiling of what would ever be asked;
- a move-by-move array in the results file — **never wanted**.

Per-move times still cross the process boundary so the orchestrator can compute the
aggregates, but they are discarded after aggregation and never serialized.

Consequences:

- `results/leaderboard.json` keeps `avg` / `max` and gains `std`. It must **not**
  grow a `moves` array.
- `MoveRecord.to_dict` and `MatchResult.to_dict` (`src/nimarena/tournament.py:175`
  and `:213`) exist only to emit that array. They are already dead code — no caller
  anywhere in the repo — and should be **deleted**, because their presence is what
  makes the current output look non-compliant.
- `MoveRecord` itself stays: it is the input `_tally_game` aggregates from.

---

## D2 — One fork per game, with a chess-clock budget per player · `DECIDED`

### Why not per move (what the code does today)

`call_move` forks a child process for **every move**. The child mutates its own copy
of the player and returns only `(move, elapsed)`, so the parent's player object is
never updated. Two fatal consequences:

1. **Player state cannot survive a move.** A bot's RNG, cache or memo table is
   discarded after every single move. A seeded `RandomBot` therefore returns the
   *same* move for the same board forever, and `--repetitions 10` produces ten
   byte-identical games. Visible in the shipped leaderboard: every matchup score is
   a multiple of 10, and two identically-distributed `RandomBot`s finished 90 pts
   vs 10 pts.
2. **~7,500 process creations per run** to serve ~20 s of actual thinking.

Memoization is a legitimate and expected strategy for a solved game like NIM, so an
architecture that forbids it is wrong on the merits, not just slow.

### The model

**One fork per game.** The child builds both players and plays the whole game, so
player state advances naturally across moves. The parent is the orchestrator and
holds no player instances at all.

Budgets are **per player per game** (a chess clock), not per move. A bot may spend
most of its budget on one hard move — that is intended.

Two independent budgets, each with its own config knob and the same default:

| Budget | Covers | Exceeded ⇒ |
|---|---|---|
| `build_budget_ms` | `create(seed)` for one player | `forfeit_build_timeout` |
| `game_budget_ms` | all of that player's `choose_move` calls in the game | `forfeit_timeout` |

Budgeting construction separately exists so a bot cannot smuggle an expensive
precomputation past the clock by doing it in `__init__`. Because a constructor can
also hang, **construction must happen inside the killable child** — which is the
main reason the child builds the players rather than receiving them.

### Attribution when the child hangs (the tricky part)

The child adds a move's time to the clock *after* `choose_move` returns, so a bot
that hangs never records its time. The parent cannot recover that from a `Queue`
either: buffered writes can be lost when the child is killed.

Use **shared memory** (`multiprocessing.Array`), which is mmap'd into both processes
and therefore still readable by the parent after `SIGKILL`:

```python
acct  = ctx.Array("d", [0.0, 0.0,  0.0, 0.0])   # move_ms[2], build_ms[2]
st    = ctx.Array("i", [PHASE_BUILD, 0, 0])     # phase, active_player, moves_done
```

The child sets `phase` and `active_player` **before** entering any student code, so
the parent always knows who was executing. The parent's wall-clock deadline is:

```
deadline = 2 * build_budget_ms + 2 * game_budget_ms + grace_ms
```

`2 ×` because both players may legitimately consume their full budgets. `grace_ms`
is required: fork, imports and teardown are not free, and without it a legitimately
slow game gets killed. On expiry the parent terminates the child and decides:

| Shared state at kill | Verdict |
|---|---|
| `phase = BUILD`, `active = i` | player `i` blew the **build** budget |
| `phase = PLAY`, `move_ms[i] > game_budget` | player `i` blew the **game** budget |
| `phase = PLAY`, neither over, `active = i` | player `i` **hung** mid-move → loses |

The last row is the exact form of the "it is the fault of the last player playing"
rule: `active_player` makes it a fact rather than a heuristic. If both clocks read
over budget (a rare race where the child was killed before it could end the game
itself), attribute to the larger overage.

The child **also enforces the budget itself between moves** and ends the game
cleanly, so the parent's cut point is only a backstop for a genuine hang. Normal
timeouts never involve a kill.

### Two existing bugs this must not reproduce

- **Report the measured time, not the budget.** Today a timeout records the budget
  while the in-process path records the real elapsed time, so one field means two
  things. Always record what was measured.
- **Normalize the move to a tuple exactly once**, before validating. Today
  `is_legal(state, move)` and then `apply_move(state, move)` each evaluate `move`,
  so a bot returning a generator passes the first check, is consumed by it, and
  crashes the entire tournament in the second. Convert once, then validate.

Also keep the defensive `list(state)` copy on every `choose_move` call. Now that a
player lives for a whole game inside one process, a bot that mutates `state` would
otherwise corrupt the game rather than harmlessly mutating a throwaway copy.

### Known scope limit

Memoization spans **moves within a game**, not games. A player is rebuilt per game,
so a memo table does not carry across games of a match. Accepted: it keeps every
game independently reproducible and independently killable. Revisit only if a real
bot demonstrates the need.

---

## D3 — Players are specified, not instantiated, by the orchestrator · `DECIDED` (blocked on D2)

Because the child builds the players, the parent never holds an instance. A roster
entry becomes a **specification**:

```python
(cls, seed, display_name)      # e.g. (RandomBot, 0, "RandomBot#0")
```

This is not incidental — it removes three existing defects for free:

- `build_roster`'s `inspect.signature(cls)` sniffing for a `seed` parameter
  (`tournament.py:445`) disappears; `create(seed)` is the uniform contract.
- Rebuilding copies with `type(player)()` silently reverted non-default constructor
  configuration (so `MinimaxBot(depth=8)` came back as `depth=5`). Nothing is
  cloned any more.
- `player.name` was mutated at three different points, and the stats dict is keyed
  by name and built *after* play — so a bot that changed its own name mid-run
  crashed the tournament with a `KeyError`. The display name now belongs to the
  roster entry, not to the player object.

It also makes the **Windows `spawn` path fixable**. It is currently 100% broken: it
pickles the `Player`, whose class lives in a synthetic module
(`nimarena_player_{stem}_{abs(hash(str(path)))}`, `manifest.py:121`) that does not
exist in a fresh interpreter — and `hash()` of a `str` is salted per process, so the
name could never match anyway. Every move became a `forfeit_error` blamed on the
bot. A child that receives a *specification* re-imports from the manifest instead of
unpickling an instance.

---

## D4 — The player API: mandatory metadata + a seed-only factory · `IMPLEMENTED`

### Shape

```python
class Player(ABC):
    @classmethod
    @abstractmethod
    def get_name(cls) -> str: ...

    @classmethod
    @abstractmethod
    def get_authors(cls) -> list[str]: ...

    @classmethod
    @abstractmethod
    def get_description(cls) -> str: ...

    @classmethod
    def create(cls, seed: int) -> "Player":
        """The ONLY way the tournament builds a player. Override if configured."""
        return cls()

    @abstractmethod
    def choose_move(self, state: list[int]) -> tuple[int, int]: ...
```

`choose_move` is deliberately **unchanged** — the hot path and every existing bot
body keep working. Metadata is readable *without constructing*, which is what lets
the tournament, the docs and the web app all render a player table from the classes
alone.

### Why abstract classmethods rather than class attributes

Enforcement. `ABCMeta` refuses to instantiate a subclass that has not implemented an
abstract method:

```
TypeError: Can't instantiate abstract class MyBot without an implementation
           for abstract methods 'get_authors', 'get_name'
```

So "if they are not set, construction fails" is enforced by Python itself — no
bespoke validation. Metadata is mandatory, `description` included, which is
appropriate for a teaching repo.

**The one gap:** `ABCMeta` blocks *instantiation*, not class definition. A static
read of `MyBot.get_name()` on a non-implementing subclass returns `None` silently
rather than raising. So `manifest.load_players` must do a **validation build**
(`cls.create(seed=0)`) at load time and check the three accessors return non-empty
values, turning a broken submission into a clear `ManifestError` in CI instead of a
`None` leaking into the scoreboard.

### `create(seed)` takes only a seed

`seed` is always an `int`, never `None`. A player may ignore it (a deterministic bot
has nothing to seed) but must accept it. Because the factory is a classmethod, a bot
is free to let the seed change its own configuration — `MinimaxBot` could pick its
depth from the seed — which is what makes repeated games genuinely different.

This replaces the earlier idea of forcing `seed` into every `__init__`. That was
rejected: it pushes a tournament concern into the signature of every bot, and
`inspect`-sniffing signatures to cope with bots that opt out is exactly the smell
it was meant to remove.

### Metadata lives with the code

`players.yaml` becomes purely an **admission list** — which file and which class are
admitted:

```yaml
players:
  - file: random_bot.py
    class: RandomBot
```

Name, authors and description move out of the manifest and into the class, so there
is a single source of truth and nothing to drift. Uniqueness of `get_name()` is
validated at load time across all admitted classes — today `load_players` calls
`registry.register(..., replace=True)`, which bypasses the registry's duplicate
guard, so two entries with the same name silently overwrite each other and CI cannot
detect it, even though "unique name" is a documented merge gate.

---

## D5 — The reference roster is a difficulty ladder · `IMPLEMENTED`

The four shipped players are difficulty *levels*, not named algorithms:

| Name | Strategy | Depth |
|---|---|---|
| `random` | uniform random legal move | — |
| `easy` | empties the largest row | — |
| `medium` | negamax + alpha-beta, total-sticks heuristic | 2 |
| `hard` | negamax + alpha-beta, endgame oracle, steer-to-known heuristic | 4 |

Strategies moved out of `players/` into `nimarena.bots`, which is **public API**: a
submission may import one and configure it instead of writing a search. Each file
in `players/` is now only identity plus configuration. Every class in
`nimarena.bots` stays abstract (it declares no identity), so none can be entered in
a tournament by accident.

`medium` and `hard` share one search. The engine
(`nimarena.bots.minimax.MinimaxBot`) holds **no NIM knowledge at all** — just
negamax with alpha-beta and two hooks, `evaluate` and `known_value`.

### Why an oracle rather than a transposition table

Memoizing *search results* under alpha-beta is unsound: a pruned search returns a
bound, not a value, so correctness needs `EXACT`/`LOWER`/`UPPER` flags plus a depth
check on every entry. An oracle of values known *independently of the search* —
a hand-written table, or a structural rule — is exact by construction, so it is
safe to consult at any node and any window. That is why `known_value` is checked
*before* the depth cutoff and returns only certainties.

### `hard`'s knowledge, and why it is still beatable

Four rules, all exact, all special cases of "nim-sum zero means the mover loses":
a single non-empty row is a win; an all-ones board is decided by parity; a board
whose row counts all appear an even number of times is lost; and three tabulated
triples are lost.

Recognising *shapes* is not computing the XOR. Measured, this is the whole point:

| Board | `hard` vs a perfect nim-sum player |
|---|---|
| `[3, 5, 7]`, `[1, 3, 5, 7]`, `[5, 7, 9]` | 50% — plays **optimally**, would only tie |
| `[7, 9, 11]`, `[1, 3, 5, 7, 9]`, `[9, 11, 13]` | 0% — genuinely beatable |

In NIM there is no "slightly imperfect": one mistake against a perfect opponent
loses the game, so the result is either 50% (optimal, splitting by who moves first)
or ~0%. On small boards a depth-4 search plus endgame knowledge *is* optimal.

So `[7, 9, 11]` was added to `DEFAULT_STARTING_STATES`. Without it the top of the
ladder does not discriminate and the planned nim-sum submission could only draw
with `hard`. Cost: ~120 ms for the slowest move, against a 2000 ms budget.

### `easy` is not reliably better than `random`

Measured over 400 games per pairing: `easy` beats `random` head-to-head (53.5%) but
scores *worse* overall, because `random` occasionally stumbles into a good move
against `medium` while `easy` loses to it every time. Emptying the largest row is
not a strategy in NIM. The two are therefore **deliberately not ordered** against
each other, in the docs or in the tests.

### The XOR player is deliberately absent

No perfect player ships. It is reserved as the first Pull Request, both to
demonstrate the submission flow end-to-end and to verify the review gate on a real
change. It should land clearly at the top of the ladder.

---

## Blast radius of D2–D4

A breaking change to the player contract. Correct time to make it: **no student bots
exist yet** (0 PRs on the repo).

D1, D4 and D5 have landed. **D2 has not**, and D3 depends on it.

| Area | Status |
|---|---|
| `src/nimarena/player.py` | ✅ new ABC: three abstract accessors + `create(seed)` |
| `src/nimarena/bots/` | ✅ new package: generic engine + 4 strategies |
| `players/*.py` | ✅ four metadata-only wrappers; old bots deleted |
| `src/nimarena/manifest.py` | ✅ admission-list schema, validation build, duplicate-name rejection |
| `players.yaml` | ✅ `file` + `class` only |
| `src/nimarena/tournament.py` | ✅ `create(seed)` roster, `std`, dead `to_dict`s deleted, third board — ❌ still forks per move |
| `web/webglue.py`, `web/app.js` | ✅ metadata exposed, terminal guard, registry guard |
| docs + PR template | ✅ all updated |
| `tests/` | ✅ 87 cases incl. metadata enforcement, oracle rules, seed variation — ❌ nothing yet for budgets or hang attribution |

**Still open (D2):** per-game forking, the two time budgets, shared-memory hang
attribution, and D3's specification-based roster.

### Verification that must accompany it

- Two runs of the same seeded tournament are byte-identical (reproducible), **and**
  the repetitions within one run are **not** identical — the matchup scores must
  stop being multiples of `--repetitions`.

  Measured now, one matchup over 12 games on `[7, 9, 11]`, which isolates the
  defect precisely to the fork granularity:

  | Mode | Distinct move sequences |
  |---|---|
  | `use_subprocess=True` (the CI default) | **2** of 12 |
  | `use_subprocess=False` | **12** of 12 |

  Two, not one, because the first-mover order alternates; within one order all six
  repetitions are byte-identical. Roster-level seeding *does* work — `random#0` and
  `random#1` differ — because `build_roster` gives each copy its own seed. What
  fails is variation between the repetitions of a single match.
- A bot that hangs in `choose_move` loses *that game* and is correctly attributed;
  the tournament completes.
- A bot that hangs in `create` loses on the build budget and is correctly
  attributed.
- A bot returning a generator forfeits cleanly instead of aborting the run.
- A class missing any accessor fails at manifest load with a clear message.
- Two classes with the same `get_name()` fail at manifest load.
