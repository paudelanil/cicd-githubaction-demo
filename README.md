# cicd-github-actions

CI/CD demo: one FastAPI service, two workflows.

- `ci.yml` — lint + format + matrix tests on every push and PR
- `build.yml` — build a Docker image and push it to GHCR on `main` and `v*` tags

The app is a deliberately tiny in-memory ticket store. The point of the
demo is the pipeline around it, not the application code.

---

## Get your own copy

Pick whichever path matches what you have.

### Path A — Use this template (recommended)

The instructor maintains a template at
**[github.com/ai-ml-academy/cicd-github-actions](https://github.com/ai-ml-academy/cicd-github-actions)**.

1. Open that URL.
2. Click the green **Use this template** button → **Create a new repository**.
3. Owner: your account. Repo name: anything. Visibility: **Public**
   (free Actions minutes + free GHCR storage).
4. Click **Create repository from template**.
5. Clone it locally:
   ```bash
   git clone git@github.com:<your-username>/<your-repo-name>.git
   cd <your-repo-name>
   ```

### Path B — Bootstrap from course materials

If you have the course repo and prefer to build from the snapshot in
`classes/03-api-deployment/03-cicd/demos/`:

1. On GitHub, create a new empty public repo (no README, no `.gitignore`,
   no license).
2. Copy the files in and push:
   ```bash
   mkdir ~/my-cicd-demo
   cd ~/my-cicd-demo
   git init -b main

   rsync -av --exclude='.git' \
     /path/to/ds-course-claude-2/classes/03-api-deployment/03-cicd/demos/ \
     ./

   git remote add origin git@github.com:<your-username>/my-cicd-demo.git
   git add . && git commit -m "bootstrap"
   git push -u origin main
   ```

Either path lands you in the same place: a fresh GitHub repo with this
code, this app, and these two workflows.

---

## After you have your copy — one-time setup

Workflows need permission to push images to GHCR:

1. In the browser, go to your repo's **Settings → Actions → General**.
2. Scroll to **Workflow permissions**.
3. Select **Read and write permissions** → **Save**.

That's it. Push any change to `main` and both workflows will fire.

---

## Run it locally

```bash
make install      # pip install -r requirements.txt
make test         # pytest
make lint         # ruff check
make format       # ruff format
make run          # uvicorn on :8000
make build        # docker build -t support-api:local .
```

## Endpoints

| Method | Path                       | What it does          |
|--------|----------------------------|-----------------------|
| GET    | `/health`                  | liveness check        |
| POST   | `/tickets`                 | create a ticket       |
| GET    | `/tickets`                 | list tickets          |
| GET    | `/tickets/{id}`            | fetch one or 404      |
| POST   | `/tickets/{id}/close`      | mark closed or 404    |

## Layout

```
cicd-github-actions/
├── .github/workflows/
│   ├── ci.yml                  # lint + format + matrix tests
│   └── build.yml               # GHCR build & push
├── app/
│   ├── main.py                 # FastAPI app + /health
│   └── routers/support.py      # ticket endpoints
├── tests/
│   └── test_support.py
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── Makefile
└── .env.example
```

## What the two workflows do

### `ci.yml` — Continuous Integration

Fires on every push to `main` and every PR. One job (`lint-format-test`)
runs across a matrix of Python 3.11 and 3.12 with `fail-fast: false` so
both lanes complete. Steps: install → `ruff check` → `ruff format --check`
→ `pytest`. Pip wheels are cached on `requirements.txt`.

### `build.yml` — Continuous Delivery

Fires on push to `main` and on `v*` tags. Logs into GHCR with the
auto-issued `GITHUB_TOKEN`, computes tags via `docker/metadata-action`
(`latest`, `sha-<short>`, `v<semver>`), and pushes to
`ghcr.io/<your-username>/<your-repo-name>` with GitHub Actions layer
cache.

> Deployment to a real cloud (AWS, Fly, Render, etc.) is the next class.

## Try it yourself

Three tiny walkthroughs — copy, push, watch the Actions tab.

### Walkthrough 1 — Ship a change (green CI)

Bump the app version. In `app/main.py`, change the line:

```python
app = FastAPI(title="support-api", version="0.1.0")
```

to:

```python
app = FastAPI(title="support-api", version="0.1.1")
```

Then:

```bash
git add app/main.py
git commit -m "bump version to 0.1.1"
git push
```

Open the **Actions** tab. `CI` runs across Python 3.11 and 3.12 in
parallel — both should go green. `Build & push image` fires next, and
a fresh `sha-<short>` tag appears under **Packages**.

### Walkthrough 2 — Watch CI catch mistakes

CI has two gates: linting (`ruff`) and tests (`pytest`). Try breaking
each, one at a time.

**(a) Lint failure — unused import**

In `app/main.py`, add a stray import at the top:

```python
import os
```

Commit and push:

```bash
git add app/main.py
git commit -m "intentionally add unused import"
git push
```

The Actions tab shows `CI` failing at the **Lint with ruff** step with:
`F401 [*] os imported but unused`. The tests never run — the pipeline
short-circuits at the first red step. Remove the line, commit, push
again → green.

**(b) Test failure — flipped assertion**

In `tests/test_support.py`, find:

```python
assert response.status_code == 200
```

in `test_health_returns_ok` and change `200` to `500`. Commit and push.

Both Python 3.11 and 3.12 lanes go red at the **Run tests** step.
Click into either run → click the failed step → read the traceback:
`AssertionError: assert 200 == 500`. Change it back to `200`, commit,
push → green.

### Walkthrough 3 — Add a third workflow

The two shipped workflows cover push and PR. Add a **scheduled** one
that re-runs the tests every morning. This catches *dependency rot* —
when a transitive package gets yanked from PyPI or a wheel stops
building on the latest runner image, your code didn't change but your
build is now broken. Scheduled CI finds that for you.

Create `.github/workflows/nightly.yml`:

```yaml
name: Nightly

on:
  schedule:
    - cron: "0 7 * * *"   # every day at 07:00 UTC
  workflow_dispatch:       # also runnable from the Actions tab

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest -q
```

Commit and push it. To trigger it without waiting until 07:00 UTC,
open the **Actions** tab → click **Nightly** in the sidebar → click
**Run workflow** → **Run workflow**. That's the `workflow_dispatch`
button — a free side-effect of adding that line to the `on:` block.

## Optional — branch protection

After your first green CI run, you can require both matrix lanes to pass
before any PR can merge:

1. **Settings → Branches → Add rule** for `main`
2. ☑ Require a pull request before merging → 1 approval
3. ☑ Require status checks to pass → select `lint-format-test (3.11)`
   and `lint-format-test (3.12)`
4. ☑ Require branches to be up to date before merging
5. Save

Now any PR to `main` is gated on green tests *and* a review. To see it
in action, open a PR with a broken test — the merge button stays
disabled until the test passes.

## Optional — make the image publicly pullable

By default the image inherits the repo's visibility. If your repo is
public the package is too. To verify or flip it:

1. Your profile → **Packages** → click your package
2. **Package settings** → scroll to **Danger Zone**
3. **Change package visibility** → **Public**

Then anyone (including you, without `docker login`) can run:

```bash
docker pull ghcr.io/<your-username>/<your-repo-name>:latest
```
