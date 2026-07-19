# `players/` — community & reference bots

Every NIM Arena player lives here as a single `.py` file that subclasses
[`nimarena.player.Player`](../src/nimarena/player.py) and is admitted through the
[`players.yaml`](../players.yaml) manifest at the repo root.

## Reference players (ship with the project)

| File | Class | Level |
|------|-------|-------|
| [`random_bot.py`](random_bot.py) | `RandomBot` | 1 — random (baseline & template) |
| [`greedy_bot.py`](greedy_bot.py) | `GreedyBot` | worked example for the docs |
| [`minimax_bot.py`](minimax_bot.py) | `MinimaxBot` | 2 — depth-limited minimax |
| [`perfect_bot.py`](perfect_bot.py) | `PerfectBot` | 3 — provably optimal (nim-sum) |

## Add your own

1. Copy [`random_bot.py`](random_bot.py) to `players/<your_bot>.py`.
2. Rename the class, set a unique `name`, implement `choose_move`.
3. Add one entry to [`players.yaml`](../players.yaml).
4. Open a Pull Request.

Full walkthrough: **[CONTRIBUTING.md](../CONTRIBUTING.md)** and the
[online docs](https://nimarena.readthedocs.io/en/latest/submit-a-player/).
