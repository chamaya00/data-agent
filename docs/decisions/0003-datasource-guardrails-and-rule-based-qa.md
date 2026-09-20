# ADR 0003: Data-source guardrails and rule-based question answering

Date: 2026-09-20
Status: accepted

## Context

Issue #4 needs a data-source abstraction over the committed `PollEvent`
fixture (schema description, a read-only query, and sampling) that enforces
a row cap and a timeout itself, and a CLI that answers a plain-language
question or says it cannot. `dependencies = []` in `pyproject.toml` is
unchanged by this issue: there is no model SDK, no API key, and no network
access available to call one from this sandbox, and the issue's own scope
note defers "the eval suite (question set, pass rate, repeated runs)" to a
later child rather than asking this one to wire up a real model.

This sandbox also still refuses to execute anything beyond a plain
`--version` check - not just Python (`python3 -c "print(1)"`), but `ruff`
and `uv` directly (`ruff --version`, `uv --version`) all return "This
command requires approval" with nobody to grant it, the same failure mode
already recorded in `docs/memory/engineer.md` from an earlier issue. That
constraint is restated here because it means every test in this issue's
diff is verified by hand against the committed fixture, not by a local run.

## Decision

`src/data_agent/poll_datasource.py` exposes `PollEventDataSource.schema()`
as a `staticmethod` that introspects `VoteEvent`/`VariantSeenEvent` via
`dataclasses.fields()` - it never touches an instance's events, so it needs
no query to have run first. `query(event_type, filters)` scans the
underlying tuple of events, checking a caller-supplied `clock()` against a
deadline on every iteration and raising `QueryTimeout` the moment it is
passed, and raising `RowCapExceeded` the moment a match count would exceed
`row_cap` - both while scanning, not as a post-hoc check. `clock` defaults
to `time.monotonic` but is an injectable dependency so a test can force a
timeout deterministically (two fixed return values: one past the deadline)
instead of needing the query to actually run slowly, which a 24-event
in-memory fixture cannot be made to do without an artificial delay.
`distinct_values(field, event_type)` is the intended way for a caller to
learn a real domain (e.g. which `option` labels exist) instead of
hardcoding one that could drift from the fixture; it is built on `query()`
so it inherits the same cap and timeout rather than bypassing them.

`src/data_agent/poll_qa.py` answers a question by matching it against two
known shapes ("how many votes did `<dimension>` `<value>` get?" and "which
option won among/for `<dimension>` `<value>`?"), then validates the named
value against `distinct_values()` before building any query. A value
outside the fixture's real domain - a variant, direction, option, or pair
that does not appear in the data - is answered by stating non-answerability
and never runs a query for it, matching issue #4's requirement that a value
outside the domain restated in #6 is exactly the "fixture cannot answer"
case. A tie in "which option won" is treated the same way, since a single
winner cannot be named from a tie. `src/data_agent/cli.py` wires this to
`data-agent <question>` (registered as a console script), printing the
query that ran (or would have run) before the answer, and exiting 1 when
the question could not be answered.

## Consequences

Answering a question never depends on a call this sandbox cannot make or
verify, and every answer is auditable: the query printed alongside it is
the literal call made against `PollEventDataSource`, not a paraphrase. The
trade-off is coverage - only the two question shapes above are understood,
and anything else (including a valid question phrased differently) is
"I can't answer that: I don't recognize this question's shape," which is
indistinguishable in the output from a genuinely out-of-domain value. The
eval suite (the next child, per issue #4's own scope note) is where a wider
question set would surface how much that costs and whether a real model
belongs in this loop instead.

## Alternatives rejected

- **Calling an actual language model to translate the question into a
  query** - ruled out by scope: this issue explicitly defers evaluating
  question-answering breadth to the next child, and nothing in
  `pyproject.toml` gives this sandbox a model to call or a way to verify
  one deterministically today.
- **Truncating instead of raising on row-cap overflow in `query()`** -
  `sample()` truncates (it is explicitly a "give me up to N" call), but
  `query()` raises: a caller filtering data should learn its query matched
  more than the cap allows, not silently receive a partial answer that
  looks complete.
- **Testing the timeout with a real sleep** - flaky under CI load and slow
  by construction; an injectable `clock` makes the timeout path exercise
  deterministically and fast.
