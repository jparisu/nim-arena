# NIM Arena — Build a Game, an AI, and the Machinery Around It

**A project for the Artificial Intelligence course**
Weight: 24% of the subject (6 ECTS) · Team size: 2–3 · Duration: ~2 months

---

## 0. Table of contents

1. [What this project is](#1-what-this-project-is)
2. [Learning objectives](#2-learning-objectives)
3. [The game: parametrized NIM](#3-the-game-parametrized-nim)
4. [System architecture](#4-system-architecture)
5. [The Python library](#5-the-python-library)
6. [The player API (core deliverable)](#6-the-player-api-core-deliverable)
7. [The three AI levels](#7-the-three-ai-levels)
8. [Player registration and discovery](#8-player-registration-and-discovery)
9. [The tournament](#9-the-tournament)
10. [The web page (GitHub Pages + Pyodide)](#10-the-web-page-github-pages--pyodide)
11. [GitHub Actions (CI)](#11-github-actions-ci)
12. [Documentation (Read the Docs)](#12-documentation-read-the-docs)
13. [Repository administration & the PR upload flow](#13-repository-administration--the-pr-upload-flow)
14. [Standard repository hygiene](#14-standard-repository-hygiene)
15. [Suggested repository structure](#15-suggested-repository-structure)
16. [Deliverables checklist](#16-deliverables-checklist)
17. [Grading & oral defense](#17-grading--oral-defense)
18. [Timeline & milestones](#18-timeline--milestones)
19. [Constraints & rules (read carefully)](#19-constraints--rules-read-carefully)

---

## 1. What this project is

You will build a complete, self-contained software project hosted **entirely on GitHub**, centered on the game of **NIM**. The project has four visible faces:

- A **Python library** that implements the game and a clean API for AI players.
- A **static web page** (GitHub Pages) where a human can play NIM against another human or against any AI — running the *actual Python AI code in the browser* via Pyodide.
- An **automatic tournament** (GitHub Actions) that pits the AIs against each other and publishes a ranked scoreboard.
- **Documentation** (Read the Docs) explaining the game, the code structure, and — most importantly — how an outsider can write and submit a new AI player through a Pull Request.

The game and a working AI are the *easy* part; modern AI coding tools will hand you those quickly. **That is intentional.** The graded difficulty lives in everything around the game: designing a clean API that a stranger can implement, running untrusted-but-reviewed code robustly, building a browser experience without a server, wiring up CI, and administering a repository like a real open-source maintainer.

> **You are required to use AI coding tools (agents, assistants) throughout.** You are *also* required to understand every design decision well enough to defend it in an oral exam. See [§17](#17-grading--oral-defense).

---

## 2. Learning objectives

By the end you should be able to:

- Model a game as a **clean, serializable state** and separate rules from strategy.
- Design a **public API** (the player interface) that others can implement without reading your internals — and feel the pain when your documentation is unclear.
- Implement and reason about **minimax** and about a **provably optimal** strategy for the same game, and understand *why* one is beatable and the other is not.
- Run **untrusted code safely and robustly**: timeouts, forfeits on error/illegal move, isolation so one bad player never breaks the tournament.
- Build a **static-first web application** with no backend, understanding exactly what "static hosting" can and cannot do, and using **WebAssembly (Pyodide)** to run Python in the browser.
- Operate a **CI pipeline** (tests, tournament, docs) and administer a repository (branch protection, PR review, issue/PR templates, contribution guidelines).
- Practice **honest, effective use of AI tools** and be able to explain, not just produce, your code.

---

## 3. The game: parametrized NIM

### Rules

NIM is played with several **rows** of **sticks**. On each turn, a player chooses **one row** and removes **one or more sticks** from that row (never from more than one row, and at least one stick). Players alternate. **The player who removes the last stick wins** (this is *normal play* convention — remember this, it determines the perfect strategy).

### Parametrization

The game must be fully parametrized:

- **Number of rows** `R` (configurable).
- **Sticks per row**, given as a list of `R` non-negative integers, e.g. `[3, 5, 7]` or `[1, 3, 5, 7]`.

A game is defined entirely by its starting configuration. The web page and the tournament must both allow configuring these values.

### State representation

The game state is just the current list of sticks per row, e.g. `[3, 0, 4]`. This representation must be **plain and JSON-serializable** (a list of ints). This is a hard requirement: the *same* representation crosses from Python (tournament, in CI) into JavaScript (rendering) and back into Python (Pyodide, in the browser). No custom objects at the boundary.

### Terminal condition

The game ends when all rows are empty (`[0, 0, ..., 0]`). The player who made the last move (removed the last stick) is the winner. There is no draw in NIM.

### A note on strategy (for your own understanding)

For normal-play NIM the optimal strategy is classic and based on the **nim-sum** (the bitwise XOR of all row sizes):

- If the nim-sum of the current position is **non-zero**, the player to move can force a win by moving to a position whose nim-sum is **zero**.
- If the nim-sum is **zero**, the player to move is in a losing position (against perfect play) and can only stall.

You will implement a player that uses exactly this. You will *also* implement a depth-limited minimax player that does **not** know this trick, so it plays well only near the endgame — that is your "medium" difficulty.

---

## 4. System architecture

Everything runs on GitHub. There is **no server you rent, no domain you buy, and no paid service**. The mental model to internalize:

> **GitHub Pages is a dumb file server.** It serves static HTML/CSS/JS and nothing else. Anything dynamic must either (a) be **precomputed by GitHub Actions** into static files, or (b) **run inside the browser itself** (JavaScript, or Python via Pyodide/WebAssembly). There is no third "server" in this stack.

```
┌──────────────────────────────────────────────────────────────────┐
│                          GitHub Repository                          │
│                                                                     │
│  ┌───────────────────┐     ┌──────────────────────────────────┐   │
│  │  Python library   │     │        GitHub Actions (CI)        │   │
│  │  - game rules     │────▶│  - run tests on push/PR           │   │
│  │  - player API     │     │  - run tournament (Python)        │   │
│  │  - 3 AI players   │     │  - build & publish docs           │   │
│  │  - tournament     │     │  - commit results/leaderboard.json│   │
│  └───────────────────┘     └───────────────┬──────────────────┘   │
│           │                                 │                       │
│           │ (same Python code)              │ writes                │
│           ▼                                 ▼                       │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                  GitHub Pages (static site)                │    │
│  │  - loads Pyodide (Python in the browser, via WebAssembly)  │    │
│  │  - imports the SAME game + player code                     │    │
│  │  - human vs human / human vs AI / AI vs AI (live)          │    │
│  │  - reads results/leaderboard.json → scoreboard             │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                    │                              │
                    ▼                              ▼
        Read the Docs (documentation)   Outsiders open PRs to add players
```

The **key elegance**: the game logic and the AI players are written **once, in Python**, and that exact same code runs both in the graded tournament (in CI) and live in the browser (via Pyodide). One source of truth. Duplicating game rules in JavaScript is **forbidden** — it creates two sources of truth that silently drift, which is a bug class you must avoid by design.

---

## 5. The Python library

The library is the heart of the project. It must be a proper, installable Python package (see [§14](#14-standard-repository-hygiene)) with at least these components:

- **Game engine** — parametrized NIM: represent state, generate legal moves, apply a move, detect the terminal state and the winner. Pure functions where possible; no I/O in the core.
- **Player API** — the abstract interface all AIs implement ([§6](#6-the-player-api-core-deliverable)).
- **Three reference AI players** — random, depth-limited minimax, and perfect XOR ([§7](#7-the-three-ai-levels)).
- **Player registry** — a mechanism to discover and list available players ([§8](#8-player-registration-and-discovery)).
- **Tournament runner** — plays all players against each other under time control, produces the results file ([§9](#9-the-tournament)).

Suggested minimal public surface (illustrative, adapt as you like):

```python
# Game engine — representative signatures
def legal_moves(state: list[int]) -> list[tuple[int, int]]:
    """All (row, count) moves legal from this state."""

def apply_move(state: list[int], move: tuple[int, int]) -> list[int]:
    """Return a NEW state with `move` applied. Must not mutate `state`."""

def is_terminal(state: list[int]) -> bool:
    """True if no sticks remain."""
```

Note `apply_move` returns a **new** state and never mutates the input — this matters because minimax explores many hypothetical futures and shared mutable state is a classic source of subtle bugs.

---

## 6. The player API (core deliverable)

**This is the spine of the project and a graded deliverable in its own right.** Everything — the tournament, the web page, and every externally submitted bot — depends on it. It must be **simple, minimal, and extensively documented**, because outsiders will implement it *from your docs alone*.

The required interface:

```python
from abc import ABC, abstractmethod

class Player(ABC):
    """A NIM player. Implement `choose_move` to build an AI.

    A player receives the current board (number of rows is len(state),
    and state[i] is the number of sticks in row i) and must return the
    move it wants to make as a tuple (row_index, sticks_to_remove).
    """

    #: Human-readable, unique player name. Shown in the UI and the scoreboard.
    name: str = "unnamed"

    @abstractmethod
    def choose_move(self, state: list[int]) -> tuple[int, int]:
        """Choose a move for the given board.

        Args:
            state: list of ints; state[i] = sticks remaining in row i.

        Returns:
            (row, count) where 0 <= row < len(state) and
            1 <= count <= state[row]. The move MUST be legal.
        """
        ...
```

### Hard requirements for the API

- **Input**: the number of rows (implied by `len(state)`) and the list of sticks per row (`state`).
- **Output**: a tuple `(row, count)` — the row index and how many sticks to remove.
- Every player exposes a **`name`** attribute (unique, human-readable). This is used to identify it in the UI and the scoreboard.
- The player **must not mutate** the `state` it receives.
- The interface must be **documented exhaustively** on Read the Docs: exact types, index base (0-based), what "legal" means, a copy-paste minimal example, and at least one full worked example of a submitted player.

### Design principle

Keep the API **as small as it can possibly be.** Every extra parameter is a thing an outsider can get wrong. If you find yourself wanting to pass more (e.g. move history, time hints), ask whether it truly belongs in the contract or whether it belongs to the tournament that *calls* the contract. (Timeouts, for example, deliberately live in the tournament, not the API — see [§9](#9-the-tournament) and [§19](#19-constraints--rules-read-carefully).)

---

## 7. The three AI levels

You must implement **at least three** AI players of distinct strength. In the tournament they must **rank in the expected order** (perfect > medium > random) across enough games to be convincing.

### Level 1 — Random (easy)

Picks a legal move uniformly at random. Trivial, but it is the essential baseline and doubles as the template every newcomer copies. Ships as a reference player.

### Level 2 — Depth-limited minimax (medium)

A standard minimax search with:

- a **maximum depth** (~5) so it does *not* see the whole game tree from the opening;
- a **trivial heuristic** at the depth cutoff (e.g. total sticks remaining, or number of non-empty rows) — deliberately **not** the nim-sum, so it is genuinely imperfect;
- alpha-beta pruning is welcome but optional.

Because it searches only 5 plies with a weak heuristic, it plays well **near the endgame** (where 5 plies reach terminal states) but makes mistakes in the opening/midgame. That is exactly what makes it beatable by the perfect player and stronger than random.

### Level 3 — Perfect XOR player (hard)

Plays **provably optimally** using the nim-sum:

1. Compute `nim_sum = XOR of all rows`.
2. If `nim_sum != 0`: find a row `i` such that `(state[i] XOR nim_sum) < state[i]`, and reduce that row to `state[i] XOR nim_sum`. This move exists whenever the nim-sum is non-zero.
3. If `nim_sum == 0`: you are in a theoretically losing position; play any legal move (e.g. remove one stick from the first non-empty row) and hope the opponent errs.

Against any imperfect opponent that ever leaves a non-zero nim-sum on your turn, this player wins. It should **never lose** from a winning starting position played out fully.

> **Note on difficulty separation.** Because NIM is fully solved, a *full-depth* minimax would also be perfect — that is why the medium player is **depth-limited with a non-nim-sum heuristic**. Make sure your medium player is genuinely weaker, or the ranking will collapse. If determinism makes your games repeat and rankings degenerate, introducing randomized tie-breaking (or a random baseline) is *your* responsibility to design around.

---

## 8. Player registration and discovery

The tournament must be able to find every player — including ones **added later by a Pull Request** — without anyone editing the tournament's own code. Use an **explicit manifest**, not import magic.

**Pattern (required):**

- Every player lives in its own file, e.g. `players/<name>/player.py`.
- A central, human-edited manifest lists the players to include. Either a plain `players/__init__.py` that imports and exposes them, or a `players.toml` naming each module and class.
- To add a player, a PR must add its file **and** add exactly **one line** to the manifest.

**Why a manifest and not auto-scanning a folder?** Because it makes the trust boundary *visible*. When someone opens a PR to add a bot, the reviewer sees, in a single diff, both the new file and the one line that admits it. That legibility is the point: the maintainer's PR review **is** the security gate. Auto-importing a directory hides what is being admitted and runs a stranger's top-level code merely to discover it.

The registry itself can be a simple singleton/dictionary mapping `name -> Player instance/class`. The tournament iterates over the registry; it never hard-codes player names.

---

## 9. The tournament

A function in the library (and a matching GitHub Action) runs a **round-robin** among all registered players and writes a results file.

### Requirements

- **Round-robin**: every player plays every other player. Play each pairing **both ways** (each player goes first once) and ideally repeat over several starting configurations, since who moves first matters enormously in NIM.
- **Time control lives here, in the tournament — not in the players and not in the game logic.** The tournament measures each player's thinking time per move and enforces a per-move (or per-game) budget.
- **Robustness (not security) is the goal.** Even accepted, well-meaning bots can hang, crash, or return an illegal move on some edge case. The tournament must survive all of it:
  - a player that **exceeds the time budget** → forfeits that game;
  - a player that **raises an exception** → forfeits that game;
  - a player that **returns an illegal move** → forfeits that game;
  - in every case, the tournament **logs the reason and continues**. One bad player never aborts the run.
- **Ranking**: aggregate results into standings (wins/losses, and a tie-break of your choosing). The three reference AIs must land in the correct order.

### Results file

The tournament writes a machine-readable file (e.g. `results/leaderboard.json`) that records, at minimum, **match results and the time elapsed per player per move**. Suggested schema:

```json
{
  "generated_at": "2026-03-01T12:00:00Z",
  "config": { "starting_states": [[3,5,7],[1,3,5,7]], "move_timeout_ms": 1000 },
  "standings": [
    { "rank": 1, "player": "PerfectXOR", "wins": 11, "losses": 1,
      "forfeits": 0, "avg_move_ms": 0.4 }
  ],
  "matches": [
    {
      "player_first": "PerfectXOR",
      "player_second": "Minimax5",
      "start_state": [3, 5, 7],
      "winner": "PerfectXOR",
      "result": "normal",              // or "forfeit_timeout" | "forfeit_illegal" | "forfeit_error"
      "moves": [
        { "player": "PerfectXOR", "state_before": [3,5,7],
          "move": [2, 1], "elapsed_ms": 0.5 }
      ]
    }
  ]
}
```

The per-move timing is what lets the scoreboard show "how fast each AI thinks," which is a genuinely nice teaching artifact.

### The timeout mechanism (design carefully)

Timing is enforced **only in the tournament**, which runs in **CI**. This has two consequences you must document:

- The **web page / Pyodide does not enforce timeouts.** Live play is best-effort. It is therefore *possible* that some obscure state breaks a player in the browser that never came up in testing. **We accept this** — chasing it is not worth the effort and the grade does not depend on it.
- Because the graded tournament runs on **GitHub's runners** (which are slower and more variable than a laptop), the timeout must be **measured relative to CI**, and the docs must say so explicitly. A bot that passes on a fast machine can still time out in the graded run; that is a stated rule, not a surprise. Choose a generous budget.

---

## 10. The web page (GitHub Pages + Pyodide)

A **simple but genuinely cool** static site, served from GitHub Pages, that loads Pyodide and runs the **same Python game + player code** in the browser. JavaScript's job is deliberately thin: draw the board, handle clicks, animate, and call into the Python that Pyodide exposes.

### Landing menu

A clean entry screen with at least:

- **Play** — start a game.
- **Scoreboard** — view the latest tournament standings (read from `results/leaderboard.json`).
- **About / How it works** — a short explainer (bonus: link to the docs).

### In-game features (required)

- **Configure the board**: choose number of rows and sticks per row before starting.
- **Pick each side**: each of the two seats can be a **Human** or **any registered AI** (random, minimax, perfect, or any PR-added bot).
- **Change a bot mid-game**: swap the AI controlling a seat between turns without restarting.
- **AI vs AI with pacing**: let two bots play each other with a **configurable delay** between moves so a human can actually watch the game unfold.
- **Record & replay / time-travel**: record the full move history and let the viewer **scrub back and forth** through states — step backward, step forward, jump to any point, and return to the live/current state. A timeline slider is ideal.

### "Cool" ideas that make this the perfect teacher example

These are strongly encouraged; pick the ones that fit your time budget:

- **Teacher / X-ray mode**: a toggle that overlays the **nim-sum** of the current position and highlights the row(s) the perfect player would touch. This turns the game into a live lecture on the XOR strategy — invaluable for an AI class.
- **"Why did it do that?" panel**: when an AI moves, show a little explanation — for minimax, the searched depth and the evaluated score; for the perfect player, the nim-sum before and after. Makes the AI's reasoning visible.
- **Hint mode** for the human seat: show the optimal move on request (uses the perfect player under the hood).
- **Speed / think-time readout**: display each AI's move time live, mirroring the tournament's per-move timing.
- **Shareable game**: encode the move history in the URL so a game can be replayed by sharing a link (pure static, no backend).
- **Board animations**: sticks visibly disappear; the winning move gets a small celebration. Small touches, big polish.

### Constraints on the web page

- **No backend, no secrets, no external paid service.** Everything is static + Pyodide + a fetched JSON file.
- **No duplicated game logic.** The rules and AIs come from the shared Python, run through Pyodide. If you catch yourself re-writing `legal_moves` in JavaScript, stop.
- **A "run the tournament" button is *not* required and is discouraged as a live trigger.** Triggering a GitHub Action from a static page would require exposing a token in the browser, which is unsafe on a public site. Instead, either omit it or provide a **plain link to the Action's "Run workflow" page** in the GitHub UI, and let GitHub's own interface be the trigger. The page stays read-only.

---

## 11. GitHub Actions (CI)

At least three workflows (they can be separate files or jobs):

- **Tests** — run the test suite on every push and every PR. A PR that fails tests is not merged. Tests need not be exhaustive; they must at least check the game rules (legal moves, apply/win detection) and that each reference player returns legal moves. Deep coverage is **not** required — a handful of meaningful tests is enough.
- **Tournament** — run the round-robin (on a schedule and/or manually via `workflow_dispatch`), then **commit the updated `results/leaderboard.json`** back to the repo so the Pages scoreboard reflects it. Must handle forfeits/timeouts gracefully as in [§9](#9-the-tournament).
- **Docs** — build the documentation (and/or let Read the Docs build on push).

Because the repository is public, Actions minutes are free (confirm current limits). PRs from forks run with a **read-only token and no secrets**, so an untrusted bot cannot damage the repo — but it *does execute*, which is exactly why the tournament's timeouts and forfeit handling are mandatory.

---

## 12. Documentation (Read the Docs)

Hosted on Read the Docs, built from the repo (e.g. Sphinx or MkDocs). Required sections:

- **Game rules** — how NIM works, the parametrization, the win condition.
- **Getting started** — install the library, run a game locally, run the tournament locally.
- **Code structure** — how the package is organized and how the pieces fit.
- **Player API reference** — *the priority section.* Exhaustive: the exact interface, types, index conventions, what "legal move" means, and a complete, copy-pasteable example player.
- **How to submit a new player via PR** — a step-by-step: fork, add `players/<name>/player.py`, subclass `Player`, set `name`, add the one manifest line, open the PR, pass CI. State clearly that a player which errors or times out **will not be merged** — that is the submitter's responsibility.

The quality of this documentation is graded directly, because it is what makes external contribution possible. Poor docs → nobody can implement your API → you failed the core lesson.

---

## 13. Repository administration & the PR upload flow

You run the repo like a real open-source maintainer. Newcomers add AI players by **Pull Request**; you review and merge.

- **The PR is the upload mechanism.** An outsider forks the repo, adds a player file to the designated folder, registers it in the manifest, and opens a PR. CI runs the tests (and can run the player against the reference bots).
- **The maintainer's review is the security and correctness gate.** Since code only runs after *you* accept the PR, there is no "automatic malware" risk — but you must actually *review*: does the code do what it claims, is it obviously malicious, does it conform to the API? "Design and correctness, and avoiding malware" must be an **explicit, documented part of your acceptance criteria.**
- **A PR that errors or times out is rejected.** Robustness of the submitted player is the submitter's job. Your tournament must still survive a bad player, but you should not merge one.
- Provide the machinery that makes this smooth:
  - **Branch protection** on `main` (require passing CI, require review).
  - A **PR template** specifically for new-player submissions (checklist: file added, manifest line added, name set, runs locally, no external dependencies, etc.).
  - **`CONTRIBUTING.md`** describing the whole flow, tied directly to the docs' "submit a player" page.
  - **Issue templates** (optional but nice).

> **Extension / part of the exercise (encouraged):** because each team builds a *different* game with its own API, a great cross-team exercise is to have a visiting team **write a brand-new player for another team's game**, implementing to *their* documented API. This exercises API design from the producer side (are your docs good enough for a stranger to succeed?) and API consumption from the consumer side (can you implement to a spec you didn't write?).

---

## 14. Standard repository hygiene

Treat this as a real Python package. Required:

- **`pyproject.toml`** — modern packaging metadata, dependencies, build config. (Prefer this over `setup.py`.)
- **`LICENSE`** — a real open-source license (MIT is fine).
- **`README.md`** — what it is, how to install, how to play, links to the live page and the docs, and a scoreboard badge/link.
- **`CONTRIBUTING.md`** — how to contribute, tied to the player-submission flow.
- **`.gitignore`** — sensible Python ignores.
- **PR template** and (optionally) **issue templates** under `.github/`.
- **Tests** under `tests/` (see [§11](#11-github-actions-ci)).
- Optional but valued: a **`CODE_OF_CONDUCT.md`**, a linter/formatter config (e.g. Ruff/Black), and status **badges** in the README.

---

## 15. Suggested repository structure

This is a suggestion, not a mandate — but it should look roughly like a real project:

```
nim-arena/
├── pyproject.toml
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── .gitignore
├── .github/
│   ├── workflows/
│   │   ├── tests.yml
│   │   ├── tournament.yml
│   │   └── docs.yml
│   └── PULL_REQUEST_TEMPLATE/
│       └── new_player.md
├── src/
│   └── nim_arena/
│       ├── __init__.py
│       ├── game.py            # rules: legal_moves, apply_move, is_terminal, winner
│       ├── player.py          # the Player ABC (the API)
│       ├── registry.py        # singleton registry
│       └── tournament.py      # round-robin runner, timeouts, forfeits, results
├── players/
│   ├── __init__.py            # the manifest (imports + registers each player)
│   ├── players.toml           # (optional alternative manifest)
│   ├── random_player/player.py
│   ├── minimax5/player.py
│   └── perfect_xor/player.py
├── results/
│   └── leaderboard.json       # written by the tournament Action
├── web/                       # GitHub Pages site
│   ├── index.html
│   ├── app.js                 # thin UI: render, clicks, Pyodide glue
│   ├── style.css
│   └── pyodide-bootstrap.js   # loads Pyodide + the Python package
├── docs/                      # Read the Docs source (Sphinx/MkDocs)
│   └── ...
└── tests/
    ├── test_game.py
    └── test_players.py
```

---

## 16. Deliverables checklist

Tick every box.

**Python library**
- [ ] Parametrized NIM engine with JSON-serializable state; `apply_move` does not mutate.
- [ ] `Player` ABC with `name` and `choose_move(state) -> (row, count)`, thoroughly documented.
- [ ] Random player (reference/template).
- [ ] Depth-limited minimax player (~depth 5, non-nim-sum heuristic).
- [ ] Perfect XOR player (provably optimal).
- [ ] Player registry + explicit manifest for discovery.
- [ ] Tournament runner: round-robin, per-move timing, timeout/illegal/exception → forfeit, never aborts.
- [ ] Results file with match results and time elapsed per player per move.

**Web (GitHub Pages + Pyodide)**
- [ ] Landing menu: Play / Scoreboard / About.
- [ ] Configurable board (rows + sticks per row).
- [ ] Human-vs-Human and Human-vs-AI (against reference and PR-added bots).
- [ ] Swap the AI controlling a seat mid-game.
- [ ] AI-vs-AI with configurable delay to watch.
- [ ] Record + scrub/replay (step back/forward, jump, return to current).
- [ ] Runs the shared Python via Pyodide (no duplicated game logic in JS).
- [ ] Scoreboard reads `results/leaderboard.json`.
- [ ] At least one "cool" educational feature (X-ray/nim-sum mode strongly recommended).

**CI / GitHub Actions**
- [ ] Tests run on push and PR; failing PRs blocked.
- [ ] Tournament workflow runs and commits the results file.
- [ ] Docs build workflow.

**Docs (Read the Docs)**
- [ ] Rules, getting started, code structure.
- [ ] Exhaustive player API reference with a full example.
- [ ] Step-by-step "submit a new player via PR" guide.

**Repo administration & hygiene**
- [ ] `pyproject.toml`, `LICENSE`, `README.md`, `CONTRIBUTING.md`, `.gitignore`.
- [ ] PR template for new players; branch protection on `main`.
- [ ] A basic but meaningful test suite.
- [ ] Explicit, documented acceptance criteria for player PRs (design, correctness, no malware).

**Process**
- [ ] Evidence of AI-tool use throughout (see below).
- [ ] All members able to defend the design orally.

---

## 17. Grading & oral defense

The project is **24% of the subject**. Suggested breakdown (the instructor may adjust):

| Component | Weight | What is assessed |
|---|---|---|
| Python library (game, API, 3 AIs, tournament) | 30% | Correctness, clean design, the API's clarity, robust tournament |
| Web page (Pages + Pyodide) | 20% | Works, required features present, polish, single-source-of-truth |
| Documentation (Read the Docs) | 15% | Especially the API reference and the PR-submission guide |
| CI, repo administration & hygiene | 15% | Working Actions, PR flow, branch protection, standard files |
| **Oral defense (individual)** | **20%** | **Understanding** — can you explain and justify it? |

### On AI tools and the oral defense

You **must** use AI coding tools; that is a requirement, not a concession. But the tools do not sit the exam — you do. In a **team oral defense**, each member must be able to:

- explain **design and structural decisions** (why a manifest and not auto-scan? why does the timeout live in the tournament? why does `apply_move` return a new state?);
- walk through any part of the code the examiner points at and explain what it does and why;
- justify trade-offs (why depth-5 minimax is beatable; why the perfect player wins; why no JS duplication of the rules).

You are also asked to keep a short **AI-usage log**: what you asked the tools to do, what worked, and — most usefully — where the tools got it **wrong** and how you caught and fixed it. This log is itself a valuable learning artifact and is looked upon favorably.

**A polished repo whose authors cannot explain it will score poorly.** The artifact proves you *produced*; the defense proves you *understand*.

---

## 18. Timeline & milestones

Two months, in four rough phases. Adjust to your pace.

- **Weeks 1–2 — Foundations.** Repo created with standard files. Game engine working with tests. `Player` ABC drafted. Random player runs. A "hello world" GitHub Pages page loads Pyodide and runs the Python engine in the browser. *Milestone: a human can play a game in the browser against the random bot.*
- **Weeks 3–4 — Intelligence.** Minimax and perfect XOR players implemented. Registry + manifest working. Tournament runner with timeouts/forfeits produces a results file locally. *Milestone: local tournament ranks the three AIs correctly.*
- **Weeks 5–6 — Automation & polish.** CI: tests, tournament (commits results), docs build. Scoreboard reads the results file on the live page. Web features: seat selection, swap mid-game, AI-vs-AI pacing, record/replay. *Milestone: the live site shows a scoreboard produced entirely by CI, and the full match of web features works.*
- **Weeks 7–8 — Documentation, administration & finishing.** Read the Docs complete (API reference + PR-submission guide). PR template, branch protection, CONTRIBUTING. Cool educational features (X-ray mode, "why did it do that"). Dry-run an external player submission. Prepare the oral defense and finalize the AI-usage log. *Milestone: an outsider can, from your docs alone, submit a working player by PR.*

A good self-test at the end: hand your repo and docs to someone not on your team and ask them to add a new AI player. If they succeed without asking you questions, your API and docs are good.

---

## 19. Constraints & rules (read carefully)

- **Everything is free and on GitHub.** No paid hosting, no purchased domain, no external paid services. GitHub (repo, Pages, Actions), Read the Docs, and Pyodide are the entire stack.
- **Python-first.** Game logic and AIs are Python. JavaScript is limited to the thin UI layer. Do **not** re-implement game rules in JavaScript — one source of truth, run through Pyodide.
- **The state at the API boundary is a plain JSON-serializable list of ints.** No custom objects cross the Python↔JS boundary.
- **The player API stays minimal and is documented exhaustively.** It carries `name` and `choose_move(state) -> (row, count)` and little else.
- **Timeouts and robustness live in the tournament, not in the players or the game logic.** The tournament enforces time limits and turns timeouts, exceptions, and illegal moves into forfeits, and never aborts. Timing is measured in **CI**; document that.
- **The web page enforces no timeouts** and is best-effort; a rare state may break a player live and that is acceptable.
- **New players arrive by Pull Request and are merged only after maintainer review.** Design, correctness, and malware-avoidance are explicit, documented acceptance criteria. A player that errors or times out is not merged.
- **You must use AI coding tools, and you must be able to explain everything you submit.** The oral defense assesses understanding, not production.

---

*Build the game fast. Spend your two months on everything around it — that is where the engineering, and the grade, actually live.*
