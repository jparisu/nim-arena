// NIM Arena — shared helpers used by every screen
//
// DOM helpers, navigation, player identity, and the board renderer. Nothing
// here knows about a specific screen.
//
// Loaded as a plain script (not an ES module): the whole app shares one global
// namespace by design, and plain scripts keep working without a bundler.
"use strict";

/* ---------------- element helpers ---------------- */
const $ = (id) => document.getElementById(id);
const el = (tag, cls, txt) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt != null) e.textContent = txt;
  return e;
};

/* Defined up here because playerHtml() below needs it, and a `const` arrow is
   unusable until its own line has been evaluated. */
const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add("hidden"), 2200);
}

/* ---------------- navigation & theme ---------------- */
function showScreen(name) {
  for (const s of document.querySelectorAll(".screen")) s.classList.add("hidden");
  $(`screen-${name}`).classList.remove("hidden");
  if (name === "scoreboard") loadScoreboard();
}

function setupNav() {
  for (const btn of document.querySelectorAll("[data-nav]")) {
    btn.addEventListener("click", () => showScreen(btn.dataset.nav));
  }
  $("theme-toggle").addEventListener("click", () => {
    const root = document.documentElement;
    const next = root.dataset.theme === "light" ? "dark" : "light";
    root.dataset.theme = next;
    try { localStorage.setItem("nim-theme", next); } catch {}
  });
  try {
    const saved = localStorage.getItem("nim-theme");
    if (saved) document.documentElement.dataset.theme = saved;
  } catch {}
}

/* ---------------- player identity ---------------- */
/* name -> {icon, authors, description}, keyed by KIND ("hard"), not roster entry
   ("hard_0"). Populated from the live registry on the Play screen and from the
   leaderboard's `players` block on the Scoreboard, which may not be the same set:
   a player can be removed from the repo after a tournament ran. */
const META = new Map();

const SUB_DIGITS = "₀₁₂₃₄₅₆₇₈₉";
/* Silhouette for a human seat; every bot supplies its own icon. */
const HUMAN_ICON = "👤";
/* Fallback when the leaderboard predates icons, or a kind is unknown. */
const BOT_ICON = "🤖";

/* Split a roster name into its kind and copy index: "hard_0" -> ["hard", "0"]. */
function splitPlayer(name) {
  const m = /^(.*)_(\d+)$/.exec(String(name));
  return m ? [m[1], m[2]] : [String(name), null];
}

function playerIcon(name) {
  const [kind] = splitPlayer(name);
  return META.get(kind)?.icon || BOT_ICON;
}

/* Plain-text label — for <option>, tooltips and anywhere markup is not allowed.
   Uses Unicode subscript digits, since <sub> cannot render inside <option>. */
function playerText(name) {
  const [kind, idx] = splitPlayer(name);
  const sub = idx == null ? "" : [...idx].map((d) => SUB_DIGITS[+d]).join("");
  return `${playerIcon(name)} ${kind}${sub}`;
}

/* HTML label — real <sub> markup, for everywhere else. */
function playerHtml(name) {
  const [kind, idx] = splitPlayer(name);
  return (
    `<span class="p-icon">${esc(playerIcon(name))}</span>` +
    `<span class="p-name">${esc(kind)}` +
    (idx == null ? "" : `<sub>${esc(idx)}</sub>`) +
    `</span>`
  );
}

/* Hard ceilings for a *playable* board. The renderer builds one element with two
   listeners per stick, so an unbounded board freezes the tab — and a 60-stick
   board is unplayable by hand long before that. Rejected rather than silently
   clamped: quietly changing what someone typed is worse than telling them. */
const MAX_ROWS = 5;
const MAX_STICKS_PER_ROW = 10;

/* Return the reason `sticks` is unplayable, or null if it is fine. */
function boardProblem(sticks) {
  if (!Array.isArray(sticks) || !sticks.length) return "A board needs at least one row.";
  if (sticks.length > MAX_ROWS) {
    return `Too many rows: ${sticks.length}. The maximum is ${MAX_ROWS}.`;
  }
  if (!sticks.every((s) => Number.isInteger(s) && s >= 0)) {
    return "Every row must be a whole number of sticks, zero or more.";
  }
  const worst = Math.max(...sticks);
  if (worst > MAX_STICKS_PER_ROW) {
    return `Too many sticks in a row: ${worst}. The maximum is ${MAX_STICKS_PER_ROW}.`;
  }
  if (!sticks.some((s) => s > 0)) return "That board has no sticks — the game is already over.";
  return null;
}

/* Draw a board into any container.
   Extracted from the Play screen so the Tournament page renders the identical
   board — same markup, same hover preview, same click semantics — without a
   second copy of it. `onPick` receives [row, count]; pass null for read-only. */
function paintBoard(container, state, { onPick = null, targetRow = -1 } = {}) {
  container.innerHTML = "";
  const interactive = typeof onPick === "function";
  container.classList.toggle("locked", !interactive);

  state.forEach((count, row) => {
    const rowEl = el("div", "row");
    if (row === targetRow) rowEl.classList.add("target");
    rowEl.appendChild(el("span", "row-index", `row ${row}`));
    for (let p = 0; p < count; p++) {
      const stick = el("div", "stick");
      if (interactive) {
        stick.classList.add("selectable");
        const removeCount = count - p; // click stick p -> remove it + all to the right
        stick.addEventListener("mouseenter", () => {
          rowEl.querySelectorAll(".stick").forEach((s, idx) => {
            if (idx >= p) s.classList.add("preview");
          });
        });
        stick.addEventListener("mouseleave", () => {
          rowEl.querySelectorAll(".stick").forEach((s) => s.classList.remove("preview"));
        });
        stick.addEventListener("click", () => onPick([row, removeCount]));
      }
      rowEl.appendChild(stick);
    }
    rowEl.appendChild(el("span", "row-count", count === 0 ? "(empty)" : `${count}`));
    container.appendChild(rowEl);
  });
}
