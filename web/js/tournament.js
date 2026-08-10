// NIM Arena — the Tournament screen
//
// A user-configured single-elimination bracket. Scheduling and drawing only —
// every move comes from Python via window.NIM.
//
// Loaded as a plain script (not an ES module): the whole app shares one global
// namespace by design, and plain scripts keep working without a bundler.
"use strict";

const HUMAN_KIND = "__human__";
/* Mirrors nimarena.tournament._seed_for_game: fold the tournament seed and the
   slot index together so every entrant is seeded distinctly, yet a given
   (seed, bracket) always reproduces the same tournament. */
const SEED_STRIDE = 1000003;
/* Pause between automatic bot-vs-bot matches, so the bracket visibly advances. */
const AUTO_MATCH_MS = 550;

const T = {
  size: 8,
  seed: 1,
  board: [1, 3, 5, 7],
  slots: [],      // {id, kind, label, icon}
  rounds: [],     // [[{a, b, winner, moves, result, detail, done}]]
  view: null,     // {r, m} match being replayed
  live: null,     // {r, m} human match in progress
  game: null,     // {history, cursor, turn, over, winnerSeat}
  timer: null,
};

const ROUND_NAME = { 1: "Final", 2: "Semifinals", 4: "Quarterfinals", 8: "Round of 16" };

/* ---------------- setup ---------------- */

function tKinds() {
  return (window.NIM?.players?.() || []).map((p) => p.name);
}

/* Render a slot with its icon, and its copy index as a subscript when the same
   kind or name entered the bracket more than once. */
function tSlotHtml(slot) {
  if (!slot) return `<span class="muted">—</span>`;
  const display = slot.display || (slot.kind === HUMAN_KIND ? slot.label : slot.kind);
  if (slot.kind !== HUMAN_KIND) return playerHtml(display);
  const [base, idx] = splitPlayer(display);
  return (
    `<span class="p-icon">${HUMAN_ICON}</span>` +
    `<span class="p-name">${esc(base)}${idx == null ? "" : `<sub>${esc(idx)}</sub>`}</span>`
  );
}

function tBuildSetup() {
  const kinds = tKinds();
  const size = parseInt($("t-size").value) || 8;
  const box = $("t-slots");
  const previous = T.slots;
  box.innerHTML = "";
  T.slots = [];

  for (let i = 0; i < size; i++) {
    const prev = previous[i];
    const slot = {
      id: `slot${i}`,
      kind: prev?.kind ?? (kinds[i % Math.max(1, kinds.length)] || HUMAN_KIND),
      label: prev?.label ?? `Player ${i + 1}`,
    };
    T.slots.push(slot);

    const row = el("div", "tslot");
    row.appendChild(el("span", "tslot-no", `${i + 1}`));

    const sel = el("select", "tslot-kind");
    for (const opt of [HUMAN_KIND, ...kinds]) {
      const o = el("option", null, opt === HUMAN_KIND ? `${HUMAN_ICON} Human` : playerText(opt));
      o.value = opt;
      sel.appendChild(o);
    }
    sel.value = slot.kind;

    const nameInput = el("input", "tslot-name");
    nameInput.type = "text";
    nameInput.value = slot.label;
    nameInput.placeholder = "Name";
    const syncName = () => {
      const human = sel.value === HUMAN_KIND;
      nameInput.classList.toggle("hidden", !human);
    };
    sel.onchange = () => { slot.kind = sel.value; syncName(); };
    nameInput.oninput = () => { slot.label = nameInput.value.trim() || `Player ${i + 1}`; };
    syncName();

    row.appendChild(sel);
    row.appendChild(nameInput);
    box.appendChild(row);
  }
}

function tRandomise() {
  const kinds = tKinds();
  if (!kinds.length) return;
  for (const [i, sel] of [...$("t-slots").querySelectorAll(".tslot-kind")].entries()) {
    const pick = kinds[Math.floor(Math.random() * kinds.length)];
    sel.value = pick;
    T.slots[i].kind = pick;
    sel.dispatchEvent(new Event("change"));
  }
}

/* ---------------- bracket construction ---------------- */

function tStart() {
  const board = $("t-start-board").value
    .split(",")
    .map((x) => parseInt(x.trim()))
    .filter(Number.isFinite);
  const problem = boardProblem(board);
  if (problem) { toast(problem); return; }

  const seed = parseInt($("t-seed").value);
  if (!Number.isFinite(seed) || seed < 0) { toast("The seed must be a whole number, 0 or more."); return; }

  T.board = board;
  T.seed = seed;
  T.size = T.slots.length;

  // Make every display name unique, so the bracket stays readable when a kind
  // (or a human name) is entered more than once. A name used once is left alone;
  // duplicates get the same _0/_1 suffix the real tournament uses.
  const base = (slot) => (slot.kind === HUMAN_KIND ? slot.label : slot.kind);
  const totals = new Map();
  for (const slot of T.slots) totals.set(base(slot), (totals.get(base(slot)) || 0) + 1);
  const used = new Map();
  for (const slot of T.slots) {
    const b = base(slot);
    if (totals.get(b) === 1) { slot.display = b; continue; }
    const n = used.get(b) || 0;
    used.set(b, n + 1);
    slot.display = `${b}_${n}`;
  }

  // One independent, seeded instance per slot.
  window.NIM.resetEntrants();
  T.slots.forEach((slot, i) => {
    if (slot.kind !== HUMAN_KIND) {
      window.NIM.createEntrant(slot.id, slot.kind, T.seed * SEED_STRIDE + i);
    }
  });

  // Round 0 pairs adjacent slots, which is what the drawn tree shows.
  T.rounds = [];
  let entrants = T.slots.slice();
  while (entrants.length > 1) {
    const round = [];
    for (let i = 0; i < entrants.length; i += 2) {
      round.push({ a: entrants[i], b: entrants[i + 1], winner: null,
                   moves: [], result: null, detail: "", done: false });
    }
    T.rounds.push(round);
    entrants = round.map(() => null);
  }

  T.view = null;
  T.live = null;
  T.game = null;
  $("t-setup").classList.add("hidden");
  $("t-reset").classList.remove("hidden");
  $("t-bracket-wrap").classList.remove("hidden");
  $("t-champion").classList.add("hidden");
  $("t-champion").innerHTML = "";
  tRenderBracket();
  tAdvance();
}

function tReset() {
  clearTimeout(T.timer);
  T.rounds = [];
  T.view = T.live = T.game = null;
  $("t-setup").classList.remove("hidden");
  $("t-reset").classList.add("hidden");
  $("t-bracket-wrap").classList.add("hidden");
  $("t-match").classList.add("hidden");
  $("t-champion").classList.add("hidden");
  $("t-champion").innerHTML = "";
  tBuildSetup();
}

/* ---------------- scheduling ---------------- */

/* The next match with both entrants known and no winner yet. */
function tNextMatch() {
  for (let r = 0; r < T.rounds.length; r++) {
    for (let m = 0; m < T.rounds[r].length; m++) {
      const match = T.rounds[r][m];
      if (!match.done && match.a && match.b) return { r, m };
    }
  }
  return null;
}

function tAdvance() {
  if (T.live) return;                       // waiting on a human
  const next = tNextMatch();
  if (!next) { tFinish(); return; }
  const match = T.rounds[next.r][next.m];
  const humans = [match.a, match.b].filter((s) => s.kind === HUMAN_KIND).length;

  if (humans === 0) {
    // Bot vs bot: Python plays the whole game in one call.
    const res = window.NIM.playAuto(match.a.id, match.b.id, T.board);
    tRecord(next, res.winner_seat, res.moves, res.result, res.detail);
    tRenderBracket();
    T.timer = setTimeout(tAdvance, AUTO_MATCH_MS);
    return;
  }
  tOpenLiveMatch(next);
}

function tRecord({ r, m }, winnerSeat, moves, result, detail) {
  const match = T.rounds[r][m];
  match.moves = moves;
  match.result = result;
  match.detail = detail || "";
  match.winner = winnerSeat === 0 ? match.a : match.b;
  match.done = true;
  // Promote the winner into the next round.
  const next = T.rounds[r + 1];
  if (next) {
    const slotIdx = Math.floor(m / 2);
    if (m % 2 === 0) next[slotIdx].a = match.winner;
    else next[slotIdx].b = match.winner;
  }
}

/* ---------------- a live match involving a human ---------------- */

function tOpenLiveMatch(at) {
  T.live = at;
  T.view = null;
  const match = T.rounds[at.r][at.m];
  T.game = { history: [T.board.slice()], moves: [], cursor: 0, turn: 0,
             over: false, winnerSeat: null };
  $("t-match").classList.remove("hidden");
  $("t-close-view").classList.add("hidden");
  $("t-timeline").classList.add("hidden");
  $("t-match-title").innerHTML =
    `${tSlotHtml(match.a)} <span class="muted">vs</span> ${tSlotHtml(match.b)}`;
  $("t-match-sub").textContent = `${tRoundName(at.r)} · board ${T.board.join(",")}`;
  $("t-match").scrollIntoView({ behavior: "smooth", block: "nearest" });
  tRenderLive();
  tMaybeBotTurn();
}

function tCurrent() { return T.game.history[T.game.history.length - 1]; }

function tSeatSlot(seat) {
  const match = T.rounds[T.live.r][T.live.m];
  return seat === 0 ? match.a : match.b;
}

function tRenderLive() {
  const g = T.game;
  const state = g.history[g.cursor];
  const live = g.cursor === g.history.length - 1;
  const mySlot = g.over ? null : tSeatSlot(g.turn);
  const interactive = live && !g.over && mySlot && mySlot.kind === HUMAN_KIND;

  paintBoard($("t-board"), state, {
    onPick: interactive ? tHumanMove : null,
  });

  const status = $("t-status");
  if (g.over) {
    const w = tSeatSlot(g.winnerSeat);
    status.innerHTML = `🏆 ${tSlotHtml(w)} takes the last stick and wins.`;
  } else {
    const chip = g.turn === 0 ? "chip-a" : "chip-b";
    status.innerHTML =
      `<span class="chip ${chip}">${g.turn === 0 ? "first" : "second"}</span> ` +
      (mySlot.kind === HUMAN_KIND
        ? `${tSlotHtml(mySlot)} — your turn.`
        : `${tSlotHtml(mySlot)} is thinking…`);
  }
}

function tApply(move) {
  const g = T.game;
  const before = tCurrent();
  const after = window.NIM.applyMove(before, move);
  g.history.push(after);
  g.cursor = g.history.length - 1;
  g.moves.push(move);
  if (window.NIM.isTerminal(after)) {
    g.over = true;
    g.winnerSeat = g.turn;      // the seat that just took the last stick
  } else {
    g.turn = 1 - g.turn;
  }
}

function tHumanMove(move) {
  const g = T.game;
  if (g.over || g.cursor !== g.history.length - 1) return;
  const legal = window.NIM.legalMoves(tCurrent())
    .some(([r, c]) => r === move[0] && c === move[1]);
  if (!legal) { toast("Illegal move — ignored."); return; }
  tApply(move);
  tRenderLive();
  if (g.over) tFinishLiveMatch(); else tMaybeBotTurn();
}

function tMaybeBotTurn() {
  const g = T.game;
  if (g.over) return;
  const slot = tSeatSlot(g.turn);
  if (slot.kind === HUMAN_KIND) return;
  T.timer = setTimeout(() => {
    try {
      const res = window.NIM.entrantMove(slot.id, tCurrent());
      tApply(res.move);
    } catch (err) {
      // A misbehaving bot forfeits rather than wedging the bracket.
      toast(`${slot.display} failed: ${err}`);
      g.over = true;
      g.winnerSeat = 1 - g.turn;
    }
    tRenderLive();
    if (g.over) tFinishLiveMatch(); else tMaybeBotTurn();
  }, Math.max(150, G.delay));
}

function tFinishLiveMatch() {
  const at = T.live;
  tRecord(at, T.game.winnerSeat, T.game.moves || [], "normal", "");
  T.live = null;
  tRenderBracket();
  T.timer = setTimeout(() => {
    $("t-match").classList.add("hidden");
    tAdvance();
  }, 1200);
}

/* ---------------- replaying a finished match ---------------- */

function tViewMatch(r, m) {
  const match = T.rounds[r][m];
  if (!match.done || T.live) return;
  T.view = { r, m };
  const states = [T.board.slice()];
  for (const mv of match.moves) states.push(window.NIM.applyMove(states[states.length - 1], mv));
  T.game = { history: states, cursor: states.length - 1, turn: 0, over: true,
             winnerSeat: match.winner === match.a ? 0 : 1 };

  $("t-match").classList.remove("hidden");
  $("t-close-view").classList.remove("hidden");
  $("t-timeline").classList.remove("hidden");
  $("t-match-title").innerHTML =
    `${tSlotHtml(match.a)} <span class="muted">vs</span> ${tSlotHtml(match.b)}`;
  const how = match.result && match.result !== "normal" ? ` · ${match.result}` : "";
  $("t-match-sub").textContent =
    `${tRoundName(r)} · ${match.moves.length} moves${how}${match.detail ? " · " + match.detail : ""}`;

  const slider = $("t-tl-slider");
  slider.min = 0;
  slider.max = states.length - 1;
  slider.value = states.length - 1;
  slider.oninput = () => { T.game.cursor = parseInt(slider.value); tRenderReplay(); };
  tRenderReplay();
  $("t-match").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function tRenderReplay() {
  const g = T.game;
  const match = T.rounds[T.view.r][T.view.m];
  paintBoard($("t-board"), g.history[g.cursor], { onPick: null });
  $("t-tl-slider").value = g.cursor;
  $("t-tl-label").textContent = `move ${g.cursor} / ${g.history.length - 1}`;
  $("t-status").innerHTML =
    g.cursor === g.history.length - 1
      ? `🏆 ${tSlotHtml(match.winner)} won this match.`
      : `Showing move ${g.cursor}. ${tSlotHtml(g.cursor % 2 === 0 ? match.a : match.b)} to play.`;
}

function tCloseView() {
  T.view = null;
  $("t-match").classList.add("hidden");
  tRenderBracket();
}

/* ---------------- the tree ---------------- */

function tRoundName(r) {
  return ROUND_NAME[T.rounds[r].length] || `Round ${r + 1}`;
}

function tRenderBracket() {
  const wrap = $("t-bracket");
  wrap.innerHTML = "";
  const total = T.rounds.reduce((n, rd) => n + rd.length, 0);
  const done = T.rounds.reduce((n, rd) => n + rd.filter((x) => x.done).length, 0);
  $("t-progress").textContent = `${done} / ${total} matches played`;

  T.rounds.forEach((round, r) => {
    const col = el("div", "sb-round");
    col.appendChild(el("div", "sb-round-name", tRoundName(r)));
    round.forEach((match, m) => {
      const card = el("div", "sb-tie t-tie");
      const next = tNextMatch();
      if (next && next.r === r && next.m === m && !match.done) card.classList.add("t-next");
      if (T.view && T.view.r === r && T.view.m === m) card.classList.add("t-viewing");
      card.appendChild(tTieSide(match, match.a));
      card.appendChild(tTieSide(match, match.b));
      if (match.done) {
        card.classList.add("t-done");
        card.title = "Click to replay this match";
        card.onclick = () => tViewMatch(r, m);
      }
      col.appendChild(card);
    });
    wrap.appendChild(col);
  });
}

function tTieSide(match, slot) {
  const won = match.done && match.winner === slot;
  const row = el("div", `sb-tie-side${won ? " won" : ""}`);
  const name = el("span", "sb-tie-name");
  name.innerHTML = slot ? tSlotHtml(slot) : `<span class="muted">—</span>`;
  row.appendChild(name);
  if (match.done) row.appendChild(el("span", "sb-tie-score", won ? "W" : "L"));
  return row;
}

/* ---------------- champion ---------------- */

function tFinish() {
  const final = T.rounds[T.rounds.length - 1][0];
  if (!final?.done) return;
  const champion = final.winner;
  const runnerUp = final.winner === final.a ? final.b : final.a;
  // No third-place match in a single-elimination bracket, so both losing
  // semi-finalists share the bronze. Stating that is better than inventing a rank.
  const semis = T.rounds.length >= 2
    ? T.rounds[T.rounds.length - 2].map((mt) => (mt.winner === mt.a ? mt.b : mt.a)).filter(Boolean)
    : [];

  const box = $("t-champion");
  box.classList.remove("hidden");
  box.innerHTML =
    `<div class="confetti" aria-hidden="true">${
      Array.from({ length: 28 }, (_, i) =>
        `<span style="--i:${i};--h:${(i * 37) % 360}">${["🎉", "🎊", "✨", "🏆"][i % 4]}</span>`
      ).join("")
    }</div>` +
    `<div class="tchampion-card">` +
    `<div class="tchampion-crown">🏆</div>` +
    `<h2>${tSlotHtml(champion)} wins the tournament!</h2>` +
    `<div class="podium">` +
    `<div class="podium-step silver"><div class="podium-medal">🥈</div>` +
    `<div class="podium-name">${tSlotHtml(runnerUp)}</div><div class="podium-block">2</div></div>` +
    `<div class="podium-step gold"><div class="podium-medal">🥇</div>` +
    `<div class="podium-name">${tSlotHtml(champion)}</div><div class="podium-block">1</div></div>` +
    `<div class="podium-step bronze"><div class="podium-medal">🥉</div>` +
    `<div class="podium-name">${semis.map(tSlotHtml).join('<span class="muted"> · </span>') || "—"}</div>` +
    `<div class="podium-block">3</div></div>` +
    `</div>` +
    `<p class="muted small">Seed ${T.seed} · board ${T.board.join(",")} · ` +
    `${T.rounds.reduce((n, rd) => n + rd.length, 0)} matches. Click any match above to replay it.</p>` +
    `</div>`;
  box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/* ---------------- wiring ---------------- */

function setupTournament() {
  // The slot list is NOT built here: it needs the engine's player list, so
  // main() calls tBuildSetup() once boot finishes. Wiring must not depend on
  // anything that can fail, or a dead button is the result.
  $("t-size").onchange = guard("Bracket size", tBuildSetup);
  $("t-start").onclick = guard("Start tournament", tStart);
  $("t-reset").onclick = guard("New bracket", tReset);
  $("t-shuffle").onclick = guard("Randomise", tRandomise);
  $("t-close-view").onclick = guard("Back to bracket", tCloseView);
  const step = (d) => () => {
    if (!T.view) return;
    T.game.cursor = Math.max(0, Math.min(T.game.history.length - 1, T.game.cursor + d));
    tRenderReplay();
  };
  $("t-tl-prev").onclick = guard("Previous move", step(-1));
  $("t-tl-next").onclick = guard("Next move", step(1));
  $("t-tl-first").onclick = guard("First move", () => { if (T.view) { T.game.cursor = 0; tRenderReplay(); } });
  $("t-tl-last").onclick = guard("Last move", () => {
    if (T.view) { T.game.cursor = T.game.history.length - 1; tRenderReplay(); }
  });
}
