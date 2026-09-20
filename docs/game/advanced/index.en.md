# Advanced documentation

How NIM Arena is put together on the inside. You do **not** need any of this to
write a bot — for that, go to [Upload a new bot](../upload-a-bot/index.md).

Read it if you want to understand the machinery, fix a bug, or change the
project itself.

<div class="grid cards" markdown>

- [**Code structure**](code-structure.md) — the repository tree and how the
  modules depend on each other.
- [**The scoreboard**](scoreboard.md) — the results file, and how it is rendered.
- [**The tournament**](tournament.md) — formats, time budgets and forfeits.
- [**The web app**](web.md) — the Pyodide page that runs the same Python in your
  browser.
- [**API reference**](api.md) — every public name of `nimarena`, generated from
  the source.

</div>

## The one big idea

> The game rules and every AI are written **once, in Python**. That exact same
> code runs both the graded tournament (in CI) and live play in the browser (via
> Pyodide). **One source of truth.** The rules are never re-implemented in
> JavaScript.
