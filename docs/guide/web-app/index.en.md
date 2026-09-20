# Web app

!!! warning "Scaffold — not written yet"
    Only the structure of this section exists. The pages below are placeholders.

A library nobody can try is a library nobody uses. This section is about putting
a **face** on your project: a page someone opens in a browser and uses, without
installing anything.

There are two routes, and they trade off differently. Read
[Hosting](hosting.md) first — it explains what the choice actually costs — then
pick one.

<div class="grid cards" markdown>

- [**1. Hosting**](hosting.md) — where a web app runs, who pays for it, and why
  "static" is the word that decides everything else.
- [**2. Streamlit**](streamlit/index.md) — write the whole app in Python, deploy
  it on Streamlit Community Cloud.
- [**3. Static web**](static-web/index.md) — HTML, CSS and JavaScript in a
  folder, published for free from your repository.

</div>

## Which one should I pick?

| | [Streamlit](streamlit/index.md) | [Static web](static-web/index.md) |
| --- | --- | --- |
| Language | Python only | HTML, CSS, JavaScript (+ Python via Pyodide) |
| Needs a server | Yes | No |
| Where it runs | Streamlit Community Cloud | GitHub Pages, any static host |
| Sleeps when idle | Yes | No |
| Effort to start | Low | Medium |

## Where to go next

- [GitHub Pages](../github/pages.md) — the free static host this project uses.
- [Documentation](../documentation/index.md) — the *other* site a project
  publishes, and why it is separate.
