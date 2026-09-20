# Python in the browser

!!! warning "Scaffold — not written yet"
    This page is a placeholder. The outline below is what it will cover.

## Outline

- What [Pyodide](https://pyodide.org) is: CPython compiled to WebAssembly,
  loaded from a CDN, running inside the tab.
- Why it matters: your library runs **as written**. No second implementation in
  JavaScript to keep in sync.
- Loading it, and the first-load cost the user pays.
- Getting your own package in: bundling `src/` into a `.zip` the page unpacks.
- The Python ↔ JavaScript boundary. Keep it narrow, and pass JSON across it.
- Not freezing the page: the event loop, and what long-running Python does to it.
- Limits: no threads, no sockets, no filesystem.

## Where to go next

- [The web app](../../../game/advanced/web.md) — this repository doing exactly
  this, documented in full.
- [GitHub Pages](../../github/pages.md) — publishing the result.
