# HTML, CSS and JavaScript

A web page is three languages with three jobs, and keeping them apart is most of
what "well built" means:

| | Is | Lives in |
| --- | --- | --- |
| **HTML** | the content and its structure | `index.html` |
| **CSS** | the appearance | `style.css` |
| **JavaScript** | the behaviour | `app.js` |

Three files, three concerns. Inline `style="…"` attributes and `onclick="…"`
handlers work, and they are how a page becomes unmaintainable by week three.

## The smallest page that works

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>My game</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <h1>My game</h1>
    <div id="board"></div>
    <button id="new-game">New game</button>

    <script src="app.js"></script>
  </body>
</html>
```

Three details in there are not decoration:

- **`<meta name="viewport">`** is what makes the page usable on a phone. Without
  it, a mobile browser renders at desktop width and scales down.
- **`id` attributes** are the handles JavaScript uses. Give one to anything the
  script needs to find.
- **`<script>` at the end of `<body>`** runs after the elements above it exist.
  A script in `<head>` runs first and finds nothing.

## The DOM, in four calls

The **DOM** is the browser's live object model of the page. Changing it changes
what is on screen, immediately. You need almost none of its surface:

```js
const board = document.getElementById("board");        // find one element
const cells = document.querySelectorAll(".stick");     // find many, by CSS selector

board.textContent = "3 5 7";                           // set text, safely
board.classList.toggle("hidden", isOver);              // add/remove a class

document.getElementById("new-game")
        .addEventListener("click", () => newGame());   // react to something
```

`textContent` over `innerHTML` is a habit worth forming: `textContent` writes
text, `innerHTML` parses markup, and the second one turns any string you did not
write yourself into a way to inject HTML into your page. When you genuinely need
markup, escape the parts that came from data — this repository keeps a four-line
`esc()` in [`web/js/core.js`](https://github.com/jparisu/nim-arena/blob/main/web/js/core.js)
and uses it on every interpolated value.

**Build elements, do not concatenate strings.** A small helper pays for itself
within an hour:

```js
const el = (tag, cls, txt) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt != null) e.textContent = txt;
  return e;
};
```

## Loading data without a backend

A static page cannot query a database, but it can read a file that is sitting
next to it:

```js
async function loadScoreboard() {
  const resp = await fetch("leaderboard.json", { cache: "no-cache" });
  if (!resp.ok) throw new Error(`leaderboard.json → HTTP ${resp.status}`);
  return resp.json();
}
```

That is the whole mechanism behind this project's scoreboard: a
[scheduled workflow](../../github/actions.md) runs the tournament, commits
`leaderboard.json`, and the page fetches it. Read-only, versioned, free, and no
server involved.

`{ cache: "no-cache" }` matters more than it looks. Without it a browser will
happily serve you yesterday's copy of a file that a workflow updated an hour
ago, and you will spend an afternoon debugging a tournament that ran correctly.

!!! warning "Everything you ship is public"
    There is no private half of a static site. Your JavaScript, your JSON and
    anything embedded in them can be read by any visitor with the developer
    tools open. Never put a token, a password or an answer key in a file the
    browser downloads. If you need a secret, you need a server — see
    [Hosting](../hosting.md).

## Keeping it readable as it grows

No framework. React, Vue and Svelte are good tools that all want a build step, a
`node_modules`, and a second toolchain in a project whose real language is
Python. For a game UI, plain files are enough, and they are still enough at a
thousand lines if you split them.

This repository's page is about 2,500 lines and has no build step for the
JavaScript at all. What keeps it readable:

**One file per screen.** [`web/js/`](https://github.com/jparisu/nim-arena/tree/main/web/js)
holds `core.js` (helpers everything uses), then `play.js`, `scoreboard.js` and
`tournament.js` — one screen each — and `main.js`, which boots and wires them.

**HTML partials.** Each screen's markup is its own file under
`web/screens/`, fetched and injected at boot:

```js
const parts = await Promise.all(
  SCREENS.map(async (name) => {
    const resp = await fetch(`screens/${name}.html`, { cache: "no-cache" });
    if (!resp.ok) throw new Error(`screens/${name}.html → HTTP ${resp.status}`);
    return resp.text();
  }),
);
host.innerHTML = parts.join("\n");
```

Five screens in one `index.html` is a file nobody can edit. Five files, injected
into one page, is five files — and it stays a single page, so the Python engine
boots once instead of once per tab.

**One shared renderer.** The board is drawn by a single `paintBoard(container,
state, {onPick})` in `core.js`, called by both the Play screen and the
Tournament screen. Two copies of a board renderer diverge; one copy cannot.

## Failing loudly

A static page has no server log. When something throws, the default outcome is a
button that does nothing and a user with no idea why — the least debuggable bug
report there is.

Two habits fix it, and both are in this repository's
[`main.js`](https://github.com/jparisu/nim-arena/blob/main/web/js/main.js):

```js
// 1. Nothing escapes silently.
window.addEventListener("error", (e) => showFatal("Unexpected error", e.error));
window.addEventListener("unhandledrejection", (e) => showFatal("Unexpected error", e.reason));

// 2. One broken step cannot disarm the others.
function step(label, fn) {
  try { fn(); return true; }
  catch (err) { showFatal(`Could not set up ${label}`, err); return false; }
}
```

The second one is the subtler win. Wiring every handler in one straight line
means an exception halfway through leaves the *later* buttons with no handler at
all — and those buttons then fail in a way that points nowhere near the cause.

## Running it locally

Serve the folder. Do not open the file.

```console
$ python -m http.server -d web 8000
# then open http://localhost:8000
```

Double-clicking `index.html` gives you a `file://` URL, and on `file://` the
browser blocks `fetch()` for security reasons. Your page will load, look
correct, and silently fail to read any of its data — a confusing failure with a
one-line fix.

## Where to go next

- [Python in the browser](pyodide.md) — running your package client-side, so
  the rules are never written twice.
- [GitHub Pages](../../github/pages.md) — publishing the folder, for free.
- [The web app](../../../game/advanced/web.md) — this repository's page,
  documented end to end.
