// Headless smoke test for the web app: boot it exactly as the browser does,
// then drive the Tournament screen the way a user does.
//
// This exists because two bugs shipped that no Python test could see, and that
// looked identical from the outside — "the button does nothing":
//
//   * a duplicate element id, so the board was painted into a text input;
//   * `main()` throwing before the wiring ran, leaving buttons with no handler.
//
// Both are caught below. Run with `node tests/js/boot_test.js`.
"use strict";

const path = require("path");
const fs = require("fs");
const { buildDocument } = require("./domstub.js");

const ROOT = path.resolve(__dirname, "..", "..");
const WEB = path.join(ROOT, "web");

let failures = 0;
function check(label, ok, detail = "") {
  if (ok) console.log(`  ok   ${label}`);
  else { failures++; console.log(`  FAIL ${label}${detail ? " — " + detail : ""}`); }
}

/* ---------- environment ---------- */
const document = buildDocument(WEB);
global.document = document;
global.localStorage = { getItem: () => null, setItem: () => {} };
global.Event = class { constructor(t) { this.type = t; } };
// Node ≥21 defines navigator as a getter-only global; only define it if absent.
if (!globalThis.navigator) global.navigator = {};
global.history = { replaceState: () => {} };
global.location = { hash: "", origin: "http://localhost", pathname: "/" };

let pending = [];
global.setTimeout = (fn) => { pending.push(fn); return 0; };
global.clearTimeout = () => {};
const drain = () => {
  let guard = 0;
  while (pending.length && guard++ < 500) { const fns = pending; pending = []; fns.forEach((f) => f()); }
};

// Screens are fetched at boot; serve them from disk.
global.fetch = async (url) => {
  const file = path.join(WEB, url.split("?")[0]);
  if (!fs.existsSync(file)) return { ok: false, status: 404 };
  return { ok: true, status: 200, text: async () => fs.readFileSync(file, "utf8") };
};

// The engine, standing in for Pyodide. Same payload shapes webglue produces.
const PLAYERS = [
  { name: "random", icon: "🎲", authors: ["jparisu"], description: "Random legal move." },
  { name: "easy", icon: "🌱", authors: ["jparisu"], description: "Empties the largest row." },
  { name: "medium", icon: "🧠", authors: ["jparisu"], description: "Depth-2 minimax." },
  { name: "hard", icon: "⚔️", authors: ["jparisu"], description: "Depth-4 minimax." },
];
const applyMove = (st, mv) => { const s = st.slice(); s[mv[0]] -= mv[1]; return s; };
let entrantCalls = 0;
global.window = {
  _handlers: {},
  addEventListener(ev, fn) { (this._handlers[ev] ||= []).push(fn); },
  bootNim: async (onStatus) => { onStatus("Ready."); },
  NIM: {
    players: () => PLAYERS,
    playerNames: () => PLAYERS.map((p) => p.name),
    resetEntrants: () => "ok",
    createEntrant: () => "ok",
    entrantMove: (id, st) => {
      entrantCalls++;
      return { move: [st.findIndex((n) => n > 0), 1], elapsed_ms: 0.5, info: null };
    },
    // A deterministic finish: empty each row in turn.
    playAuto: (a, b, st) => {
      const moves = [];
      let s = st.slice();
      let turn = 0;
      while (s.some((x) => x > 0)) {
        const r = s.findIndex((x) => x > 0);
        moves.push([r, s[r]]);
        s = applyMove(s, [r, s[r]]);
        turn = 1 - turn;
      }
      return { moves, winner_seat: 1 - turn, result: "normal", detail: "", elapsed_ms: [1, 1] };
    },
    applyMove,
    isTerminal: (st) => st.every((x) => x === 0),
    legalMoves: (st) => st.flatMap((n, r) => Array.from({ length: n }, (_, k) => [r, k + 1])),
    perfectAnalysis: () => ({ nim_sum: 1, winning: true, move: [0, 1], target_row: 0 }),
    nimSum: () => 1,
    totalSticks: (st) => st.reduce((a, b) => a + b, 0),
  },
};

/* ---------- load every screen script, in the order index.html does ----------
   Concatenated and evaluated once: separate <script> tags share one global
   scope, and evaluating each file separately here would not. */
const shell = fs.readFileSync(path.join(WEB, "index.html"), "utf8");
const scripts = [...shell.matchAll(/<script src="(js\/[^"]+)"><\/script>/g)].map((m) => m[1]);
if (scripts.length < 5) {
  console.log(`  FAIL index.html loads only ${scripts.length} screen scripts`);
  process.exit(1);
}
const app = {};
eval(
  scripts.map((rel) => fs.readFileSync(path.join(WEB, rel), "utf8")).join("\n;\n") +
  // `const` at the top of an eval is scoped to that eval, so hand out what the
  // assertions below need to poke at.
  "\n;Object.assign(app, { T, G, tHumanMove, newGame, humanMove });"
);

const $ = (id) => document.getElementById(id);
const sticksIn = (node) => node.querySelectorAll("stick").length;

(async () => {
  console.log("boot");
  const dcl = window._handlers.DOMContentLoaded || [];
  check("index.html registers a DOMContentLoaded handler", dcl.length === 1);
  for (const fn of dcl) await fn();
  drain();

  check("no fatal banner", $("fatal").classList.contains("hidden"),
        $("fatal").innerHTML.replace(/<[^>]+>/g, " ").trim());
  check("boot overlay hidden", $("boot").classList.contains("hidden"));
  check("screens injected", $("screens").innerHTML.length > 500);
  check("no lookups for missing ids", document._missing.size === 0,
        [...document._missing].join(", "));

  console.log("\nwiring — every control a user can click must have a handler");
  for (const id of ["btn-new", "btn-hint", "btn-share", "btn-play-ai",
                    "t-start", "t-reset", "t-shuffle", "t-close-view",
                    "t-tl-first", "t-tl-prev", "t-tl-next", "t-tl-last"]) {
    check(`${id} is wired`, typeof $(id).onclick === "function");
  }

  console.log("\ntournament — all bots");
  check("slot list built", $("t-slots").children.length === 8);
  $("t-start").onclick();
  drain();
  check("bracket drawn", $("t-bracket").children.length === 3,
        `columns=${$("t-bracket").children.length}`);
  check("bracket visible", !$("t-bracket-wrap").classList.contains("hidden"));
  check("all matches played", /7 \/ 7/.test($("t-progress").textContent),
        $("t-progress").textContent);
  check("champion shown", !$("t-champion").classList.contains("hidden"));
  check("podium rendered", /podium-step/.test($("t-champion").innerHTML));

  console.log("\ntournament — replay a finished match");
  const firstTie = $("t-bracket").children[0].children[1]; // [0] is the round name
  check("finished match is clickable", typeof firstTie.onclick === "function");
  firstTie.onclick();
  check("match panel opens", !$("t-match").classList.contains("hidden"));
  check("timeline shown", !$("t-timeline").classList.contains("hidden"));
  $("t-tl-first").onclick();
  check("scrubbing to the start redraws the full board", sticksIn($("t-board")) === 16,
        `sticks=${sticksIn($("t-board"))}`);
  $("t-tl-last").onclick();
  check("scrubbing to the end empties it", sticksIn($("t-board")) === 0);
  $("t-close-view").onclick();
  check("replay closes", $("t-match").classList.contains("hidden"));

  console.log("\ntournament — a human entrant gets somewhere to play");
  $("t-reset").onclick();
  $("t-size").value = "4";
  $("t-size").onchange();
  app.T.slots[0].kind = "__human__";
  app.T.slots[0].label = "Ada";
  [1, 2, 3].forEach((i) => { app.T.slots[i].kind = "hard"; });
  $("t-start").onclick();
  drain();
  check("bracket paused for the human", app.T.live !== null);
  check("match panel visible", !$("t-match").classList.contains("hidden"));
  check("board has clickable sticks", $("t-board").querySelectorAll("selectable").length === 16,
        `selectable=${$("t-board").querySelectorAll("selectable").length}`);
  check("status names the human", /Ada/.test($("t-status").innerHTML));

  let n = 0;
  while (app.T.live && !app.T.game.over && n++ < 40) {
    const st = app.T.game.history[app.T.game.history.length - 1];
    app.tHumanMove([st.findIndex((x) => x > 0), 1]);
    drain();
  }
  check("the bot replied", entrantCalls > 0, `entrantMove calls=${entrantCalls}`);
  check("human match recorded", app.T.rounds[0][0].done);
  drain();
  check("bracket ran to a champion", app.T.rounds.every((r) => r.every((m) => m.done)));
  check("champion panel shown", !$("t-champion").classList.contains("hidden"));

  console.log("\nplay screen still works after the split");
  app.newGame([3, 5, 7]);
  check("board rendered", sticksIn($("board")) === 15, `sticks=${sticksIn($("board"))}`);
  app.G.seats = ["Human", "Human"];
  app.newGame([1, 1, 1]);
  app.humanMove([0, 1]); app.humanMove([1, 1]); app.humanMove([2, 1]);
  check("game reaches a winner", app.G.gameOver === true && app.G.winnerSeat === 0);

  console.log(`\n${failures ? "FAILED: " + failures + " check(s)" : "all checks passed"}`);
  process.exit(failures ? 1 : 0);
})();
