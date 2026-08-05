// Loads Pyodide, mounts the shared Python package, and exposes a small JS API
// (`window.NIM`) over the Python `webglue` bridge. All game rules and AI moves
// come from Python — JavaScript never re-implements the rules.

const PYODIDE_VERSION = "0.26.2";
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const MOUNT = "/lib/nimsite";

// Load the Pyodide loader script from the CDN.
function loadPyodideScript() {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = `${PYODIDE_CDN}pyodide.js`;
    s.onload = resolve;
    s.onerror = () => reject(new Error("Failed to load Pyodide from the CDN"));
    document.head.appendChild(s);
  });
}

// Boot Pyodide, unpack py.zip into the virtual FS, import webglue, load players.
async function bootNim(onStatus = () => {}) {
  onStatus("Loading Pyodide…");
  await loadPyodideScript();
  const pyodide = await loadPyodide({ indexURL: PYODIDE_CDN });

  onStatus("Loading PyYAML…");
  await pyodide.loadPackage("pyyaml");

  onStatus("Fetching the Python code…");
  const resp = await fetch("py.zip", { cache: "no-cache" });
  if (!resp.ok) {
    throw new Error(
      "Could not fetch py.zip. Run `python scripts/build_web.py` first."
    );
  }
  const buffer = await resp.arrayBuffer();

  onStatus("Mounting the game engine…");
  pyodide.FS.mkdirTree(MOUNT);
  await pyodide.unpackArchive(buffer, "zip", { extractDir: MOUNT });
  pyodide.runPython(`import sys; sys.path.insert(0, "${MOUNT}")`);

  onStatus("Registering players…");
  const webglue = pyodide.pyimport("webglue");
  // init() loads the manifest and returns the same payload as players_json().
  webglue.init(MOUNT);

  // Public API used by app.js. Every call round-trips JSON strings.
  window.NIM = {
    pyodide,
    players: () => JSON.parse(webglue.players_json()), // [{name, authors, description}, ...]
    playerNames: () => JSON.parse(webglue.players_json()).map((p) => p.name),
    legalMoves: (state) => JSON.parse(webglue.legal_moves(JSON.stringify(state))),
    applyMove: (state, move) =>
      JSON.parse(webglue.apply_move(JSON.stringify(state), JSON.stringify(move))),
    isTerminal: (state) => webglue.is_terminal(JSON.stringify(state)),
    nimSum: (state) => webglue.nim_sum(JSON.stringify(state)),
    totalSticks: (state) => webglue.total_sticks(JSON.stringify(state)),
    askMove: (name, state) =>
      JSON.parse(webglue.ask_move(name, JSON.stringify(state))),
    perfectAnalysis: (state) =>
      JSON.parse(webglue.perfect_analysis(JSON.stringify(state))),
  };

  onStatus("Ready.");
  return window.NIM;
}

window.bootNim = bootNim;
