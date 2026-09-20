# Step-by-step guide

This is the whole project, in order, on one page.

You are going to build a **two-player turn-based game**: the rules as a Python
library, an interface other people's bots can plug into, a bot of your own, a
page anyone can play on, and a tournament that ranks every bot and publishes the
result. At the end it is a real open-source project, not an exercise.

Every task below says what to do, links to the section of this
[Guide](index.md) that explains it, and ends with a **Result** — the concrete
thing you should be able to see. Tick a task when you can see its result, not
when you feel finished.

## How this works

Three rules. They matter more than any individual task below.

**One big step, one pull request.** Branch off `main`, build the step, open a
pull request, have a teammate review it, merge. Nobody commits to `main` — not
even for a typo, not even on the last day. This is what makes the history
readable and the project recoverable when something breaks. See
[Workflow](github/workflow.md) and [Pull requests](github/pull-requests.md).

**A step is not done when the code runs.** It is done when the tests pass, the
documentation says the thing exists, the checks are green and the branch is
merged. Code written now and tested "later" is code tested never. See
[Testing](python-library/testing.md) and
[Documenting a project](documentation/documentation.md).

**Something playable at every stage.** Each big step ends with something you can
put in front of a person. That is deliberate: a project that only works at the
end is a project you cannot tell the state of.

!!! tip "The order is a dependency order, not a schedule"
    Each step needs the one before it — the bot needs the interface, the
    interface needs the rules. Within a step, tasks can be split across the
    team and done in parallel.

---

## Step 0 — The repository

Somewhere to put it. **This is the only step you do directly on `main`;**
from Step 1 onwards everything arrives by pull request.

- [ ] **0.1 — Create the repository**

    Create it **public**, on GitHub, with a short descriptive name. Let GitHub
    add the three files it offers: a `README`, a `.gitignore` for Python, and a
    license. Invite your teammates as collaborators straight away.

    The license is the one of the three that people skip and should not. A
    public repository with no license is not open source — copyright is the
    default, so nobody may legally reuse it. Pick **MIT** unless you have a
    reason to pick something else. See
    [First steps](github/first-steps.md) and
    [Choosing a license](github/first-steps.md#choosing-a-license).

    **Result.** A public URL. Your teammates can clone it and push a branch.

- [ ] **0.2 — Make it an installable package**

    Add a `pyproject.toml` and put your code under `src/yourgame/`, with an
    `__init__.py`. The `src/` layout is not decoration: it stops Python from
    importing your source folder by accident, so the tests run against the
    package **as a user receives it**. See
    [Organization](python-library/organization.md#the-src-layout).

    Then install it in editable mode into a virtual environment and import it
    from somewhere else entirely. If that works, everything after this — the
    tests, the web app, the tournament, somebody else's bot — can import your
    game with one line. See
    [What is a library](python-library/library.md) and
    [Installation and usage](python-library/installation-and-usage.md).

    ```console
    $ python -m venv .venv && source .venv/bin/activate
    $ pip install -e .
    $ cd /tmp && python -c "import yourgame; print(yourgame.__version__)"
    ```

    **Result.** `import yourgame` works from any directory.

- [ ] **0.3 — Adopt the workflow**

    Protect `main`: **Settings → Rules**, require a pull request, require at
    least one approving review, and forbid direct pushes. Do this *now*, while
    the repository is empty and the rule costs nothing to obey. Doing it in week
    six means unpicking six weeks of habits. See
    [Repository configuration](github/repository-configuration.md).

    Add a pull request template so every PR answers the same questions — what it
    does, and whether the tests and docs were updated. It is a checklist you
    write once and a reviewer benefits from thirty times. See
    [Pull requests](github/pull-requests.md#pull-request-templates).

    **Result.** `git push origin main` is refused. A PR shows a review
    requirement before it can be merged.

- [ ] **0.4 — Run the checks on every push**

    Write `.github/workflows/tests.yml`: check out the repository, install
    Python, install the package, run `pytest` and a linter. You have nothing
    worth testing yet, so start with a test that asserts the package imports —
    the point of this task is the *pipeline*, not the coverage. See
    [GitHub Actions](github/actions.md#running-the-tests).

    Then make it mandatory. In the branch rules, add the workflow as a
    **required status check**. From this moment on, a red suite is not a
    warning, it is a locked merge button, and nobody has to remember to look.
    See [Required status checks](github/repository-configuration.md#required-status-checks).

    **Result.** A green tick on a pull request. A deliberately broken test turns
    it red and blocks the merge.

- [ ] **0.5 — Publish the documentation site**

    Add a `mkdocs.yml` and a `docs/index.md` with one paragraph in it. Run
    `mkdocs serve` to see it locally, then import the repository on
    [Read the Docs](documentation/readthedocs.md) and add the build badge to
    your README. See [MkDocs](documentation/mkdocs.md).

    Fifteen minutes now buys you a published site that every later step writes
    into. The alternative — leaving documentation to the end — produces a
    documentation sprint in the last week, and documentation written in the last
    week is documentation nobody believes. See
    [Documenting a project](documentation/documentation.md).

    **Result.** A live documentation URL with one page on it, rebuilt on every
    push.

!!! success "End of Step 0"
    An empty project that is already professional: public, installable,
    protected, tested on every change, and documented at a real URL. Nothing
    works yet. Everything is in place for something to.

---

## Step 1 — The game

The rules, and nothing but the rules. No interface, no bots, no bells.

- [ ] **1.1 — Write the rules down, before any code**

    Open `docs/rules.md` and describe the game in prose: the starting position,
    what a turn consists of, what makes a move legal, when the game ends, and
    who wins. Write it for someone who has never heard of your game.

    This is the cheapest hour of the project. Every ambiguity you find while
    writing this page — *can a player pass? what happens on a draw? who moves
    first?* — is an ambiguity you would otherwise have found halfway through the
    web app, with three files already built on the wrong answer.

    If your game has **hidden information** or **randomness**, say so here,
    explicitly. Those two properties change the design of everything downstream,
    and they must be decided now rather than discovered later. See
    [Documenting a project](documentation/documentation.md) and this
    repository's own [Game rules](../game/rules.md) as an example of the shape.

    **Result.** A rules page a stranger could play the game from, on paper.

- [ ] **1.2 — Model the state and the move**

    Decide the smallest data that captures a position completely, and the
    smallest data that captures a move. Prefer plain built-in types — a list of
    integers, a tuple, a string — over classes you do not need yet. A state that
    is a plain structure can be printed, compared, copied and sent through JSON
    to a browser without any work at all.

    Two decisions to make deliberately. **Where does "whose turn is it" live** —
    inside the state, or held by whatever is running the game? And **is a state
    immutable**: does applying a move return a new state, or modify the one you
    were given? Return a new one. A bot that accidentally mutates the board it
    was handed is a bug you will otherwise spend an evening on.

    Name the shapes with type aliases (`State = list[int]`,
    `Move = tuple[int, int]`) so every signature in the project reads the same
    way. See [Organization](python-library/organization.md).

    **Result.** You can write a starting position as a literal in the REPL and
    print it.

- [ ] **1.3 — Implement the rules as pure functions**

    Four functions carry a turn-based game: `legal_moves(state)`,
    `apply_move(state, move)`, `is_terminal(state)` and `winner(state)`. Add
    `is_legal(state, move)` if the legal set is large enough that generating it
    is wasteful.

    Keep them **pure**: no printing, no `input()`, no files, no global state.
    They take a position and return an answer. Everything else in the project —
    the terminal loop, the bots, the web page, the tournament — is a caller of
    these four functions, and they can only all agree if the functions are the
    single place the rules exist.

    Be strict at the boundary. `apply_move` with an illegal move should raise,
    not silently do something reasonable. A strict engine turns a bot's bug into
    an immediate, located error instead of a corrupted game three moves later.
    See [API](python-library/api.md) and, for a worked example,
    [Code structure](../game/advanced/code-structure.md).

    **Result.** In a REPL: apply a move to a position and get the next position
    back, with the original unchanged.

- [ ] **1.4 — Test the rules**

    Create `tests/test_game.py`, mirroring `src/yourgame/game.py`. One source
    module, one test module — that pairing is the whole convention, and it makes
    a missing test obvious. See [Testing](python-library/testing.md).

    Test the things that are true regardless of the game: the legal moves at a
    position you worked out by hand; that `apply_move` does not mutate its
    input; that an illegal move raises; that a terminal position is detected;
    that a scripted sequence of moves ends with the winner you expect.

    Then test the awkward cases, because they are where the marks and the bugs
    both live: the empty board, the position with exactly one legal move, the
    move at the edge of the board, and — if your game has them — a draw and a
    position where a player cannot move at all.

    **Result.** `pytest` is green locally, and the check is green on the pull
    request.

- [ ] **1.5 — Play a whole game from Python**

    Write a twenty-line loop: print the state, read a move from `input()`,
    apply it, repeat until terminal, announce the winner. Two humans, one
    keyboard, no interface.

    This is the honest test of everything above it. If the loop is awkward to
    write — if you need to reach into the internals, or keep a variable the
    state should have held, or special-case the first turn — your API is wrong,
    and it is far cheaper to fix that now than after a web page has been built
    on it.

    Keep the loop out of the library. It is a script, or a small
    `__main__`/console entry point; the package stays importable and silent. See
    [Installation and usage](python-library/installation-and-usage.md).

    **Result.** You and a teammate play a complete game in a terminal.

!!! success "End of Step 1"
    Your game exists and is correct, with no interface at all. Someone who
    installs your package can play it from a Python prompt.

---

## Step 2 — The platform

Somewhere for a bot to plug in — including a bot written by someone who has
never seen your source.

- [ ] **2.1 — Design the `Player` interface**

    Write an abstract base class with **one** required method:
    `choose_move(self, state) -> Move`. Add class-level identity — a name, the
    authors, a one-line description — and a `create(cls, seed)` factory, so that
    a bot using randomness can be constructed reproducibly.

    Keep the contract as small as the job allows. Every method you require is a
    method a stranger has to implement correctly, and every one of them is a way
    for their bot to be broken. One method is usually enough; a hook for
    "game over" is a reasonable second. See
    [Designing a plug-in API](python-library/api.md#designing-a-plug-in-api).

    Decide here **what a player is allowed to see**. For a perfect-information
    game, the state. For a game with hidden information, a *view* of the state
    built for that player — never the full position, or your bots can cheat and
    your game is not the game you documented. This is the one decision in the
    project that cannot be retrofitted. See
    [Player API](../game/upload-a-bot/player-api.md).

    **Result.** An abstract class that refuses to instantiate if `choose_move`
    is missing.

- [ ] **2.2 — Write the baseline player**

    Implement `RandomPlayer`: ask for the legal moves, pick one at random with
    its own seeded generator, return it. Thirty seconds of thought, and it does
    two important jobs.

    First, it proves the interface is implementable — if writing the simplest
    possible bot is awkward, fix the interface now, while there is exactly one
    implementation of it. Second, it is the yardstick: every bot for the rest of
    the project is measured against random, and "beats random" is the first
    meaningful thing any AI achieves.

    Write it the way an outsider would, importing only your public API. If it
    needs a private helper, that helper is part of the API and should be public.

    **Result.** Two random players finish a legal game against each other.

- [ ] **2.3 — Write the match runner**

    One function: `play_game(player_a, player_b, state)`. Alternate turns, ask
    the player whose turn it is for a move, check the move, apply it, repeat
    until terminal. Return the winner and the move history.

    Validate **every** move a player hands you, before applying it. This
    function is the boundary between your code and a stranger's, and the engine
    on the other side of it is strict. Hand each player a copy of the state, so
    a bot that mutates what it was given damages only itself.

    Keep the runner ignorant of *who* is playing. It knows about two objects
    with a `choose_move` method — nothing about humans, bots, difficulty or the
    tournament. That is what will let you reuse it unchanged in Step 4 and
    Step 5. See [The tournament](../game/advanced/tournament.md).

    **Result.** Two bots play to the end; you get a winner and the list of moves
    that produced it.

- [ ] **2.4 — Write the contract test**

    Write one test that runs over **every** registered player and asserts, at
    every single turn of several different games: the returned move was legal,
    and the state it was handed was not modified. Parametrize it over the
    registry, so admitting a new bot needs no new test.

    Then prove the test works by writing bots that break it. A bot that raises,
    a bot that returns an illegal move, a bot that never returns, a bot that
    edits the board it was given. Each should fail cleanly and by itself. See
    [Testing a contract other people implement](python-library/testing.md#testing-a-contract-other-people-implement).

    This is the task that makes accepting outside contributions safe. Without
    it, every bot someone sends you is a code review you have to do perfectly by
    eye; with it, the pull request goes red on its own.

    **Result.** A deliberately broken bot fails CI. A correct one passes without
    anyone adding a test for it.

- [ ] **2.5 — Document the API and the submission path**

    Two documents, and they are different documents. The **reference** is
    generated from your docstrings with `mkdocstrings`, so a renamed parameter
    cannot leave a stale page behind. See
    [API pages from docstrings](documentation/mkdocs.md#api-pages-from-docstrings).

    The **tutorial** is written by hand and walks one person from nothing to a
    merged bot: copy this file, implement this method, register it here, run
    this command to check it, open a pull request. Number the steps. Show the
    whole file, not a fragment. See
    [Documenting a project](documentation/documentation.md) and this
    repository's [Submit a player](../game/upload-a-bot/submit-a-player.md).

    **Result.** Someone outside your team follows the tutorial and opens a
    working pull request without asking you a single question.

!!! success "End of Step 2"
    Your game is a platform. A stranger can add a bot to it without opening
    your source, and your tests will tell them if it is broken.

---

## Step 3 — The bot

Something worth beating. You already have random; now build an opponent.

- [ ] **3.1 — Beat random**

    Find one rule of thumb about your game — take the biggest capture, control
    the centre, never leave two in a row — and apply it greedily: score every
    legal move with that rule, play the best one, break ties randomly.

    Greedy play has no lookahead and no cleverness, and it will still crush
    random in most games. Build it before anything sophisticated: it is an hour
    of work, it gives you a second yardstick, and the scoring function you write
    here is usually the evaluation function you will reuse in the next task.

    **Result.** Over 100 games against random, it wins more than 80% of them.

- [ ] **3.2 — Look ahead**

    Now search. **Minimax with alpha–beta pruning** for a perfect-information
    game, **expectimax** if there is randomness, **Monte Carlo tree search** if
    the branching factor is too large for either. You need three things: a value
    for a terminal position, an evaluation for a non-terminal one (your greedy
    score, most likely), and a depth limit.

    The depth limit is not optional. An unbounded search is a bot that takes
    thirty seconds on a busy position, and a thirty-second move is a broken
    interface no matter how good it is. Cap the depth, or cap the time and
    deepen iteratively until it runs out.

    Watch what the search actually costs. If a full-depth search is fast, go
    deeper; if it is slow, make the evaluation cheaper before you make the
    search cleverer.

    **Result.** It beats your greedy player, and it answers in under a second on
    the worst position you can find.

- [ ] **3.3 — Measure it**

    Write a small script that plays N games between two named players and prints
    a win-rate table. Run each pairing **both ways** — in a great many games,
    moving first is worth more than any amount of intelligence, and a bot tested
    only as player one is a bot you know nothing about.

    Fix the seed so a run is reproducible, and report the number of games. "It
    seems better" is not a result; "wins 71% of 200 games, 68% as second player"
    is, and it is the sentence that tells you whether your last change helped.

    **Result.** A table of win rates between random, greedy and your search bot,
    produced by a command you can run again.

- [ ] **3.4 — Explain how it decides**

    Write the docs page: what it evaluates, how deep it looks, what it is bad
    at. Being honest about the weakness is more useful than praise — "it cannot
    see a forced loss more than four moves away" tells a reader something they
    can act on.

    Optionally, let the bot publish its reasoning for the last move — the depth
    reached, the score, the number of positions examined. It costs a dictionary
    and it turns your web page into something that shows *why* a move was made,
    which is a far better demonstration than a board that simply moves. See
    [Documenting a project](documentation/documentation.md).

    **Result.** A page from which a reader could reimplement your bot.

!!! success "End of Step 3"
    Your bot beats random every time, beats greedy most of the time, and beats
    you sometimes.

---

## Step 4 — Build and deploy

Somewhere a person can actually play. You are building a **static page**, served
by [GitHub Pages](github/pages.md) from your own repository — the same
arrangement as [this project's page](https://jparisu.github.io/nim-arena). No
server, no bill, no cold start, and the Python you already wrote runs in the
browser through [Pyodide](web-app/static-web/pyodide.md).

!!! note "Streamlit is also a valid answer"
    If your team would rather write no JavaScript at all,
    [Streamlit](web-app/streamlit/index.md) is a legitimate route and the rest
    of this step still applies — only the mechanics of tasks 4.1 to 4.3 change.
    Be aware of two differences: it is deployed to
    [Streamlit Community Cloud](web-app/streamlit/cloud.md) rather than Pages,
    so **the URL is a different one on a different host**, and a free app
    [sleeps when nobody is using it](web-app/streamlit/cloud.md#the-limits-that-will-bite-you).

    Either way, **the published URL goes in the `README.md`**, at the top, as a
    link. Whichever host you chose, a visitor to your repository must be able to
    find the playable page without asking where it is.

- [ ] **4.1 — Serve a page from your repository**

    Make a `web/` folder with three files — `index.html`, `style.css`, `app.js` —
    saying nothing more than the name of your game. Set **Settings → Pages →
    Source** to **GitHub Actions**, and write the deploy workflow that builds
    `web/` and publishes it. See
    [Publishing a site of your own](github/pages.md#publishing-a-site-of-your-own)
    and [HTML, CSS and JavaScript](web-app/static-web/html-js.md).

    Do this **before** there is anything worth showing. Getting the deployment
    pipeline working while the page says "hello" takes an afternoon of settings
    and permissions; getting it working the night before a demo, with a finished
    game on the line, takes the same afternoon and costs considerably more.

    Test locally by serving the folder, never by double-clicking the file —
    `fetch()` is blocked on `file://`, and a page that works locally and fails
    when published is almost always this.

    ```console
    $ python -m http.server -d web 8000
    ```

    **Result.** A public `github.io` URL showing your placeholder, redeployed on
    every push to `main`. The link is in the README.

- [ ] **4.2 — Get your game into the browser**

    Add a build script that zips `src/yourgame/` into `web/py.zip`, and have the
    page load Pyodide, fetch the archive, unpack it and import your package.
    Write **one bridge module** that exposes exactly the functions the page
    needs, and pass JSON strings across the Python↔JavaScript boundary. See
    [Python in the browser](web-app/static-web/pyodide.md).

    This is the task that keeps the project honest. The alternative —
    reimplementing the rules in JavaScript — means two versions of the thing you
    spent Step 1 getting right, and they will disagree. One engine, used by the
    tests, the tournament and the page alike. See
    [The web app](../game/advanced/web.md).

    Have the deploy workflow run the build script, and keep `py.zip` out of Git:
    it is generated output, and committing it makes every rebuild a diff.

    **Result.** From the browser console, you can ask the bridge for the legal
    moves of a position and get your Python's answer back.

- [ ] **4.3 — Draw the board and take a click**

    Render the board from the state — one element per cell, pile or square — and
    make clicking one produce a move, apply it through the bridge, and redraw
    from the new state. Always redraw from the state; never patch the display
    and hope it stayed in agreement.

    Write it as one function, `paintBoard(container, state, onPick)`, and call it
    from everywhere the board appears. Two copies of a board renderer diverge
    within a week. See
    [HTML, CSS and JavaScript](web-app/static-web/html-js.md).

    **Result.** A human can play both seats of a complete game in the browser.

- [ ] **4.4 — Put a bot in the other seat**

    Add a selector listing your registered players, and after each human move
    ask the chosen bot for its reply and apply it. Show which player is which,
    and say who won when the game ends.

    You already have everything this needs: the registry from Step 2, the bot
    from Step 3, and a bridge that can call both. If this task requires new
    game logic, something leaked into the wrong layer — the page should be
    asking questions, not answering them.

    A short delay before the bot's move makes the game feel considered rather
    than instant. So does showing what the bot was thinking, if you did the
    optional half of task 3.4.

    **Result.** A person opens the URL and plays a full game against your bot,
    with an ending.

- [ ] **4.5 — Survive the user**

    Now try to break it. Click a stick that is already gone. Double-click.
    Click during the bot's turn. Click after the game is over. Reload halfway
    through. Open it on a phone. Each of these should produce a message or
    nothing at all — never a blank page and never a dead button.

    A static page has no server log, so an exception that escapes is invisible:
    the user sees a button that does nothing and has no way to tell you why.
    Catch errors globally, show them somewhere visible, and wire each part of
    the page up independently so one failure cannot silently disarm the rest.
    See [Failing loudly](web-app/static-web/html-js.md#failing-loudly).

    **Result.** You cannot break the page by clicking. Someone with a phone and
    the link plays a full game without you standing next to them.

!!! success "End of Step 4"
    A link you can send to anyone. They install nothing, and they play your
    game against your bot.

---

## Step 5 — The tournament

Who is actually best — decided automatically, and published.

- [ ] **5.1 — Play every pairing**

    Round robin: every registered player against every other, both orders,
    several games each. Reuse `play_game` from task 2.3 unchanged — if you find
    yourself needing a second runner, the first one knew too much.

    Count wins, losses and draws, and keep the per-match detail as well as the
    totals. Seed the whole run from a single number so the same tournament
    produces the same result twice; a leaderboard that changes when nothing
    changed is a leaderboard nobody trusts. See
    [The tournament](../game/advanced/tournament.md).

    **Result.** A standings table printed in your terminal.

- [ ] **5.2 — Survive a bad player**

    A tournament runs unattended, with strangers' code in it, and the failure
    mode that matters is not a bot losing — it is a bot taking the whole run
    down with it. Every one of these must cost the offender its game and nothing
    more: raising an exception, returning an illegal move, returning nothing,
    never returning at all, mutating the board it was handed, or lying about its
    own name.

    Wrap each move request: catch everything, enforce a timeout, validate the
    move, pass a copy of the state. On any violation, the offender forfeits that
    game, the reason is recorded, and the tournament continues to the next pair.

    Prove it with tests. Write the broken bots deliberately — one that crashes,
    one that cheats, one that hangs — and assert that each loses its own games
    while the run completes. See [Testing](python-library/testing.md).

    **Result.** A bot that raises on every move finishes last with a recorded
    reason, and the tournament still produces a full table.

- [ ] **5.3 — Write the ranking to a file**

    Emit the standings as JSON — not to stdout, to `results/leaderboard.json`.
    Include a schema version, the time the run finished, the ranked standings,
    and enough per-player metadata for a page to render the table without
    knowing anything else.

    A file is what makes the next two tasks possible. It is read by the web
    page, committed by CI, diffed in a pull request, and kept in history, and
    none of that works if the result only ever existed on a terminal that has
    since been closed. See [The scoreboard](../game/advanced/scoreboard.md).

    **Result.** A `leaderboard.json` you can open, and a command that
    regenerates it.

- [ ] **5.4 — Run it automatically**

    Write a workflow that runs the tournament on a schedule — nightly is plenty
    — and on `workflow_dispatch` so you can also trigger it by hand. Have it
    commit the new `leaderboard.json` back to the repository. See
    [GitHub Actions](github/actions.md).

    One trap, and it will cost you an evening if you meet it unwarned: **GitHub
    raises no `push` event for a commit made by a workflow**. Your Pages deploy,
    which triggers on push, will not notice the new leaderboard. The fix is to
    have the deploy also listen for the tournament workflow finishing, with
    `workflow_run`. See
    [When the site does not redeploy](github/pages.md#when-the-site-does-not-redeploy).

    **Result.** The leaderboard file changes overnight with nobody watching.

- [ ] **5.5 — Show it**

    Add a scoreboard screen that fetches `leaderboard.json` and renders the
    table. No game is played to draw it — it is pure data rendering over a file
    the build put next to the page. Pass `{ cache: "no-cache" }`, or a browser
    will cheerfully show you yesterday's copy of a file that updated an hour
    ago. See
    [Loading data without a backend](web-app/static-web/html-js.md#loading-data-without-a-backend).

    Handle the empty case: before the first tournament has run, the file may not
    exist. Say so on the page rather than failing.

    **Result.** A public scoreboard. Merge a bot today, and it is ranked
    tomorrow without anyone doing anything.

!!! success "End of Step 5"
    The project now runs itself. A pull request adds a bot, the checks say
    whether it is valid, the tournament ranks it, and the page shows the
    result.

---

## Ship it

- [ ] **6.1 — Make the README a real front page**

    One screen: what the game is, a picture or a short animation of it being
    played, a link to the playable page, a link to the documentation, how to
    install it, how to add a bot, and the license. Put the badges for the tests
    and the docs build at the top.

    The README is the trailer, not the documentation. Everything longer than a
    paragraph belongs on the [documentation site](documentation/index.md) with a
    link from here. A README that grows past two screens is a documentation site
    trying to escape. See
    [Documenting a project](documentation/documentation.md).

    **Result.** A stranger understands what this is in thirty seconds and knows
    exactly where to click next.

- [ ] **6.2 — Clone it fresh and follow your own instructions**

    On a different machine, or at least in a new directory with a new virtual
    environment, clone the repository from scratch and do exactly what your
    README and your bot tutorial say. Type the commands as written. Do not fix
    anything from memory as you go — write down what failed.

    This finds the step nobody wrote down, because everyone on the team has had
    it installed since week two. It is the single highest-value hour at the end
    of a project, and the only way to know whether the instructions you have
    been publishing actually work. See
    [Installation and usage](python-library/installation-and-usage.md).

    **Result.** A clean clone reaches a finished game, and a working bot, using
    nothing but what is written down.

- [ ] **6.3 — Be able to explain it**

    Go through the project and find every decision that could have gone the
    other way — the state representation, the size of the player interface, what
    a bot is allowed to see, the search you chose, Pages over Streamlit — and
    make sure someone on the team can say why.

    Where the reason is not obvious from the code, write it down next to the
    code or on the page where a reader would go looking. A comment explaining
    *why* something is the way it is outlives every comment explaining *what* it
    does.

    **Result.** For any part of the project, somebody can answer "why is it
    built like this?" with a reason rather than a shrug.

---

## What you should have

| After | There is |
| --- | --- |
| **Step 0** | a public, installable, protected, tested, documented empty project |
| **Step 1** | a correct game, playable from a Python prompt |
| **Step 2** | an interface a stranger can write a bot against, and a test that checks them |
| **Step 3** | a bot worth playing, with measured results |
| **Step 4** | a public URL where anyone plays your game against it |
| **Step 5** | a tournament that ranks every bot and publishes the table by itself |

## Where to go next

- [Git](git/index.md) · [GitHub](github/index.md) ·
  [Python library](python-library/index.md) · [Web app](web-app/index.md) ·
  [Documentation](documentation/index.md) — the five sections, in depth.
- [The game](../game/index.md) — this repository as a finished example of
  everything above.
