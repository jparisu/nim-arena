# Contributing to NIM Arena

Thanks for your interest! The main way to contribute is by **adding a new AI
player** through a Pull Request. This page describes the whole flow. The same
content lives, with more narrative, in the
[online docs](https://nim-arena.readthedocs.io/en/latest/submit-a-player/).

## The upload mechanism is the Pull Request

There is no separate upload form. You **fork the repo, add your player file,
register it in the manifest, and open a PR**. CI runs the tests. A maintainer
reviews and merges. Your code only ever runs *after* a human accepts your PR —
which is exactly why review is the security and correctness gate.

## Add a player in 4 steps

1. **Fork & clone**, then create a branch.

2. **Add your player file** at `players/<your_bot>.py`. Copy
   [`players/random_bot.py`](players/random_bot.py) as a template. Your class
   must subclass `nimarena.player.Player`, set a unique `name`, and implement
   `choose_move(self, state) -> (row, count)`:

   ```python
   from nimarena.game import State, legal_moves
   from nimarena.player import Player

   class MyBot(Player):
       name = "MyBot"  # unique, human-readable

       def choose_move(self, state: State) -> tuple[int, int]:
           # state[i] = sticks in row i. Return (row, count):
           # 0 <= row < len(state) and 1 <= count <= state[row].
           row, sticks = next((i, s) for i, s in enumerate(state) if s > 0)
           return (row, 1)
   ```

3. **Register it** — add exactly one entry to [`players.yaml`](players.yaml):

   ```yaml
     - name: MyBot
       author: your-github-handle
       file: my_bot.py
       class: MyBot
   ```

4. **Verify locally**, then open the PR:

   ```bash
   pip install -e ".[dev]"
   pytest                      # your bot is exercised by tests/test_players.py
   nim-tournament --no-subprocess   # optional: see it in a local tournament
   ```

## Rules your player must follow

- **Output** a legal move: `(row, count)` with `0 <= row < len(state)` and
  `1 <= count <= state[row]`.
- **Do not mutate** the `state` you receive.
- **No external dependencies** beyond the standard library and `nimarena`.
- **No network, filesystem, or subprocess access.** Your `choose_move` should be
  a pure function of the board.
- **Be reasonably fast.** The tournament enforces a per-move timeout *measured on
  GitHub's runners* (slower than your laptop). A bot that times out forfeits.

## Acceptance criteria (what the maintainer checks)

A PR is merged only if it passes **all** of these — they are our explicit,
documented gate:

1. **Design** — one file in `players/`, one manifest line, subclasses `Player`,
   unique `name`, minimal and readable.
2. **Correctness** — CI is green; the bot returns legal moves and never mutates
   state; it does not error or time out against the reference bots.
3. **No malware** — the reviewer reads the code. No obfuscation, no network/file/
   subprocess/`eval`/`exec`, no attempts to read secrets or escape the sandbox.
   Anything suspicious is rejected on sight.

A player that errors or times out **will not be merged** — robustness of your
bot is your responsibility. (The tournament still survives bad bots, but we
don't ship them.)

## Contributing to the library itself

Bug fixes and improvements to the engine, docs, or web app are welcome too. Open
an issue to discuss larger changes first. Please run `ruff check .` and `pytest`
before opening a PR.

## Code of Conduct

By participating you agree to the
[Code of Conduct](CODE_OF_CONDUCT.md).
