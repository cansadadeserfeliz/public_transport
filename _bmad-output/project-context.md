---
project_name: 'public_transport'
user_name: 'Vera'
date: '2026-08-02'
sections_completed: ['technology_stack', 'language_rules']
existing_patterns_found: 7
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python** 3.11
- **Django** 4.2.4 — SQLite (dev)
- **Scrapy** 2.10.1 + **scrapy-djangoitem** 1.1.1 — pipeline writes directly into Django ORM models, no separate scraped-data schema
- **python-telegram-bot** 20.4
- **requests** 2.31.0, **python-dotenv** 1.0.0
- **pytest** 7.0.1 + pytest-cov (coverage collection is mandatory — `pytest.ini` runs with `--cov=./ --no-cov-on-fail`) + pytest-sugar
- **black** 23.7.0 (line-length 79, `skip-string-normalization`), **flake8** 6.1.0, **pre-commit**

## Critical Implementation Rules

### Language-Specific Rules

- One import per line — never combine multiple names from the same module into one `from x import a, b, c`.
- 79-char line length, enforced by black (not flake8 — flake8 ignores E501). Run black rather than hand-wrapping.
- Google-style `Args:`/`Returns:`/`Raises:` docstrings on public service functions where the signature isn't self-explanatory; skip on trivial functions.
- Use `@dataclass` for typed in-memory value objects (API responses, parsed data) instead of dicts, when the data isn't a Django model.

_Documented after discovery phase_