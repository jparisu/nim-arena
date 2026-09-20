# Streamlit Community Cloud

!!! warning "Scaffold — not written yet"
    This page is a placeholder. The outline below is what it will cover.

## Outline

- What it is: free hosting that runs a Streamlit app straight from a public
  GitHub repository.
- Connecting the repository, picking the branch and the entry-point script.
- Dependencies: `requirements.txt`, and why the app's deps are not the library's
  deps.
- Every push to the branch redeploys. Where to read the build log when it fails.
- Secrets and configuration, without committing them.
- The limits that matter: the app sleeps when nobody uses it, resources are
  capped, and the URL is not yours.
- When to move off it.

## Where to go next

- [Static web](../static-web/index.md) — the route with no server to fall asleep.
- [GitHub Actions](../../github/actions.md) — automating the checks that run
  before a deploy.
