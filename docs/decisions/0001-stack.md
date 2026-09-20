# ADR 0001: Language, package manager, and publish target

Date: 2026-09-20
Status: accepted

## Context

The objective filed at #2 needs a stack before any of its later children —
the fixture, the data-source abstraction, the CLI, the eval suite — have
anything to build on. The objective owner already decided the language:
Python, because evaluating an agent is an explicit goal of this project and
the eval, statistical, and data tooling is stronger there than in the
alternative (TypeScript) this repository could otherwise have chosen. That
half of the decision is not re-litigated here; this ADR records it alongside
the two things the owner left open — the package manager, and what, if
anything, publishes this repository.

## Decision

**Language:** Python, `>=3.12`. Not re-decided, restated for the record.

**Package manager: [uv](https://docs.astral.sh/uv/).** It resolves and
installs dependencies, manages the virtual environment, and pins the
interpreter version, from one tool and one lockfile, which is fewer moving
parts than pip + `venv` + `pip-tools` wired together by hand. It reads a
standard `pyproject.toml` (PEP 621), so nothing about the project shape is
uv-specific, and it has a maintained GitHub Actions integration
(`astral-sh/setup-uv`) for wiring into this repository's CI once the
placeholder gate is replaced.

Build backend: [hatchling](https://hatch.pypa.io/), a standard PEP 517
backend with no project-specific configuration needed beyond pointing it at
the `src/` package.

**Publish target: none yet.** This objective is a vertical slice per its own
scope (see #2) — a library and CLI exercised locally and in CI, not a
published artifact. Nothing builds this repository anywhere other than the
CI gate today. When a release target is chosen (a package index, a
container, anything else), that choice gets its own ADR recording what
builds it, how that differs from what CI runs, and what covers the
difference — per this repository's `CLAUDE.md`.

## Consequences

This makes it easy to add and pin dependencies (`uv add`), reproduce the
exact environment CI used (`uv sync`), and run project commands without
activating a virtualenv by hand (`uv run <command>`).

It makes it harder to fall back to bare `pip install` if a contributor does
not have `uv` on their machine — the install step in `CLAUDE.md` now
requires it. That is treated as an acceptable trade for one lockfile instead
of a bespoke pip/venv setup that has no lockfile at all today.

**`uv.lock` is not committed in this pull request.** The sandbox this
scaffold was built in refuses execution of `python3` beyond `python3
--version` — `pip3 --version`, `python3 -m pip`, `python3 -m venv`, and
`python3 <script>.py` were all tried and all refused before this was
accepted as a hard constraint of the environment rather than something to
route around. `uv` itself could not be installed or run here, so no lockfile
could be generated and verified without inventing one that nothing checked.
The person wiring the real `commands:` block onto this PR's branch should
run `uv sync` there — it generates `uv.lock` from `pyproject.toml` on first
run — and commit the result, or a follow-up commit on this branch should.
Until then, `uv sync` is the install command and resolves dependencies
fresh each time, which is correct but unpinned.

It rules out, for now, choosing a release target that assumes a different
packaging tool (e.g. a `setup.py`-based flow); revisiting the package
manager later is a new ADR, not an edit to this one.

## Alternatives rejected

- **pip + `venv` + `requirements.txt`** — the standard library baseline, and
  the reason this project did not stay there is that it has no lockfile
  story: `pip freeze` captures what happens to be installed, not what was
  asked for, and drifts silently between environments. Rejected in favour of
  a tool with a real lockfile.
- **Poetry** — a credible, popular alternative with the same lockfile
  guarantee. Rejected for being slower in practice and for using a
  Poetry-specific `[tool.poetry]` project shape historically, rather than the
  now-standard PEP 621 `[project]` table that uv reads directly — one fewer
  thing to translate if the package manager is ever revisited.
- **pip-tools** — compiles a lockfile from a requirements file but still
  leaves environment and interpreter management to be wired up separately.
  Rejected for being three tools glued together where uv is one.
