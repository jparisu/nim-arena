# FAQ

Common questions about putting a web app online. Each answer links to the page
where the topic is covered in full.

??? question "Do I need to buy a domain or a server?"
    No. [GitHub Pages](../github/pages.md) and
    [Streamlit Community Cloud](streamlit/cloud.md) are both free, both give you
    a public URL, and both are enough for this project. A custom domain is
    optional and changes nothing technically.

??? question "Streamlit or a static page — which should I use?"
    Streamlit if your team writes Python and nothing else; static if you want a
    page that is always instant and never sleeps. The comparison table is on the
    [Web app](index.md) page, and [Hosting](hosting.md) explains the trade-off
    behind it. Both are acceptable answers.

??? question "Can I write the game rules again in JavaScript? It would be easier."
    You can, and you will regret it. Two implementations of the same rules
    always drift, and then your page and your tournament disagree about which
    moves are legal. Either run your Python in the browser with
    [Pyodide](static-web/pyodide.md), or use [Streamlit](streamlit/index.md) so
    there is no second language at all.

??? question "Why is my GitHub Pages site showing a 404?"
    Four usual causes, in the order worth checking: Pages is not enabled
    (**Settings → Pages**); the **Source** is set to a branch that has no site
    in it; the deploy workflow has not run, or failed — look at the **Actions**
    tab; or the site is there but your links are absolute (`/style.css`) and the
    site is served from a subpath (`/your-repo/`). Use relative links. See
    [GitHub Pages](../github/pages.md#when-the-site-does-not-redeploy).

??? question "My page works when I double-click `index.html` but not when published — or the reverse."
    You are comparing `file://` with `http://`, and they are not the same
    environment. `fetch()` is blocked on `file://`, so anything loading JSON or
    HTML partials fails silently. Always test with a real server:
    `python -m http.server -d web 8000`. See
    [HTML, CSS and JavaScript](static-web/html-js.md#running-it-locally).

??? question "I pushed a fix and the published page still shows the old version."
    Either the deploy has not finished — check the **Actions** tab — or your
    browser is caching. Hard-reload (`Ctrl`+`Shift`+`R`), and add
    `{ cache: "no-cache" }` to any `fetch()` of a file your workflow updates.

??? question "Why does my Streamlit app take 30 seconds to load the first time?"
    It went to sleep. A free Community Cloud app shuts down after a period with
    no visitors, and the next visitor waits for it to wake. Nothing is wrong,
    and there is no setting to disable it — open the app a few minutes before a
    demo. See [the limits](streamlit/cloud.md#the-limits-that-will-bite-you).

??? question "Why does my Pyodide page take several seconds to load *every* first visit?"
    Because it is downloading a Python interpreter — around 10 MB, plus your own
    code. That cost is real and cannot be removed; show a progress message
    instead of a blank page, and note that the second visit is fast because the
    browser caches it. See
    [what the user pays for](static-web/pyodide.md#what-the-user-pays-for).

??? question "My Streamlit app resets the board every time I click."
    You are keeping the game in a normal variable. Streamlit re-runs the whole
    script on every interaction, so only `st.session_state` survives. Guard the
    initialisation with `if "state" not in st.session_state:`. See
    [Keeping state between reruns](streamlit/building.md#keeping-state-between-reruns).

??? question "Can I use React, Vue or Svelte?"
    Nothing stops you, but they bring a build step, a `node_modules` and a
    second toolchain into a project whose real language is Python — and none of
    that is what you are assessed on. Plain HTML, CSS and JavaScript scale
    perfectly well to a game UI; this repository's page is ~2,500 lines with no
    JavaScript build step at all.

??? question "Where do I store data if there is no database?"
    In a **JSON file in the repository**, written by a
    [scheduled workflow](../github/actions.md) and read by the page with one
    `fetch()`. It is versioned, reviewable and free. For per-visitor
    preferences, `localStorage`. For a shareable game, the URL. See
    [Hosting](hosting.md#where-data-lives-when-there-is-no-database).

??? question "Can I hide an API key in my JavaScript?"
    No. Everything the browser downloads is readable by anyone who opens the
    developer tools — minifying it changes nothing. If something must stay
    secret, it cannot live in a static page; put it in
    [Streamlit's secrets](streamlit/cloud.md#configuration-and-secrets) or drop
    the requirement. For a game project you almost certainly do not need one.

??? question "Can two people play against each other from different computers?"
    Not without a server. Every option in this section runs the game either in
    one browser or in one process; there is nothing coordinating two visitors.
    Human-vs-bot in one browser is what this project asks for, and it fits
    comfortably. Real-time multiplayer is a much larger project.

??? question "Do I have to commit the built files?"
    No — and you should not. `web/py.zip` and a copied `leaderboard.json` are
    build output: let the [deploy workflow](../github/actions.md) produce them
    and keep them in `.gitignore`. Committed build output makes every rebuild a
    diff and every merge a conflict.

??? question "My deploy works but a fork's pull request cannot publish a preview. Is it broken?"
    No, that is deliberate. A workflow triggered by a fork runs without secrets
    and without write access, because the PR author controls the code it would
    run. Review the change by building it locally instead. See
    [Pull requests cannot deploy](../github/pages.md#pull-requests-cannot-deploy).
