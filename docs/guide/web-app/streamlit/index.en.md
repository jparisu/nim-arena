# Streamlit

**Streamlit** turns a Python script into a web app. No HTML, no JavaScript, no
front-end framework — you write Python, it renders widgets.

The price is that it is **not static**: a Streamlit app needs a process running
somewhere to answer every interaction. That is what
[Streamlit Community Cloud](cloud.md) provides, for free, with limits.

---

## How it works, in one line

```mermaid
flowchart LR
    C["🖱️ A click"] --> S["🔁 Streamlit reruns<br/>your whole script"]
    S --> W["🧩 Redraws the widgets"]
```

That rerun is the one strange thing about Streamlit, and it is the first thing
[Building the app](building.md) explains.

---

## The pages

<div class="grid cards" markdown>

- :material-application-braces-outline:{ .lg .middle } **[Building the app](building.md)**

    ---

    The script, the widgets and the state model.

- :material-cloud-upload-outline:{ .lg .middle } **[Streamlit Community Cloud](cloud.md)**

    ---

    Deploying it from your repository, and the limits of the free tier.

</div>

---

**Next:** [Static web](../static-web/index.md) — the other route, with no server at all.

**Also:** [Hosting](../hosting.md)
