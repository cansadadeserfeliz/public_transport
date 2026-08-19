# Story 6.1: Dependency Modernization & Ruff Migration

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

<!--
Not derived from relaunch-epics.md — this is maintainer-initiated tooling/dependency
debt, not tied to any PRD FR. Tracked as its own epic bucket (epic-6) in
sprint-status.yaml so it's visible without disturbing the FR-driven Epic 1-5
numbering. Not required for MVP; pull it into a sprint whenever it's convenient,
independent of Epic 1-5 sequencing.
-->

## Story

As a maintainer,
I want the dependencies Story 1.1 deliberately left untouched brought current where it's actually worth it, and `black`+`flake8` consolidated onto `ruff`,
so that the project isn't running years-old packages for no reason and isn't paying for two overlapping lint/format tools where one now does both, faster.

## Acceptance Criteria

1. **Given** `requests` is pinned at `2.31.0` (2023) and `python-dotenv` at `1.0.0` (2023), **when** this story lands, **then** both are bumped to their current stable release, verified against their actual changelogs for breaking changes (neither is expected to have any affecting this codebase's usage).
2. **Given** `black==23.7.0` and `flake8==6.1.0` are both installed and configured (`pyproject.toml`, `.flake8`, `.pre-commit-config.yaml`), **when** this story lands, **then** both are replaced by a single `ruff` dependency doing both lint and format, configured in `pyproject.toml` under `[tool.ruff]`/`[tool.ruff.lint]`/`[tool.ruff.format]`, with `.flake8` deleted and `.pre-commit-config.yaml`'s black/flake8 hooks replaced by `ruff-pre-commit`'s `ruff-check` and `ruff-format` hooks.
3. **And** the ruff config preserves this repo's actual existing conventions — 79-char line length, single-quote strings (not double) — rather than adopting ruff's defaults wholesale; `routes/migrations/` (what remains of it) stays excluded, matching the current black/flake8 exclusion.
4. **And** each of flake8's currently-blanket-ignored codes (`E203`, `E266`, `E501`, `W503`, `F403`, `F401`) is individually re-evaluated against what ruff actually flags in this codebase — carried forward only if it still fires on real code, not copied forward by default. (Confirmed during story drafting: there are zero `import *` statements anywhere in the repo today, so the `F403` ignore has nothing to suppress — do not carry it forward without first checking whether ruff's `F401`/`F403` surface anything real.)
5. **And** a one-time `ruff format .` pass across the whole existing codebase lands as its own dedicated commit, separate from the tooling/config change itself, so the mechanical reformatting diff is reviewable independently of the actual config decisions.
6. **Given** `python-telegram-bot==20.4` and `Scrapy==2.10.1`/`scrapy-djangoitem==1.1.1`, **when** this story is scoped, **then** neither is bumped as part of this story (see Dev Notes — both are deliberately excluded, not overlooked).
7. **And** `pre-commit` (currently unpinned in `requirements.txt`) gets an explicit version pin for reproducibility, matching the pattern used for every other dependency in the file.

## Tasks / Subtasks

- [ ] Task 1: Bump the two dependencies actually worth bumping (AC: #1)
  - [ ] 1.1 Verify current stable versions at implementation time (`pip index versions requests`, `pip index versions python-dotenv`) rather than trusting a stale pin — as of story drafting, `requests` was around `2.34.x` and `python-dotenv` around `1.2.x`, but ruff/PyPI move fast enough that these should be re-checked, not copy-pasted blind
  - [ ] 1.2 Update `requirements.txt`, rebuild, run the full test suite — neither library is expected to need any code changes in this repo (no deprecated `requests` API usage, `python-dotenv`'s `load_dotenv()` call signature added in Story 1.1 is stable across 1.x)

- [ ] Task 2: Explicitly scope out Scrapy/scrapy-djangoitem and python-telegram-bot (AC: #6)
  - [ ] 2.1 Do not bump `Scrapy`, `scrapy-djangoitem`, or `python-telegram-bot` in this story. Document why directly in the PR description so a future reviewer doesn't assume it was an oversight: `scrapy-djangoitem` is unmaintained (still at `1.1.1`, its last release, with no newer version to move to) and `crawler/` — the only app that uses it — is explicitly scheduled for retirement once Story 1.3's GTFS pipeline is confirmed working (`relaunch-architecture.md`). Bumping `Scrapy` alone without a matching `scrapy-djangoitem` release risks breaking `crawler` for an app that's being deleted soon anyway. `telegram_bot/` is separately marked `UNCHANGED — dormant, out of scope for v1 (Phase 2 revival)` in the same architecture doc — bumping `python-telegram-bot` from v20 to the current v22.x line means crossing two major versions of an actively-developed library for a component nothing currently exercises.
  - [ ] 2.2 If either app is later revived (crawler's replacement falling through, or Phase 2's Telegram bot work), its dependency bump belongs to whatever story revives it — not backfilled here speculatively.

- [ ] Task 3: Configure ruff in `pyproject.toml` (AC: #2, #3)
  - [ ] 3.1 Add `ruff` to `requirements.txt`, pinned to its current stable release (verify at implementation time — was `~0.15.19` as of story drafting; ruff ships very frequently, don't trust that number without checking)
  - [ ] 3.2 Remove the `[tool.black]` section from `pyproject.toml`; add `[tool.ruff]` (`line-length = 79`, `target-version = "py311"`, `exclude` list carrying forward the current black exclusion — `.git`, `.hg`, `.mypy_cache`, `.tox`, `.venv`, `_build`, `buck-out`, `build`, `dist`, `migrations`)
  - [ ] 3.3 Add `[tool.ruff.format]` with `quote-style = "preserve"` — the codebase uses single quotes throughout (confirmed: every file touched in Story 1.1, plus `routes/models.py`, `routes/views.py`, etc.) and black's `skip-string-normalization = true` was set specifically to avoid forcing a quote-style rewrite; ruff's default `quote-style` is `"double"`, which would silently violate that existing decision and reformat the entire codebase's quoting if left at default
  - [ ] 3.4 Add `[tool.ruff.lint]` starting from `select = ["E", "F", "W"]` (flake8-equivalent coverage: pycodestyle errors/warnings + pyflakes) — do not enable ruff's much larger additional rule catalog (import sorting, pydocstyle, bugbear, etc.) as part of this story; that's a separate, larger decision the maintainer should make deliberately, not inherit as a side effect of the migration
  - [ ] 3.5 For each of the 6 flake8-ignored codes, decide per Task 4 below and encode only the ones still needed in `[tool.ruff.lint] ignore = [...]`

- [ ] Task 4: Re-evaluate flake8's ignored codes against ruff, per-code (AC: #4)
  - [ ] 4.1 Run `ruff check .` with nothing ignored yet, on a throwaway branch/locally, and read what actually fires for each of: `E203` (whitespace before `:`, a black-vs-pycodestyle disagreement — likely still needed since ruff's formatter has the same disagreement with pycodestyle), `E266` (`##` block comments), `E501` (line-too-long — currently ignored because black already enforces line length; ruff's formatter plays the same role, so this should stay ignored for the same reason), `W503` (line break before binary operator — a black-style preference, likely still applicable)
  - [ ] 4.2 For `F403` (star imports) — confirmed zero `import *` in the repo today (verified via `grep -rn "import \*"` during story drafting); do not blanket-carry this ignore forward. If `ruff check` doesn't flag anything under `F403` with the ignore removed, leave it **off** the ignore list — there's nothing to suppress, and keeping an unnecessary ignore just hides future accidental star-imports
  - [ ] 4.3 For `F401` (unused imports) — this one is the most likely to surface real, previously-hidden issues. Run `ruff check --select F401` and actually look at what comes back rather than reflexively re-adding it to `ignore`; a Django app's `apps.py`/`__init__.py` sometimes has legitimate unused-looking imports (e.g. for side-effect registration) — those need `# noqa: F401` inline, not a blanket file-wide or repo-wide ignore
  - [ ] 4.4 Document the final ignore list's reasoning inline in `pyproject.toml` as a comment next to `ignore = [...]`, so the next person doesn't have to redo this investigation

- [ ] Task 5: Update `.pre-commit-config.yaml` (AC: #2)
  - [ ] 5.1 Remove the `psf/black` and `PyCQA/flake8` repo entries
  - [ ] 5.2 Add `astral-sh/ruff-pre-commit` at its current tag (verify latest — was around `v0.15.22` as of story drafting), with both the `ruff-check` hook (`args: ["--fix"]` optional, maintainer's call) and `ruff-format` hook
  - [ ] 5.3 Keep the existing `pre-commit/pre-commit-hooks` entries (`trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-added-large-files`) untouched — unrelated to this migration

- [ ] Task 6: Delete `.flake8`, run the one-time reformat, pin `pre-commit` (AC: #2, #5, #7)
  - [ ] 6.1 Delete `.flake8` — fully superseded by `[tool.ruff.lint]` in `pyproject.toml`
  - [ ] 6.2 Run `ruff format .` across the whole repo once, and commit the result **separately** from the config/tooling changes above (AC #5) — expect a real diff even with matching line-length/quote-style, since ruff's formatter is "black-compatible," not byte-identical to black in every edge case
  - [ ] 6.3 Pin `pre-commit` in `requirements.txt` to its current version (was `4.6.2` as installed during Story 1.1's Docker build — verify still current) instead of leaving it unpinned

- [ ] Task 7: Validate (Testing Standards)
  - [ ] 7.1 `ruff check .` and `ruff format --check .` both pass clean
  - [ ] 7.2 Full `pytest` suite still passes with the same baseline as Story 1.1 (78 passed, 3 pre-existing unrelated `crawler/tests/test_utils.py` failures — confirm the count hasn't changed, since a changed count would mean this story accidentally touched something in scope for a different story)
  - [ ] 7.3 `pre-commit run --all-files` passes (proves the new hook config actually works, not just that the underlying tools do)

## Dev Notes

### Why Scrapy/scrapy-djangoitem and python-telegram-bot are explicitly out of scope

This is the single most important scoping decision in this story, and it's easy to get wrong by treating "modernize dependencies" as "bump everything":

- `scrapy-djangoitem` has had no PyPI release in over a year and is classified inactive/unmaintained — the currently-pinned `1.1.1` **is** the latest version. There's nothing to bump it to.
- `crawler/` (the only consumer of both `Scrapy` and `scrapy-djangoitem`) is explicitly scheduled for retirement once Story 1.3's GTFS pipeline is confirmed working (`relaunch-architecture.md` → Infrastructure & monitoring: *"`crawler/` (Scrapy) app is retired once the GTFS pipeline is confirmed working — left in place until then, not extended with new spiders"*). Bumping `Scrapy` alone (its 2.13.x line changed `start_requests()` to an async `start()`, among other things) without a matching `scrapy-djangoitem` release is a real regression risk against code with a known, near-term deletion date. Not worth it.
- `telegram_bot/` is separately marked `UNCHANGED — dormant, out of scope for v1 (Phase 2 revival)` in the architecture doc's Project Structure & Boundaries. `python-telegram-bot` v20→v22 crosses two major version lines of an actively-developed library. Doing that work now, for a component nothing in v1 exercises, is pure risk with no near-term payoff — it belongs to whatever story actually revives the bot in Phase 2, when it can be tested against real usage.

### Ruff config — don't inherit ruff's defaults where they conflict with existing decisions

- **Quote style**: this repo is single-quote throughout, and `pyproject.toml`'s `skip-string-normalization = true` was a deliberate black setting to preserve that. Ruff's formatter defaults to double quotes. Set `quote-style = "preserve"` explicitly — don't let the migration silently flip the codebase's quoting convention as a side effect.
- **Line length**: stays 79, matching `black`'s current config and `.editorconfig`.
- **Rule selection**: start narrow (`select = ["E", "F", "W"]`, the flake8-equivalent set). Ruff ships 800+ rules across many additional categories (import sorting via `I`, docstring conventions via `D`, `flake8-bugbear` via `B`, etc.) — enabling those is a legitimate future improvement, but it's a separate decision with its own diff and its own discussion, not something to bundle into "swap the tool that runs the same rules we already had."

### Testing Standards

Same as Story 1.1: `pytest` + `pytest-cov` per `pytest.ini`. This story adds no new tests of its own (it's tooling/config, not application code) — validation is running the existing suite and confirming the pass/fail count is unchanged from Story 1.1's baseline (78 passed / 3 pre-existing unrelated failures in `crawler/tests/test_utils.py`).

### References

- [Source: requirements.txt] — current pins verified directly: `requests==2.31.0`, `python-dotenv==1.0.0`, `python-telegram-bot==20.4`, `Scrapy==2.10.1`, `scrapy-djangoitem==1.1.1`, `black==23.7.0`, `flake8==6.1.0`, unpinned `pre-commit`
- [Source: pyproject.toml] — current `[tool.black]` config (line-length 79, `skip-string-normalization`, migrations excluded)
- [Source: .flake8] — current ignore list (`E203, E266, E501, W503, F403, F401`) and migrations exclusion
- [Source: .pre-commit-config.yaml] — current hook set to be replaced
- [Source: _bmad-output/planning-artifacts/relaunch-architecture.md#Infrastructure & monitoring] — `crawler/` retirement timing
- [Source: _bmad-output/planning-artifacts/relaunch-architecture.md#Project Structure & Boundaries] — `telegram_bot/` dormant/out-of-scope-for-v1 status
- Verified live during story drafting (Aug 2026): scrapy-djangoitem inactive/unmaintained at 1.1.1 (no newer release exists); Scrapy latest ~2.13.4; python-telegram-bot latest ~22.7; requests latest ~2.34.2; python-dotenv latest ~1.2.x; ruff latest ~0.15.19; ruff-pre-commit latest ~v0.15.22; pre-commit latest 4.6.2 — all should be re-verified at implementation time, not trusted as still-current

## Change Log

### Debug Log References

### Completion Notes List

### File List
