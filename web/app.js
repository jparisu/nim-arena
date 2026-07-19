// NIM Arena — thin UI layer. All game rules and AI moves come from Python
// (window.NIM, provided by pyodide-bootstrap.js). JavaScript only renders the
// board, handles clicks, animates, paces AI-vs-AI, and manages the timeline.

"use strict";

const HUMAN = "Human";

const G = {
  config: { sticks: [3, 5, 7] },
  seats: [HUMAN, HUMAN], // seat 0 (first) and seat 1 (second)
  history: [[3, 5, 7]], // states; history[0] is the start
  moves: [], // {seat, move:[r,c], elapsed, info} for each transition
  cursor: 0, // which history index is shown
  gameOver: false,
  winnerSeat: null,
  thinking: false,
  aiTimer: null,
  showXray: false,
  showWhy: true,
  delay: 600,
};

/* ---------------- element helpers ---------------- */
const $ = (id) => document.getElementById(id);
const el = (tag, cls, txt) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (txt != null) e.textContent = txt;
  return e;
};

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

/* ---------------- setup / seats ---------------- */
function populateSeatSelects() {
  const names = window.NIM.playerNames();
  for (const i of [0, 1]) {
    const sel = $(`seat-${i}`);
    sel.innerHTML = "";
    for (const opt of [HUMAN, ...names]) {
      const o = el("option", null, opt);
      o.value = opt;
      sel.appendChild(o);
    }
    // Default: seat 0 Human, seat 1 PerfectBot (if available).
    sel.value = i === 1 && names.includes("PerfectBot") ? "PerfectBot" : HUMAN;
    G.seats[i] = sel.value;
    sel.onchange = () => {
      G.seats[i] = sel.value;
      // Swapping a seat mid-game takes effect on the next turn.
      if (!G.gameOver && isLive()) maybeScheduleAI();
      render();
    };
  }
}

function readConfig() {
  const rows = Math.max(1, Math.min(8, parseInt($("cfg-rows").value) || 1));
  let sticks = $("cfg-sticks").value
    .split(",")
    .map((x) => parseInt(x.trim()))
    .filter((x) => Number.isFinite(x) && x >= 0);
  if (sticks.length < rows) {
    while (sticks.length < rows) sticks.push(sticks.length + 2);
  } else if (sticks.length > rows) {
    sticks = sticks.slice(0, rows);
  }
  if (sticks.every((s) => s === 0)) sticks = sticks.map(() => 1);
  $("cfg-sticks").value = sticks.join(",");
  return sticks;
}

/* ---------------- game lifecycle ---------------- */
function newGame(startSticks, replayMoves) {
  clearTimeout(G.aiTimer);
  G.config.sticks = startSticks || readConfig();
  $("cfg-rows").value = G.config.sticks.length;
  $("cfg-sticks").value = G.config.sticks.join(",");
  G.history = [G.config.sticks.slice()];
  G.moves = [];
  G.cursor = 0;
  G.gameOver = false;
  G.winnerSeat = null;
  G.thinking = false;
  $("why").innerHTML = "";

  if (replayMoves && replayMoves.length) {
    for (const mv of replayMoves) {
      const state = current();
      if (window.NIM.isTerminal(state)) break;
      commitMove(mv, null, false);
    }
    G.cursor = G.history.length - 1;
  }
  render();
  maybeScheduleAI();
}

const current = () => G.history[G.history.length - 1];
const shown = () => G.history[G.cursor];
const isLive = () => G.cursor === G.history.length - 1;
const seatToMove = () => (G.history.length - 1) % 2; // seat 0 moves first

function commitMove(move, meta, animate) {
  const before = current();
  if (!window.NIM.legalMoves(before).some(([r, c]) => r === move[0] && c === move[1])) {
    toast(`Illegal move ${JSON.stringify(move)} — ignored.`);
    return false;
  }
  const seat = seatToMove();
  const after = window.NIM.applyMove(before, move);
  G.history.push(after);
  G.moves.push({ seat, move, elapsed: meta?.elapsed ?? null, info: meta?.info ?? null });
  G.cursor = G.history.length - 1;
  logMove(G.moves[G.moves.length - 1]);

  if (window.NIM.isTerminal(after)) {
    G.gameOver = true;
    G.winnerSeat = seat; // the seat that took the last stick wins
  }
  return true;
}

function humanMove(move) {
  if (G.gameOver || !isLive() || G.thinking) return;
  if (G.seats[seatToMove()] !== HUMAN) return;
  if (commitMove(move, null, true)) {
    render();
    maybeScheduleAI();
  }
}

function maybeScheduleAI() {
  clearTimeout(G.aiTimer);
  if (G.gameOver || !isLive() || G.thinking) return;
  const name = G.seats[seatToMove()];
  if (name === HUMAN) return;
  G.aiTimer = setTimeout(() => runAITurn(name), Math.max(0, G.delay));
}

function runAITurn(name) {
  if (G.gameOver || !isLive()) return;
  if (G.seats[seatToMove()] !== name) return; // seat was swapped
  G.thinking = true;
  render();
  try {
    const res = window.NIM.askMove(name, current());
    G.thinking = false;
    if (!commitMove(res.move, res, true)) {
      toast(`${name} returned an illegal move — stopping.`);
      G.gameOver = true;
    }
  } catch (err) {
    G.thinking = false;
    G.gameOver = true;
    toast(`${name} crashed: ${err}`);
  }
  render();
  maybeScheduleAI();
}

/* ---------------- rendering ---------------- */
function render() {
  renderStatus();
  renderBoard();
  renderXray();
  renderTimeline();
  updateButtons();
}

function seatLabel(i) {
  return `Seat ${i + 1} (${G.seats[i]})`;
}

function renderStatus() {
  const st = $("status");
  if (!isLive()) {
    st.innerHTML = `⏳ Viewing move ${G.cursor} / ${G.moves.length}. ` +
      `<em>Return to the latest move to keep playing.</em>`;
    return;
  }
  if (G.gameOver) {
    st.innerHTML = `🎉 <strong>${seatLabel(G.winnerSeat)}</strong> wins — took the last stick!`;
    return;
  }
  const seat = seatToMove();
  const who = G.seats[seat];
  const chip = seat === 0 ? "chip-a" : "chip-b";
  if (who === HUMAN) {
    st.innerHTML = `<span class="chip ${chip}">${seatLabel(seat)}</span> your turn — click a stick to remove it and everything to its right in that row.`;
  } else {
    st.innerHTML = `<span class="chip ${chip}">${seatLabel(seat)}</span> ${who} is ${G.thinking ? "thinking…" : "up next…"}`;
  }
}

function renderBoard() {
  const board = $("board");
  board.innerHTML = "";
  const state = shown();
  const interactive =
    isLive() && !G.gameOver && !G.thinking && G.seats[seatToMove()] === HUMAN;
  board.classList.toggle("locked", !interactive);

  // X-ray target row (perfect player's choice) on the live state.
  let targetRow = -1;
  if (G.showXray && isLive() && !G.gameOver) {
    const an = window.NIM.perfectAnalysis(state);
    if (an.target_row != null) targetRow = an.target_row;
  }

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
        stick.addEventListener("click", () => humanMove([row, removeCount]));
      }
      rowEl.appendChild(stick);
    }
    rowEl.appendChild(el("span", "row-count", count === 0 ? "(empty)" : `${count}`));
    board.appendChild(rowEl);
  });

  const old = board.parentElement.querySelector(".win-banner");
  if (old) old.remove();
  if (G.gameOver && isLive()) {
    const banner = el("div", "win-banner", `🏆 ${seatLabel(G.winnerSeat)} wins!`);
    board.after(banner);
  }
}

function renderXray() {
  const box = $("xray");
  if (!G.showXray) { box.classList.add("hidden"); return; }
  box.classList.remove("hidden");
  const state = shown();
  const ns = window.NIM.nimSum(state);
  const binary = state.map((x) => x.toString(2)).join(" ⊕ ");
  if (window.NIM.isTerminal(state)) {
    box.innerHTML = `<strong>X-ray:</strong> board empty — game over.`;
    return;
  }
  const an = window.NIM.perfectAnalysis(state);
  let advice;
  if (ns === 0) {
    advice = `nim-sum is <span class="ns">0</span> → the player to move is <strong>losing</strong> under perfect play (can only stall).`;
  } else {
    advice = `nim-sum is <span class="ns">${ns}</span> → the player to move can <strong>force a win</strong>` +
      (an.move ? ` by playing <strong>row ${an.move[0]}, remove ${an.move[1]}</strong> (highlighted).` : ".");
  }
  box.innerHTML = `<strong>X-ray:</strong> ${binary} = <span class="ns">${ns}</span>. ${advice}`;
}

function logMove(m) {
  if (!G.showWhy) return;
  const cls = m.seat === 0 ? "a" : "b";
  const entry = el("div", `why-entry ${cls}`);
  const head = el("div", "head");
  head.appendChild(el("span", null, `${seatLabel(m.seat)} · row ${m.move[0]} −${m.move[1]}`));
  head.appendChild(el("span", "time", m.elapsed != null ? `${m.elapsed.toFixed(1)} ms` : "human"));
  entry.appendChild(head);
  if (m.info && m.info.note) {
    const note = el("div", "note", m.info.note);
    entry.appendChild(note);
    const bits = [];
    if (m.info.depth != null) bits.push(`depth ${m.info.depth}`);
    if (m.info.score != null) bits.push(`score ${Number(m.info.score).toFixed(2)}`);
    if (m.info.nodes != null) bits.push(`${m.info.nodes} nodes`);
    if (m.info.nim_sum_before != null)
      bits.push(`nim-sum ${m.info.nim_sum_before} → ${m.info.nim_sum_after}`);
    if (bits.length) entry.appendChild(el("div", "note", bits.join(" · ")));
  }
  const body = $("why");
  body.insertBefore(entry, body.firstChild);
}

/* ---------------- timeline ---------------- */
function renderTimeline() {
  const slider = $("tl-slider");
  slider.max = G.history.length - 1;
  slider.value = G.cursor;
  $("tl-label").textContent = `move ${G.cursor} / ${G.history.length - 1}`;
}

function gotoCursor(idx) {
  G.cursor = Math.max(0, Math.min(G.history.length - 1, idx));
  clearTimeout(G.aiTimer);
  render();
  if (isLive()) maybeScheduleAI(); // returning to live resumes AI play
}

function setupTimeline() {
  $("tl-first").onclick = () => gotoCursor(0);
  $("tl-prev").onclick = () => gotoCursor(G.cursor - 1);
  $("tl-next").onclick = () => gotoCursor(G.cursor + 1);
  $("tl-last").onclick = () => gotoCursor(G.history.length - 1);
  $("tl-slider").oninput = (e) => gotoCursor(parseInt(e.target.value));
}

/* ---------------- buttons ---------------- */
function updateButtons() {
  const humanTurn = isLive() && !G.gameOver && G.seats[seatToMove()] === HUMAN;
  $("btn-hint").disabled = !humanTurn;
  const aiTurn = isLive() && !G.gameOver && G.seats[seatToMove()] !== HUMAN;
  $("btn-play-ai").disabled = !aiTurn;
}

function hint() {
  const an = window.NIM.perfectAnalysis(current());
  if (an.move) {
    toast(`Optimal: row ${an.move[0]}, remove ${an.move[1]} (nim-sum → 0).`);
    const rows = $("board").querySelectorAll(".row");
    rows[an.move[0]]?.classList.add("target");
    setTimeout(() => rows[an.move[0]]?.classList.remove("target"), 1500);
  } else {
    toast("nim-sum is 0 — you're theoretically losing. Stall and hope!");
  }
}

/* ---------------- share / replay ---------------- */
function shareLink() {
  const payload = {
    s: G.history[0],
    seats: G.seats,
    m: G.moves.map((x) => x.move),
  };
  const hash = "#g=" + btoa(unescape(encodeURIComponent(JSON.stringify(payload))));
  const url = location.origin + location.pathname + hash;
  navigator.clipboard?.writeText(url).then(
    () => toast("Replay link copied to clipboard!"),
    () => toast("Copy failed — link is in the address bar."),
  );
  history.replaceState(null, "", hash);
}

function loadFromHash() {
  if (!location.hash.startsWith("#g=")) return false;
  try {
    const payload = JSON.parse(decodeURIComponent(escape(atob(location.hash.slice(3)))));
    for (const i of [0, 1]) {
      if (payload.seats?.[i]) {
        $(`seat-${i}`).value = payload.seats[i];
        G.seats[i] = payload.seats[i];
      }
    }
    newGame(payload.s, payload.m || []);
    showScreen("game");
    toast("Loaded a shared replay.");
    return true;
  } catch (err) {
    toast("Could not read the shared link.");
    return false;
  }
}

/* ---------------- scoreboard ---------------- */
const MEDALS = { 1: "🥇", 2: "🥈", 3: "🥉" };
const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmtMs = (v) => (v == null ? "—" : `${Number(v).toFixed(v < 10 ? 3 : 1)} ms`);
const MODE_LABEL = { simple: "Simple", league: "League", championship: "Championship" };
const MODE_BLURB = {
  simple: "Every pair plays one match; players are ranked by points (one per win).",
  league: "Every pair plays one match; players are ranked by their Elo rating.",
  championship: "A group phase (round-robin, top two advance) then a knockout bracket.",
};

async function loadScoreboard() {
  const meta = $("sb-meta");
  const layout = $("sb-layout");
  const empty = $("sb-empty");
  try {
    const resp = await fetch("leaderboard.json", { cache: "no-cache" });
    if (!resp.ok) throw new Error("not found");
    const data = await resp.json();
    empty.classList.add("hidden");
    layout.classList.remove("hidden");
    renderScoreboard(data);
  } catch {
    layout.classList.add("hidden");
    empty.classList.remove("hidden");
    empty.textContent =
      "No leaderboard yet. Run the tournament (`nim-tournament`) or the tournament workflow to generate results/leaderboard.json.";
    meta.textContent = "";
  }
}

function renderScoreboard(data) {
  const cfg = data.config || {};
  const mode = cfg.tournament || "simple";
  const useElo = !!cfg.elo;

  $("sb-title").textContent = `${MODE_LABEL[mode] || "Tournament"} results`;
  $("sb-meta").textContent =
    `Generated ${data.generated_at} · ${MODE_LABEL[mode] || mode} · ` +
    `${cfg.player_repetition ?? "?"} per kind · ${cfg.repetitions ?? "?"} reps/board · ` +
    `boards ${JSON.stringify(cfg.starting_states)} · ` +
    `time limit ${cfg.time_limit_s != null ? cfg.time_limit_s + " s" : (cfg.move_timeout_ms + " ms")}`;

  renderStandings(data.standings || [], useElo);
  renderStructure(data, mode);
  renderMatches(data.matches || []);
  renderPlayerStats(data.player_stats || [], useElo);
  renderTotals(data.totals || {});
}

/* Right-wing classification column. */
function renderStandings(standings, useElo) {
  $("sb-class-title").textContent = useElo ? "Classification · Elo" : "Classification · points";
  const ol = $("sb-standings");
  ol.innerHTML = "";
  for (const row of standings) {
    const li = el("li", `sb-rank rank-${row.rank}`);
    const score = useElo ? Math.round(row.elo) : `${row.points} pts`;
    li.innerHTML =
      `<span class="sb-rank-no">${MEDALS[row.rank] || row.rank}</span>` +
      `<span class="sb-rank-name">${esc(row.player)}</span>` +
      `<span class="sb-rank-score">${esc(score)}</span>` +
      `<span class="sb-rank-wl">${row.wins}–${row.losses}` +
      `${row.forfeits ? ` · ${row.forfeits} ff` : ""}</span>`;
    ol.appendChild(li);
  }
}

/* Tournament structure block (mode-dependent). */
function renderStructure(data, mode) {
  $("sb-structure-sub").textContent = MODE_LABEL[mode] || mode;
  const box = $("sb-structure");
  box.innerHTML = "";
  box.appendChild(el("p", "muted", MODE_BLURB[mode] || ""));

  const struct = data.structure || {};
  if (mode !== "championship") {
    const t = data.totals || {};
    box.appendChild(el("p", null,
      `${t.players ?? "?"} players · ${t.matches ?? "?"} matches · ${t.games ?? "?"} games.`));
    return;
  }

  // Group phase
  const groupsWrap = el("div", "sb-groups");
  for (const g of struct.groups || []) {
    const card = el("div", "sb-group");
    card.appendChild(el("h4", null, g.name));
    const table = el("table", "sb-mini");
    table.innerHTML =
      "<thead><tr><th>#</th><th>Player</th><th>Pts</th><th>W</th><th>L</th></tr></thead>";
    const tb = el("tbody");
    for (const r of g.table) {
      const advanced = (g.advance || []).includes(r.player);
      const tr = el("tr", advanced ? "advances" : null);
      tr.innerHTML =
        `<td>${r.rank}</td><td>${esc(r.player)}${advanced ? " ⬆" : ""}</td>` +
        `<td>${r.points}</td><td>${r.wins}</td><td>${r.losses}</td>`;
      tb.appendChild(tr);
    }
    table.appendChild(tb);
    card.appendChild(table);
    groupsWrap.appendChild(card);
  }
  box.appendChild(el("h4", "sb-phase-title", "Group phase"));
  box.appendChild(groupsWrap);

  // Knockout bracket
  const bracket = struct.bracket || {};
  box.appendChild(el("h4", "sb-phase-title", "Knockout bracket"));
  const brWrap = el("div", "sb-bracket");
  for (const round of bracket.rounds || []) {
    const col = el("div", "sb-round");
    col.appendChild(el("div", "sb-round-name", round.name));
    for (const tie of round.ties) {
      const card = el("div", "sb-tie");
      card.appendChild(tieSide(tie.a, tie.a_wins, tie.winner === tie.a, tie.b == null));
      card.appendChild(tieSide(tie.b, tie.b_wins, tie.winner === tie.b, false));
      col.appendChild(card);
    }
    brWrap.appendChild(col);
  }
  box.appendChild(brWrap);
  if (bracket.champion) {
    box.appendChild(el("div", "sb-champion", `🏆 Champion: ${bracket.champion}`));
  }
}

function tieSide(name, wins, isWinner, isBye) {
  const row = el("div", `sb-tie-side${isWinner ? " won" : ""}`);
  if (name == null) {
    row.appendChild(el("span", "sb-tie-name muted", "— bye —"));
    return row;
  }
  row.appendChild(el("span", "sb-tie-name", name));
  if (!isBye) row.appendChild(el("span", "sb-tie-score", String(wins)));
  return row;
}

/* Match summary — one row per match, averaged over its games. */
function renderMatches(matches) {
  $("sb-matches-sub").textContent = `${matches.length} matches`;
  const box = $("sb-matches");
  box.innerHTML = "";
  const table = el("table", "sb-table");
  table.innerHTML =
    "<thead><tr><th>Phase</th><th>Match</th><th>Score</th><th>Winner</th>" +
    "<th>Games</th><th>Avg A</th><th>Avg B</th></tr></thead>";
  const tb = el("tbody");
  for (const m of matches) {
    const tr = el("tr");
    const score = `${m.a_wins}–${m.b_wins}`;
    tr.innerHTML =
      `<td class="muted">${esc(m.phase)}</td>` +
      `<td>${esc(m.player_a)} <span class="muted">vs</span> ${esc(m.player_b)}</td>` +
      `<td class="num">${score}</td>` +
      `<td>${m.winner ? esc(m.winner) : "<span class='muted'>tie</span>"}</td>` +
      `<td class="num">${m.games}</td>` +
      `<td class="num">${fmtMs(m.a_avg_move_ms)}</td>` +
      `<td class="num">${fmtMs(m.b_avg_move_ms)}</td>`;
    tb.appendChild(tr);
  }
  table.appendChild(tb);
  const wrap = el("div", "table-wrap");
  wrap.appendChild(table);
  box.appendChild(wrap);
}

/* Player stats — per-player card with head-to-head breakdown. */
function renderPlayerStats(stats, useElo) {
  $("sb-players-sub").textContent = `${stats.length} players`;
  const box = $("sb-playerstats");
  box.innerHTML = "";
  for (const s of stats) {
    const d = el("details", "sb-player");
    const summary = el("summary");
    summary.innerHTML =
      `<span class="sb-player-name">${esc(s.player)}</span>` +
      `<span class="sb-player-quick">${s.wins}–${s.losses}` +
      `${useElo ? ` · elo ${Math.round(s.elo)}` : ""} · ${(s.win_rate * 100).toFixed(0)}%</span>`;
    d.appendChild(summary);

    const body = el("div", "sb-player-body");
    const tiles = el("div", "sb-tiles");
    tiles.appendChild(statTile("Win rate", `${(s.win_rate * 100).toFixed(0)}%`));
    tiles.appendChild(statTile("Wins / Losses", `${s.wins} / ${s.losses}`));
    tiles.appendChild(statTile("Forfeits", String(s.forfeits)));
    tiles.appendChild(statTile("Avg move", fmtMs(s.avg_move_ms)));
    tiles.appendChild(statTile("Max move", fmtMs(s.max_move_ms)));
    tiles.appendChild(statTile("Moves made", String(s.moves_made)));
    if (useElo) tiles.appendChild(statTile("Elo", String(Math.round(s.elo))));
    body.appendChild(tiles);

    if (s.opponents && s.opponents.length) {
      const oppTable = el("table", "sb-mini");
      oppTable.innerHTML = "<thead><tr><th>Opponent</th><th>W</th><th>L</th></tr></thead>";
      const tb = el("tbody");
      for (const o of s.opponents) {
        const tr = el("tr");
        tr.innerHTML = `<td>${esc(o.opponent)}</td><td>${o.wins}</td><td>${o.losses}</td>`;
        tb.appendChild(tr);
      }
      oppTable.appendChild(tb);
      body.appendChild(el("h5", "sb-h2h", "Head-to-head"));
      body.appendChild(oppTable);
    }
    d.appendChild(body);
    box.appendChild(d);
  }
}

/* Total stats — overview tiles. */
function renderTotals(t) {
  $("sb-totals-sub").textContent = `${t.games ?? "?"} games`;
  const box = $("sb-totals");
  box.innerHTML = "";
  const tiles = el("div", "sb-tiles");
  tiles.appendChild(statTile("Players", String(t.players ?? "—")));
  tiles.appendChild(statTile("Matches", String(t.matches ?? "—")));
  tiles.appendChild(statTile("Games", String(t.games ?? "—")));
  tiles.appendChild(statTile("Total moves", String(t.total_moves ?? "—")));
  tiles.appendChild(statTile("Avg game length", `${t.avg_game_moves ?? "—"} moves`));
  tiles.appendChild(statTile("Longest game", `${t.longest_game_moves ?? "—"} moves`));
  tiles.appendChild(statTile("Forfeits", String(t.forfeits ?? "—")));
  tiles.appendChild(statTile("Total think time",
    t.total_move_time_ms != null ? `${(t.total_move_time_ms / 1000).toFixed(2)} s` : "—"));
  box.appendChild(tiles);
}

function statTile(label, value) {
  const tile = el("div", "sb-tile");
  tile.appendChild(el("div", "sb-tile-value", value));
  tile.appendChild(el("div", "sb-tile-label", label));
  return tile;
}

/* ---------------- init ---------------- */
async function main() {
  setupNav();
  setupTimeline();
  $("btn-new").onclick = () => newGame();
  $("btn-hint").onclick = hint;
  $("btn-share").onclick = shareLink;
  $("btn-play-ai").onclick = () => {
    clearTimeout(G.aiTimer);
    const name = G.seats[seatToMove()];
    if (name !== HUMAN) runAITurn(name);
  };
  $("cfg-delay").onchange = (e) => { G.delay = parseInt(e.target.value) || 0; };
  $("toggle-xray").onchange = (e) => { G.showXray = e.target.checked; render(); };
  $("toggle-why").onchange = (e) => { G.showWhy = e.target.checked; };

  try {
    await window.bootNim((msg) => { $("boot-status").textContent = msg; });
  } catch (err) {
    $("boot-status").textContent = "⚠️ " + err.message;
    return;
  }

  populateSeatSelects();
  $("boot").classList.add("hidden");

  if (!loadFromHash()) {
    newGame([3, 5, 7]);
    showScreen("menu");
  }
}

window.addEventListener("DOMContentLoaded", main);
