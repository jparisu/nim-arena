# Static web

A **static** site is a folder of files — HTML, CSS, JavaScript, images, JSON —
that a host hands out unchanged. Nothing runs on the server, because there is no
server to speak of.

That sounds limiting until you notice how much fits inside it. Everything
interactive still works; it just runs in the visitor's browser instead. This
repository's own game page is static, and it runs the project's **real Python**
through [Pyodide](pyodide.md).

<div class="grid cards" markdown>

- [**HTML, CSS and JavaScript**](html-js.md) — the three files a web page is made
  of, and the least you need to know about each.
- [**Python in the browser**](pyodide.md) — running your own package client-side
  with Pyodide, so the logic is never written twice.

</div>

## Publishing it

A static site needs a static host, and the one attached to your repository is
free: **[GitHub Pages](../../github/pages.md)**. That page covers the
`gh-pages` branch, the deploy workflow and the published URL.

## Where to go next

- [GitHub Pages](../../github/pages.md) — publishing this, for free.
- [Streamlit](../streamlit/index.md) — the other route, if you would rather write
  no JavaScript at all.
- [The web app](../../../game/advanced/web.md) — this repository's own static app,
  documented end to end.
