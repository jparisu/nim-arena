# AI-usage log

The project requires using AI coding tools *and* being able to explain every
decision. Keep a short running log here: what you asked the tools to do, what
worked, and — most usefully — where the tools got it **wrong** and how you caught
and fixed it.

| Date | Task asked of the AI | Outcome | Where it went wrong / what you fixed |
|------|----------------------|---------|--------------------------------------|
| 2026-07-17 | Scaffold the whole project from `devs/design_prompt.md` | Generated engine, API, 3 AIs, tournament, web app, docs, CI | Reviewed the timeout mechanism (process-based kill vs. thread) and the minimax heuristic (kept it non-nim-sum on purpose so the ranking holds). Verified the Pyodide flow end-to-end in headless Chrome. |
|      |                      |         |                                      |

## Design decisions to be able to defend orally

- **Why a manifest (`players.yaml`) and not folder auto-scan?** The trust boundary
  is visible in one PR diff; no stranger's code runs merely to be discovered.
- **Why does the timeout live in the tournament, not the player?** The contract a
  stranger implements must stay tiny; time control is a property of the match. It
  is enforced by running each move in a separate process so a hung bot can be
  killed.
- **Why does `apply_move` return a new state?** Minimax explores many hypothetical
  futures; shared mutable state would be a subtle bug source.
- **Why is the medium AI depth-limited with a non-nim-sum heuristic?** A full-depth
  minimax would be perfect (NIM is solved); a weak heuristic + shallow depth keeps
  it genuinely beatable, so the ranking held. (Historical: that roster was
  replaced by the random/easy/medium/hard ladder — see DESIGN_DECISIONS.md D5.)
- **Why no JS duplication of the rules?** One source of truth — the same Python
  runs in CI and in the browser via Pyodide; two copies would silently drift.
