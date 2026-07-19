# Maintaining NIM Arena

Notes for repository maintainers. Contributors should read
[CONTRIBUTING.md](../CONTRIBUTING.md) instead.

## Branch protection on `main`

Configure under **Settings → Branches → Add rule** for `main`:

- ✅ **Require a pull request before merging** (require at least 1 approval).
- ✅ **Require status checks to pass before merging** — select the **Tests**
  workflow (both Python versions) and **Docs**.
- ✅ **Require branches to be up to date before merging.**
- ✅ **Do not allow bypassing the above settings** (optional but recommended).

This makes the PR review the real gate: nothing lands on `main` without passing
CI and a human review.

## GitHub Pages

**Settings → Pages → Build and deployment → Source: GitHub Actions.** The
[`pages.yml`](workflows/pages.yml) workflow assembles and deploys the site.

## Reviewing a new-player PR

Every submission runs untrusted-but-reviewed code. Your review is the security
and correctness gate. Check the acceptance criteria from
[submit-a-player](https://nimarena.readthedocs.io/en/latest/submit-a-player/):

1. **Design** — one file in `players/`, one manifest line, subclasses `Player`,
   unique `name`.
2. **Correctness** — CI green; legal moves; no mutation of `state`; no
   errors/timeouts against the reference bots.
3. **No malware** — read the code in full. Reject on sight: network, filesystem,
   subprocess, `eval`/`exec`, `os`/`sys` manipulation, obfuscation, or attempts
   to read secrets or escape the sandbox.

A player that errors or times out is **not merged**, even if the tournament would
survive it.

!!! note
    PRs from forks run with a **read-only token and no secrets**, so a submitted
    bot cannot damage the repo during CI — but it *does execute*, which is exactly
    why the tournament's timeouts and forfeit handling are mandatory.
