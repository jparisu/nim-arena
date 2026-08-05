# Design decisions

Decisions that are **not** derivable from the code, recorded so the next reader
(or the next AI agent) does not re-derive the wrong answer from
[`design_prompt.md`](design_prompt.md). The brief is the original assignment; where
this file disagrees with it, **this file wins** and says why.

Status of each entry: `DECIDED` (agreed, may not be implemented yet) or
`IMPLEMENTED`.

---

## D1 — Timing is reported as aggregates, never per move · `DECIDED`

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

## D3 — Players are specified, not instantiated, by the orchestrator · `DECIDED`

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

## D4 — The player API: mandatory metadata + a seed-only factory · `DECIDED`

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

## Blast radius of D2–D4

A breaking change to the player contract. Correct time to make it: **no student bots
exist yet** (0 PRs on the repo).

| Area | Work |
|---|---|
| `src/nimarena/player.py` | the new ABC |
| `players/*.py` (4 bots) | add the three accessors; `PerfectBot`/`GreedyBot` need no `create` |
| `src/nimarena/tournament.py` | fork-per-game worker, shared-memory accounting, specs instead of instances, `std`, delete the two dead `to_dict`s |
| `src/nimarena/manifest.py` | admission-list schema, validation build, name-uniqueness check |
| `src/nimarena/registry.py` | keyed by `get_name()`; drop `replace=True` at the call site |
| `players.yaml` | drop `name` / `author` |
| `web/webglue.py`, `web/app.js` | build via `create(seed)`; read metadata from the class |
| `docs/player-api.md`, `docs/submit-a-player.md`, `players/README.md`, `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE/new_player.md` | the contract changed in all five |
| `tests/` | new tests for budgets, hang attribution, metadata enforcement, `create(seed)` variation |

### Verification that must accompany it

- Two runs of the same seeded tournament are byte-identical (reproducible), **and**
  the repetitions within one run are **not** identical — the matchup scores must
  stop being multiples of `--repetitions`.
- A bot that hangs in `choose_move` loses *that game* and is correctly attributed;
  the tournament completes.
- A bot that hangs in `create` loses on the build budget and is correctly
  attributed.
- A bot returning a generator forfeits cleanly instead of aborting the run.
- A class missing any accessor fails at manifest load with a clear message.
- Two classes with the same `get_name()` fail at manifest load.
