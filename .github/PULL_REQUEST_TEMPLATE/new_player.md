<!--
New-player submission template.
To use it explicitly, append ?template=new_player.md to the PR URL, or just copy
this checklist into your PR description.
-->

## New player: <!-- your bot's name -->

**Author:** <!-- your GitHub handle -->
**Strategy in one sentence:** <!-- what does your bot do? -->

### Submission checklist

- [ ] Added a single file `players/<my_bot>.py`.
- [ ] The class subclasses `nimarena.player.Player`.
- [ ] `name` is set and **unique** (matches the manifest entry).
- [ ] `choose_move(self, state) -> (row, count)` returns a **legal** move.
- [ ] Does **not** mutate the `state` it receives.
- [ ] Added **exactly one** entry to `players.yaml` (name, author, file, class).
- [ ] No external dependencies beyond the standard library and `nimarena`.
- [ ] No network / filesystem / subprocess / `eval` / `exec`.
- [ ] Runs locally: `pytest` is green and `nim-tournament --no-subprocess` works.

### Maintainer review (acceptance criteria)

- [ ] **Design** — one file + one manifest line, minimal and readable.
- [ ] **Correctness** — CI green; legal moves; no mutation; no errors/timeouts vs
      the reference bots.
- [ ] **No malware** — code read in full; nothing suspicious.

<!--
A player that errors or times out will not be merged — robustness is the
submitter's responsibility. See CONTRIBUTING.md and
https://nim-arena.readthedocs.io/en/latest/submit-a-player/
-->
