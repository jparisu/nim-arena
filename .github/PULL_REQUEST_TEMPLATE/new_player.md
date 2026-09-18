<!--
New-player submission template.
To use it explicitly, append ?template=new_player.md to the PR URL, or just copy
this checklist into your PR description.
-->

## New player: <!-- your bot's name -->

**Author:** <!-- your GitHub handle -->
**Strategy in one sentence:** <!-- what does your bot do? -->

### Submission checklist

- [ ] Added a single file `players/custom/<my_bot>.py`.
- [ ] The class subclasses `nimarena.player.Player`.
- [ ] `get_name`, `get_authors`, `get_description` and `get_icon` are implemented.
- [ ] The icon is a **single** emoji, and not already used by another player.
- [ ] The name is **unique** — no admitted player already uses it.
- [ ] `choose_move(self, state) -> (row, count)` returns a **legal** move.
- [ ] Does **not** mutate the `state` it receives.
- [ ] Added **exactly one** entry to `players/custom/players.yaml` (`file` and `class`).
- [ ] No external dependencies beyond the standard library and `nimarena`.
- [ ] No network / filesystem / subprocess / `eval` / `exec`.
- [ ] Runs locally: `pytest` is green and `nim-tournament --no-subprocess` works.

### Maintainer review (acceptance criteria)

- [ ] **Design** — one file in `players/custom/` + one manifest line, minimal.
- [ ] **Correctness** — CI green; legal moves; no mutation; no errors/timeouts vs
      the reference bots.
- [ ] **No malware** — code read in full; nothing suspicious.

<!--
A player that errors or times out will not be merged — robustness is the
submitter's responsibility. See CONTRIBUTING.md and
https://nim-arena.readthedocs.io/en/latest/arena/submit-a-player/
-->
