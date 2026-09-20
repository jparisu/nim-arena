# Building the app

!!! warning "Scaffold — not written yet"
    This page is a placeholder. The outline below is what it will cover.

## Outline

- `pip install streamlit`, `streamlit run app.py`, and the live-reload loop.
- The execution model: the whole script re-runs top to bottom on every
  interaction. Everything else follows from this.
- Widgets: `st.button`, `st.slider`, `st.selectbox`, `st.text_input`.
- Layout: columns, tabs, the sidebar, `st.container`.
- Keeping values between re-runs: `st.session_state`.
- Not re-computing the expensive parts: `@st.cache_data`, `@st.cache_resource`.
- Calling *your own library* from the app — the app is a thin shell, the logic
  stays in the package.
- Project layout: where `app.py` goes, and what belongs in `requirements.txt`.

## Where to go next

- [Streamlit Community Cloud](cloud.md) — putting it online.
