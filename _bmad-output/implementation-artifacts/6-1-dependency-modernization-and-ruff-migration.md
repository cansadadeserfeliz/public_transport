# Story 6.1: Dependency Modernization & Ruff Migration

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

<!--
Not derived from relaunch-epics.md — this is maintainer-initiated tooling/dependency
debt, not tied to any PRD FR. Tracked as its own epic bucket (epic-6) in
sprint-status.yaml so it's visible without disturbing the FR-driven Epic 1-5
numbering. Not required for MVP; pull it into a sprint whenever it's convenient,
independent of Epic 1-5 sequencing.

Revised 2026-08-19: expanded scope after a dependency-usage audit (see Dev Notes)
found pre-commit is currently non-functional and the pytest stack is 2+ majors
behind. Both folded into this story rather than deferred, per maintainer decision.
-->

## Story

As a maintainer,
I want the dependencies Story 1.1 deliberately left untouched brought current where it's actually worth it, `black`+`flake8` consolidated onto `ruff`, the non-functional `pre-commit` setup removed rather than papered over, the stale `pytest` stack modernized, and `factory-boy` added for upcoming model-factory-based tests,
so that the project isn't running years-old packages for no reason, isn't paying for two overlapping lint/format tools where one now does both, faster, and isn't carrying a dev-tooling dependency that nothing in the actual workflow ever invokes.

## Acceptance Criteria

1. **Given** `requests` is pinned at `2.31.0` (2023) and `python-dotenv` at `1.0.0` (2023), **when** this story lands, **then** both are bumped to their current stable release, verified against their actual changelogs for breaking changes (neither is expected to have any affecting this codebase's usage).
2. **Given** `black==23.7.0` and `flake8==6.1.0` are both installed and configured (`pyproject.toml`, `.flake8`), **when** this story lands, **then** both are replaced by a single `ruff` dependency doing both lint and format, configured in `pyproject.toml` under `[tool.ruff]`/`[tool.ruff.lint]`/`[tool.ruff.format]`, with `.flake8` deleted and the README's linting section updated to invoke `ruff` instead.
3. **And** the ruff config preserves this repo's actual existing conventions — 79-char line length, single-quote strings (not double) — rather than adopting ruff's defaults wholesale; `routes/migrations/` (what remains of it) stays excluded, matching the current black/flake8 exclusion.
4. **And** each of flake8's currently-blanket-ignored codes (`E203`, `E266`, `E501`, `W503`, `F403`, `F401`) is individually re-evaluated against what ruff actually flags in this codebase — carried forward only if it still fires on real code, not copied forward by default. (Confirmed during story drafting: there are zero `import *` statements anywhere in the repo today, so the `F403` ignore has nothing to suppress — do not carry it forward without first checking whether ruff's `F401`/`F403` surface anything real.)
5. **And** a one-time `ruff format .` pass across the whole existing codebase lands as its own dedicated commit, separate from the tooling/config change itself, so the mechanical reformatting diff is reviewable independently of the actual config decisions.
6. **Given** `python-telegram-bot==20.4` and `Scrapy==2.10.1`/`scrapy-djangoitem==1.1.1`, **when** this story is scoped, **then** neither is bumped as part of this story (see Dev Notes — both are deliberately excluded, not overlooked).
7. **Given** `pre-commit` is currently pinned nowhere, configured in `.pre-commit-config.yaml`, but never actually wired into the workflow — the Dockerfile installs no `git` binary, the README documents only `docker compose run --rm app ...` commands with no `pre-commit install` step anywhere, and no CI workflow exists to invoke it either — **when** this story lands, **then** `pre-commit` is removed entirely (dropped from `requirements.txt`, `.pre-commit-config.yaml` deleted) rather than fixed in place, and the README's linting section becomes the sole documented enforcement mechanism.
8. **Given** `pytest==7.0.1`, `pytest-cov==3.0.0`, and `pytest-sugar==0.9.4` are each two or more majors behind current, **when** this story lands, **then** all three are bumped together to their current stable releases, and the full application suite still passes at the same baseline as before this story: 10 passed, 3 pre-existing unrelated `crawler/tests/test_utils.py` failures (13 collected). (Note — corrected during implementation: the "78 passed" figure documented at drafting time turned out to be inflated by a `pytest.ini` collection-scope bug that let `_bmad/`'s own bundled test suite leak into the run; see Dev Notes.)
9. **And** `factory-boy` is added to `requirements.txt`, pinned to its current stable release, as a dependency-only addition to unblock model-factory-based tests in upcoming stories — no factories are written as part of this story.

## Tasks / Subtasks

- [x] Task 1: Bump the two application dependencies actually worth bumping (AC: #1)
  - [x] 1.1 Verify current stable versions at implementation time (`pip index versions requests`, `pip index versions python-dotenv`) rather than trusting a stale pin — re-verified live at implementation time (2026-08-19, via PyPI JSON API): `requests` `2.34.2`, `python-dotenv` `1.2.3` (unchanged from drafting).
  - [x] 1.2 Update `requirements.txt`, rebuild, run the full test suite — no code changes were needed; the app suite (10 passed, 3 pre-existing unrelated `crawler` failures) is unaffected.

- [x] Task 2: Explicitly scope out Scrapy/scrapy-djangoitem and python-telegram-bot (AC: #6)
  - [x] 2.1 `Scrapy`, `scrapy-djangoitem`, `python-telegram-bot` left untouched at their current pins. Rationale (for PR description): `scrapy-djangoitem` is unmaintained (still at `1.1.1`, its last release). `crawler/` is scheduled for retirement once Story 1.3's GTFS pipeline lands (`relaunch-architecture.md`) — bumping `Scrapy` alone risks breaking code with a known near-term deletion date. `telegram_bot/` is `UNCHANGED — dormant, out of scope for v1` per the same doc, confirmed zero references from any other app and absent from `INSTALLED_APPS` — bumping `python-telegram-bot` v20→v22 now is pure risk for a component nothing exercises.
  - [x] 2.2 Noted for future stories: if either app is revived, its dependency bump belongs to that story, not backfilled here.

- [x] Task 3: Configure ruff in `pyproject.toml` (AC: #2, #3)
  - [x] 3.1 Added `ruff==0.16.3` to `requirements.txt` (re-verified current at implementation time).
  - [x] 3.2 Removed `[tool.black]`; added `[tool.ruff]` with `line-length = 79`, `target-version = "py311"`, and the exclude list carrying forward black's original entries. **Extended the exclude list with one entry not in the original scope**: `_bmad-output` — discovered during implementation that `ruff format`, unlike `black`, also reformats fenced ```python code blocks inside Markdown files, and `_bmad-output/planning-artifacts/relaunch-architecture.md` has Django model snippets as documentation. Without this exclusion, `ruff format .` would rewrite planning-doc code samples on every run. See Dev Notes.
  - [x] 3.3 Added `[tool.ruff.format]` with `quote-style = "preserve"` — confirmed via `ruff format --diff .` that no quote-style changes occurred anywhere in the codebase.
  - [x] 3.4 Added `[tool.ruff.lint]` with `select = ["E", "F", "W"]` only — no additional rule categories enabled.
  - [x] 3.5 Ignore list resolved via Task 4's investigation below.

- [x] Task 4: Re-evaluate flake8's ignored codes against ruff, per-code (AC: #4)
  - [x] 4.1 Ran `ruff check .` (real project config: line-length 79, full exclude list, `ignore = []`) both before and after the Task 6 reformat pass. Result: **none** of `E203`, `E266`, `E501`, `W503` fired, either before or after formatting — the constructs they'd flag don't currently occur anywhere in this codebase. Per AC #4's own rule ("carried forward only if it still fires on real code"), none are kept.
  - [x] 4.2 `F403` confirmed zero hits — matches drafting-time prediction (zero `import *` in the repo). Not added to ignore.
  - [x] 4.3 `F401` surfaced 4 real unused imports: `itemadapter.is_item`/`itemadapter.ItemAdapter` in `crawler/middlewares.py`, `re` in `crawler/spiders/sitp_spider.py`, `django.core.management.base.CommandError` in `routes/management/commands/load_bus_stations.py`. None were side-effect imports (no Django app-registration pattern) — all four were genuinely dead code, so removed via `ruff check --fix .` rather than suppressed with `# noqa`. Also cleaned up an orphaned comment in `crawler/middlewares.py` left referencing the removed import.
  - [x] 4.4 Final `ignore = []` — empty list, with a comment in `pyproject.toml` documenting why each of the 6 original codes was evaluated and dropped, so a future reader doesn't have to redo the investigation.

- [x] Task 5: Remove `pre-commit` entirely — decommission, don't reconfigure (AC: #7)
  - [x] 5.1 Removed `pre-commit` from `requirements.txt`.
  - [x] 5.2 Deleted `.pre-commit-config.yaml`.
  - [x] 5.3 Updated README's "Linting / formatting" section to `docker compose run --rm app ruff check .` / `docker compose run --rm app ruff format .`.
  - [x] 5.4 Rationale documented in Dev Notes (carried over from drafting, unchanged): `pre-commit` was configured but never wired up — no `git` in the Docker image, no host install step ever documented, no CI. Removing it is honest about the prior state, not a regression.

- [x] Task 6: Delete `.flake8` and run the one-time reformat (AC: #2, #5)
  - [x] 6.1 Deleted `.flake8`.
  - [x] 6.2 Ran `ruff format .`: 2 files reformatted (`app/urls.py`, `manage.py` — both trivial "blank line after module docstring" changes), 33 files already compliant. (This count reflects the corrected exclude list — see Task 3.2; the `_bmad-output` markdown file is not part of this diff.)

- [x] Task 7: Bump the test-tooling stack — pytest, pytest-cov, pytest-sugar (AC: #8)
  - [x] 7.1 Re-verified at implementation time: `pytest` `9.1.1`, `pytest-cov` `7.1.0`, `pytest-sugar` `1.1.1` — unchanged from drafting-time figures.
  - [x] 7.2 Bumped all three together in `requirements.txt`.
  - [x] 7.3 Ran the full suite and found a real discrepancy against the documented "78 passed" baseline — investigated rather than assumed pre-existing (per this task's own instruction). Root cause: **`pytest.ini` had no collection-scope restriction, and `_bmad/` (the gitignored, dockerignored BMAD tooling framework) was being swept into `python -m pytest`'s collection via the `app` service's bind mount** (`.dockerignore` excludes `_bmad/` from the image `COPY`, but `docker-compose.yml`'s `volumes: - .:/app` bind-mounts the full host tree at runtime regardless). One `_bmad` test file failed outright with `ModuleNotFoundError: No module named 'yaml'` (a BMAD-tooling dependency never installed by this project, correctly so). This is unrelated to the pytest version bump — it's a pre-existing `pytest.ini` scoping gap that the "78 passed" baseline apparently never hit cleanly either (see Dev Notes for the fix and full reasoning). Fixed by adding `--ignore=_bmad --ignore=_bmad-output` to `pytest.ini`'s `addopts`. After the fix: **10 passed, 3 pre-existing unrelated `crawler/tests/test_utils.py` failures, 13 collected** — this is the real, reproducible application-suite baseline going forward.
  - [x] 7.4 `pytest.ini`'s `addopts` (`--cov=./`, `--no-cov-on-fail`, `--cov-report html`, `--cov-report term`) all behaved identically under the new `pytest-cov` major — no flag errors, coverage reports generated as before.

- [x] Task 8: Add `factory-boy` for upcoming model-factory-based tests (AC: #9)
  - [x] 8.1 Added `factory-boy==3.3.3` to `requirements.txt` (re-verified current at implementation time).
  - [x] 8.2 Dependency addition only — no factories written.
  - [x] 8.3 No config changes needed — confirmed no `pytest.ini` changes required for `factory-boy` itself.

- [x] Task 9: Validate (Testing Standards)
  - [x] 9.1 `ruff check .` → "All checks passed!"; `ruff format --check .` → "35 files already formatted". Both clean.
  - [x] 9.2 Full `pytest` suite passes under the bumped `pytest`/`pytest-cov`/`pytest-sugar` at the corrected real baseline: 10 passed, 3 pre-existing unrelated `crawler/tests/test_utils.py` failures (13 collected) — see Task 7.3 for why this differs from the "78 passed" figure documented at drafting time.
  - [x] 9.3 Verified through the actual Docker workflow: `docker compose run --rm app ruff check .` and `docker compose run --rm app ruff format --check .` both work as documented in the updated README.

### Review Findings

- [x] [Review][Patch] Reformat pass not landed as its own dedicated commit, per AC #5 [pyproject.toml, app/urls.py, manage.py]
- [x] [Review][Patch] Dev Notes overstate necessity of `--ignore=_bmad-output` — only `--ignore=_bmad` was load-bearing for the collection leak [pytest.ini, story Dev Notes]
- [x] [Review][Patch] `E501` no longer blanket-ignored with no documented escape hatch for future long comments/URLs [pyproject.toml:~30]
- [x] [Review][Patch] `factory-boy==3.3.3` appended under `pytest-django` with no blank-line separation, inconsistent with the file's own grouping convention [requirements.txt]
- [x] [Review][Defer] No dev/prod split for requirements.txt (ruff/pytest/factory-boy mixed with runtime deps) — deferred, pre-existing
- [x] [Review][Defer] No lockfile/hash-pinning introduced — deferred, pre-existing pattern, out of scope for this story

## Dev Notes

### Why Scrapy/scrapy-djangoitem and python-telegram-bot are explicitly out of scope

This is the single most important scoping decision in this story, and it's easy to get wrong by treating "modernize dependencies" as "bump everything":

- `scrapy-djangoitem` has had no PyPI release in over a year and is classified inactive/unmaintained — the currently-pinned `1.1.1` **is** the latest version. There's nothing to bump it to.
- `crawler/` (the only consumer of both `Scrapy` and `scrapy-djangoitem`) is explicitly scheduled for retirement once Story 1.3's GTFS pipeline is confirmed working (`relaunch-architecture.md` → Infrastructure & monitoring: *"`crawler/` (Scrapy) app is retired once the GTFS pipeline is confirmed working — left in place until then, not extended with new spiders"*). Bumping `Scrapy` alone (its 2.13.x line changed `start_requests()` to an async `start()`, among other things) without a matching `scrapy-djangoitem` release is a real regression risk against code with a known, near-term deletion date. Not worth it.
- `telegram_bot/` is separately marked `UNCHANGED — dormant, out of scope for v1 (Phase 2 revival)` in the architecture doc's Project Structure & Boundaries. `python-telegram-bot` v20→v22 crosses two major version lines of an actively-developed library. Doing that work now, for a component nothing in v1 exercises, is pure risk with no near-term payoff — it belongs to whatever story actually revives the bot in Phase 2, when it can be tested against real usage.

### Dependency-usage audit (2026-08-19) — nothing else is actually dead

Before scoping this story's expansion, every package in `requirements.txt` was traced against real imports in the codebase:

- `requests` → `transmiapp/services.py`; `python-dotenv` → `app/settings.py`, `telegram_bot/services.py`; `whitenoise` → `app/settings.py` middleware; `psycopg` → the DB backend; `gunicorn` → `Dockerfile` CMD (not imported, but load-bearing). All in active use.
- The full `pytest`/`pytest-cov`/`pytest-django`/`pytest-sugar` stack is exercised via `pytest.ini` (`DJANGO_SETTINGS_MODULE`, `--cov` flags). All in active use.
- `Scrapy`/`scrapy-djangoitem` (via `crawler/`, which **is** in `INSTALLED_APPS`) and `python-telegram-bot` (via `telegram_bot/`, which is **not** in `INSTALLED_APPS` and has zero references from any other app) are both unused *by the rest of the codebase* but not dead code — see above, both are deliberate architecture decisions, not oversights. Nothing was deleted as a result of this audit; the conclusion is "nothing here is safe to delete," which is itself the useful finding.

### Why pre-commit is being removed, not reconfigured

Maintainer decision (2026-08-19), after auditing whether the existing `.pre-commit-config.yaml` setup actually does anything: it doesn't, today. Three independent gaps, any one of which would be enough on its own:

1. The `Dockerfile` never installs a `git` binary, and `pre-commit` needs `git` to install/run hooks.
2. The README's entire documented dev workflow is `docker compose run --rm app ...` — there is no host-side Python environment, and no step anywhere tells a developer to run `pre-commit install`.
3. There is no CI workflow (`.github/workflows` doesn't exist) providing a second line of enforcement either.

So the hooks defined in `.pre-commit-config.yaml` have never actually fired for anyone working through the documented setup. Rather than investing in making it work (adding `git` to the image, documenting a `docker compose exec app pre-commit install` step, and figuring out how hooks fire correctly for a bind-mounted repo where `git commit` typically runs on the host) — which is real, ongoing complexity for a single-maintainer project — the simpler and more honest fix is to remove it and rely on the same manually-invoked `docker compose run --rm app ruff check .` / `ruff format .` commands that are already the documented linting workflow. If working git-hook enforcement becomes worth the complexity later, it should be its own deliberately-scoped story, not bundled into a dependency-version bump.

### Ruff config — don't inherit ruff's defaults where they conflict with existing decisions

- **Quote style**: this repo is single-quote throughout, and `pyproject.toml`'s `skip-string-normalization = true` was a deliberate black setting to preserve that. Ruff's formatter defaults to double quotes. Set `quote-style = "preserve"` explicitly — don't let the migration silently flip the codebase's quoting convention as a side effect.
- **Line length**: stays 79, matching `black`'s current config and `.editorconfig`.
- **Rule selection**: start narrow (`select = ["E", "F", "W"]`, the flake8-equivalent set). Ruff ships 800+ rules across many additional categories (import sorting via `I`, docstring conventions via `D`, `flake8-bugbear` via `B`, etc.) — enabling those is a legitimate future improvement, but it's a separate decision with its own diff and its own discussion, not something to bundle into "swap the tool that runs the same rules we already had."

### Discovered during implementation: ruff format reformats Python code fences inside Markdown

`ruff format .`, unlike `black`, by default also formats fenced ```python code blocks embedded in `.md`/`.rst`/`.ipynb` files — not just `.py` files. This surfaced immediately: `_bmad-output/planning-artifacts/relaunch-architecture.md` contains Django model definitions as illustrative documentation, and the first `ruff format --diff .` run tried to reformat them (wrapping long field definitions, moving inline comments). Planning docs aren't meant to be enforced as compilable, lint-clean code, and `_bmad-output/` was never in scope for black (which never touched non-`.py` files at all). Fixed by adding `_bmad-output` to `[tool.ruff]`'s `exclude` list (Task 3.2). Worth remembering for any future story that adds more Markdown-with-code-fences under version control: check `ruff format --diff .` before assuming "it only touches Python files."

### Discovered during implementation: the "78 passed" baseline was inflated by a pytest.ini scoping bug

The story's drafted baseline (78 passed, 3 pre-existing `crawler` failures) turned out not to be reproducible. Investigating (per Task 7.3's instruction to investigate rather than assume pre-existing) found the real cause: `pytest.ini` had no `testpaths`/`--ignore` scoping, so bare `python -m pytest` recursively collects from the repo root — including `_bmad/`, the BMAD tooling framework's own bundled test suite. `_bmad/` is listed in both `.gitignore` and `.dockerignore`, so it's correctly excluded from the git repo and from the Docker image's `COPY . .` layer — but `docker-compose.yml`'s `app` service uses `volumes: - .:/app`, a bind mount that re-exposes the entire host working tree at runtime regardless of `.dockerignore` (which only governs image-build-time `COPY`). So `_bmad/`'s own test files were reachable inside `docker compose run --rm app python -m pytest` the whole time, and at least one of them (`_bmad/core/bmad-init/scripts/tests/test_bmad_init.py`) fails outright with `ModuleNotFoundError: No module named 'yaml'` — a dependency of the BMAD tooling itself, correctly never installed by this project.

This is independent of the pytest version bump — it's a pre-existing `pytest.ini` gap, not something Task 7's version change introduced. It was fixed here (not deferred) because it directly blocks this story's own validation gate (AC #8/Task 9.2 requires a reproducible baseline), by adding `--ignore=_bmad` to `pytest.ini`'s `addopts` — **this is the load-bearing fix** (verified: `pytest --ignore=_bmad` alone reproduces the full corrected result). `--ignore=_bmad-output` was added alongside it defensively, for consistency with the same ruff-exclude decision above (`_bmad-output` is BMAD-generated tooling output, not application code) — not because it fixes anything itself: it contains no test files, and unlike `_bmad` it isn't even gitignored (it's a tracked directory the story file itself lives in). The corrected, real, reproducible application-suite baseline is **10 passed, 3 pre-existing unrelated failures in `crawler/tests/test_utils.py`, 13 collected** — a much smaller number than "78," but the real one: this app currently has exactly two test files (`crawler/tests/test_utils.py`, `routes/tests/test_foundation.py`). Any future story quoting a test-suite baseline should use this corrected figure, not the "78 passed" figure from Story 1.1's own validation notes (which was almost certainly counting the same leaked `_bmad` tests without noticing).

### Testing Standards

`pytest` + `pytest-cov` per `pytest.ini`, now scoped correctly to exclude `_bmad`/`_bmad-output` (see Dev Notes above). This story bumps `pytest`, `pytest-cov`, and `pytest-sugar` together, and adds no new application tests of its own (it's tooling/config, not application code) — `factory-boy` is added but deliberately not used yet (Task 8.2). The pass/fail baseline going forward: **10 passed, 3 pre-existing unrelated failures in `crawler/tests/test_utils.py` (13 collected)**.

### References

- [Source: requirements.txt] — **pre-change baseline** (pins as they stood before this story, verified directly at drafting time): `requests==2.31.0`, `python-dotenv==1.0.0`, `python-telegram-bot==20.4`, `Scrapy==2.10.1`, `scrapy-djangoitem==1.1.1`, `black==23.7.0`, `flake8==6.1.0`, unpinned `pre-commit`, `pytest==7.0.1`, `pytest-cov==3.0.0`, `pytest-sugar==0.9.4`, `pytest-django==4.14.0`
- [Source: pyproject.toml] — **pre-change baseline**: `[tool.black]` config (line-length 79, `skip-string-normalization`, migrations excluded)
- [Source: .flake8] — **pre-change baseline** (file deleted by this story): ignore list (`E203, E266, E501, W503, F403, F401`) and migrations exclusion
- [Source: .pre-commit-config.yaml] — **pre-change baseline** (file deleted by this story): hook set removed, not replaced
- **Final state** (post-implementation, see Task checkboxes and File List above for full detail): `requirements.txt` now pins `requests==2.34.2`, `python-dotenv==1.2.3`, `pytest==9.1.1`, `pytest-cov==7.1.0`, `pytest-sugar==1.1.1`, `ruff==0.16.3`, `factory-boy==3.3.3`; `black`/`flake8`/`pre-commit` are gone. `pyproject.toml`'s `[tool.ruff]`/`[tool.ruff.lint]`/`[tool.ruff.format]` replaces `[tool.black]` (empty lint `ignore` list, `quote-style = "preserve"`, `_bmad-output` added to `exclude`). `.flake8` and `.pre-commit-config.yaml` no longer exist.
- [Source: Dockerfile] — confirmed no `git` package installed; confirmed Docker-only workflow (no host venv setup)
- [Source: README.md] — confirmed entire dev workflow is `docker compose run --rm app ...`; confirmed no `pre-commit install` step documented anywhere; "Linting / formatting" section is the one being updated to `ruff`
- [Source: app/settings.py `INSTALLED_APPS`] — confirmed `telegram_bot` is not a registered app; `crawler` is
- [Source: _bmad-output/planning-artifacts/relaunch-architecture.md#Infrastructure & monitoring] — `crawler/` retirement timing
- [Source: _bmad-output/planning-artifacts/relaunch-architecture.md#Project Structure & Boundaries] — `telegram_bot/` dormant/out-of-scope-for-v1 status
- Verified live during story drafting via PyPI JSON API (2026-08-19): `requests` `2.34.2`, `python-dotenv` `1.2.3`, `ruff` `0.16.3`, `pre-commit` `4.6.2` (moot — being removed), `pytest` `9.1.1`, `pytest-cov` `7.1.0`, `pytest-sugar` `1.1.1`, `factory-boy` `3.3.3`, `pytest-django` `4.14.0` (unchanged — already current), `whitenoise` `6.12.0` (unchanged — already current), `psycopg` `3.3.4` (unchanged — already current), Scrapy latest `2.17.0`, `scrapy-djangoitem` latest `1.1.1` (unchanged — unmaintained), `python-telegram-bot` latest `22.8` — all should be re-verified at implementation time, not trusted as still-current.

## Change Log

- 2026-08-19: Implemented all 9 tasks. `requests`/`python-dotenv` bumped; `black`+`flake8` replaced with `ruff` (empty ignore list — all 6 legacy flake8 ignores evaluated and dropped, none currently fire); `pre-commit` removed entirely; one-time `ruff format .` pass applied; `pytest`/`pytest-cov`/`pytest-sugar` bumped together; `factory-boy` added. Two issues found and fixed during implementation, beyond the story's original task list: (1) `ruff format` reformats Python code fences inside Markdown — excluded `_bmad-output` to protect planning-doc code samples; (2) `pytest.ini` had no collection-scope restriction, letting `_bmad/`'s own bundled test suite leak into `python -m pytest` via the bind-mounted `app` service — fixed with `--ignore=_bmad --ignore=_bmad-output`, which also corrected the story's baseline figure from an inflated "78 passed" to the real "10 passed, 3 pre-existing failures."

### Debug Log References

### Completion Notes List

- 2026-08-19: Story expanded post-drafting after a maintainer-directed dependency audit. Added: pre-commit removal (AC #7, reworked), pytest/pytest-cov/pytest-sugar bump (AC #8, new), factory-boy addition (AC #9, new). Confirmed via codebase grep that no currently-listed dependency is fully unused — see Dev Notes audit section.
- 2026-08-19: Implementation complete. All ACs satisfied. `ruff check .` and `ruff format --check .` both clean; full app test suite passes at the corrected baseline (10 passed, 3 pre-existing unrelated failures). Two out-of-task-list fixes were required to make validation reproducible — both documented in Dev Notes and disclosed here rather than silently folded in: the `_bmad-output` ruff exclude, and the `pytest.ini` collection-scope fix (which also corrected a wrong baseline figure inherited from drafting/Story 1.1).

### File List

- `requirements.txt` — modified: `requests` 2.31.0→2.34.2, `python-dotenv` 1.0.0→1.2.3, `pytest` 7.0.1→9.1.1, `pytest-cov` 3.0.0→7.1.0, `pytest-sugar` 0.9.4→1.1.1, added `factory-boy==3.3.3`, removed `black`/`flake8`/`pre-commit`, added `ruff==0.16.3`
- `pyproject.toml` — modified: `[tool.black]` replaced with `[tool.ruff]`/`[tool.ruff.format]`/`[tool.ruff.lint]`
- `pytest.ini` — modified: added `--ignore=_bmad --ignore=_bmad-output` to `addopts`
- `.flake8` — deleted
- `.pre-commit-config.yaml` — deleted
- `README.md` — modified: "Linting / formatting" section now documents `ruff` commands instead of `black`/`flake8`
- `crawler/middlewares.py` — modified: removed unused `itemadapter.is_item`/`ItemAdapter` imports and an orphaned comment (ruff F401)
- `crawler/spiders/sitp_spider.py` — modified: removed unused `re` import (ruff F401)
- `routes/management/commands/load_bus_stations.py` — modified: removed unused `CommandError` import (ruff F401)
- `app/urls.py` — modified: one-time `ruff format .` pass (blank line after module docstring)
- `manage.py` — modified: one-time `ruff format .` pass (blank line after module docstring)
