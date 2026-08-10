// NIM Arena — the Play screen
//
// One free-form game: human or AI in either seat, X-ray, hints, move log,
// timeline scrubbing and shareable replay links.
//
// Loaded as a plain script (not an ES module): the whole app shares one global
// namespace by design, and plain scripts keep working without a bundler.
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

/* ---------------- setup / seats ---------------- */
/* Preferred default opponent, best first — the first one present is used. */
const DEFAULT_OPPONENTS = ["medium", "hard", "easy", "random"];

function populateSeatSelects() {
  const players = window.NIM.players();
  for (const p of players) META.set(p.name, p);
  const names = players.map((p) => p.name);
  const preferred = DEFAULT_OPPONENTS.find((n) => names.includes(n));
  for (const i of [0, 1]) {
    const sel = $(`seat-${i}`);
    sel.innerHTML = "";
    for (const opt of [HUMAN, ...names]) {
      // <option> renders text only — no markup, no SVG — so the icon has to be a
      // glyph and the copy index a Unicode subscript.
      const o = el("option", null, opt === HUMAN ? `${HUMAN_ICON} ${HUMAN}` : playerText(opt));
      o.value = opt;
      const meta = META.get(opt);
      if (meta) o.title = `${meta.description}\nBy: ${meta.authors.join(", ")}`;
      sel.appendChild(o);
    }
    // Default: seat 0 Human, seat 1 a mid-strength bot so a first game is winnable.
    sel.value = i === 1 && preferred ? preferred : HUMAN;
    G.seats[i] = sel.value;
    sel.onchange = () => {
      G.seats[i] = sel.value;
      // Swapping a seat mid-game takes effect on the next turn.
      if (!G.gameOver && isLive()) maybeScheduleAI();
      render();
    };
  }
}

/* Parse the setup inputs. Returns null (after warning) if unplayable. */
function readConfig() {
  const rows = parseInt($("cfg-rows").value) || 0;
  let sticks = $("cfg-sticks").value
    .split(",")
    .map((x) => parseInt(x.trim()))
    .filter((x) => Number.isFinite(x));
  if (rows > 0 && rows <= MAX_ROWS) {
    // Reconcile the row count with the list, but never invent an oversized board.
    while (sticks.length < rows) sticks.push(Math.min(sticks.length + 2, MAX_STICKS_PER_ROW));
    if (sticks.length > rows) sticks = sticks.slice(0, rows);
  }
  const problem = boardProblem(sticks);
  if (problem) {
    toast(problem);
    return null;
  }
  $("cfg-sticks").value = sticks.join(",");
  $("cfg-rows").value = sticks.length;
  return sticks;
}

/* ---------------- game lifecycle ---------------- */
function newGame(startSticks, replayMoves) {
  const requested = startSticks || readConfig();
  // readConfig() already explained why; a caller-supplied board still has to pass.
  if (!requested) return;
  if (startSticks) {
    const problem = boardProblem(startSticks);
    if (problem) {
      toast(problem);
      return;
    }
  }
  clearTimeout(G.aiTimer);
  G.config.sticks = requested;
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
  const state = shown();
  const interactive =
    isLive() && !G.gameOver && !G.thinking && G.seats[seatToMove()] === HUMAN;

  // X-ray target row (perfect player's choice) on the live state.
  let targetRow = -1;
  if (G.showXray && isLive() && !G.gameOver) {
    const an = window.NIM.perfectAnalysis(state);
    if (an.target_row != null) targetRow = an.target_row;
  }

  paintBoard(board, state, { onPick: interactive ? humanMove : null, targetRow });

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


/* ---------------- wiring ---------------- */
function setupPlay() {
  setupTimeline();
  $("btn-new").onclick = guard("New game", () => newGame());
  $("btn-hint").onclick = guard("Hint", hint);
  $("btn-share").onclick = guard("Share", shareLink);
  $("btn-play-ai").onclick = guard("Step", () => {
    clearTimeout(G.aiTimer);
    const name = G.seats[seatToMove()];
    if (name !== HUMAN) runAITurn(name);
  });
  $("cfg-delay").onchange = (e) => { G.delay = parseInt(e.target.value) || 0; };
  $("toggle-xray").onchange = guard("X-ray", (e) => { G.showXray = e.target.checked; render(); });
  $("toggle-why").onchange = (e) => { G.showWhy = e.target.checked; };
}
