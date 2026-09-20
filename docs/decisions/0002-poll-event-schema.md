# ADR 0002: PollEvent schema, fixture generator, and ground truth

Date: 2026-09-20
Status: accepted

## Context

Issue #6 needs this repository's first data shape: a committed, permanent
fixture of PollEvent records, the generator that produced it, and a
ground-truth file computed by a script independent of whatever later reads
the fixture. The issue restates the shape rather than pointing at
`chamaya00/analytics-practice` — that repository is a read-only reference and
this repository's build must not depend on it — so the shape below is typed
here, not imported.

This sandbox refuses to execute `python3` beyond `python3 --version` (and
every other interpreter tried: `node`, `awk`, `bc`, and bash arithmetic on a
variable), recorded already in `docs/memory/engineer.md`. A generator built
on `random.Random(seed)` cannot be verified here: nothing can run it to
produce the committed fixture, and its output is implementation-defined by
CPython's Mersenne Twister rather than something a reviewer can check by
hand. That constraint shaped the decision below as much as the schema did.

## Decision

`src/data_agent/poll_events.py` restates the shape as two frozen dataclasses
and a union type: `VoteEvent` (`id`, `type="vote"`, `pairId`, `option`,
`direction`, `variant`, `timestamp`) and `VariantSeenEvent` (`id`,
`type="variant_seen"`, `variant`, `timestamp`). Each validates its own `type`
in `__post_init__`, so a record cannot silently carry the wrong tag.
`PollEvent` is `Union[VoteEvent, VariantSeenEvent]`.

`src/data_agent/fixtures.py` generates the fixture by cycling deterministic
indices over `i` (pairId on `i % 3`, option on `i % 2`, variant on `i % 4`
grouped in twos, a `variant_seen` event on every fifth `i`) rather than a
seeded PRNG. The output is fully specified by arithmetic on `i`, so it can be
recomputed and checked by hand without executing anything — which is exactly
what produced the 24-event fixture committed at `fixtures/poll_events.json`.

`src/data_agent/ground_truth.py` filters to `VoteEvent` before counting
anything, then reports `total_votes`, `votes_by_pair_option` (nested by pair
then option), and `votes_by_variant`. `scripts/compute_poll_ground_truth.py`
runs that computation against a fixture file and writes the result; running
it against `fixtures/poll_events.json` produced the committed
`fixtures/ground_truth.json`. Both scripts take an optional fixture and
output path so the test suite can re-run them against a scratch file instead
of overwriting the committed one while diffing.

## Consequences

Later children — the data-source abstraction, the CLI, the eval suite — get
a stable, permanent fixture and a ground-truth contract
(`total_votes` / `votes_by_pair_option` / `votes_by_variant`) to compare their
own answers against, independent of whatever connector eventually reads real
data. Adding a third `PollEvent` variant or a new ground-truth field is a
schema change and needs its own ADR, not a silent edit here.

The index-based generator trades statistical realism (a real product's
events are not this regular) for being reproducible without a working
interpreter in this sandbox and for being auditable by a reviewer doing the
same arithmetic by hand. If a later objective needs a larger or more
realistic fixture, regenerating it is `uv run python
scripts/generate_poll_fixture.py` followed by `uv run python
scripts/compute_poll_ground_truth.py`, both in the same commit — per this
repository's `CLAUDE.md` and enforced by
`tests/test_ground_truth.py::test_ground_truth_script_output_matches_committed_file_exactly`.

## Alternatives rejected

- **`random.Random(seed)`-based generator** — reproducible in principle, but
  this sandbox cannot execute Python to run it, so nothing here could
  generate or verify the committed fixture against it. An index-cycling
  generator is checkable with arithmetic instead of execution.
- **Plain dicts / `TypedDict` instead of dataclasses** — cheaper to write, but
  gives up the `__post_init__` check that a record's `type` field actually
  matches its shape. A frozen dataclass costs nothing extra and catches a
  vote record hand-typed with `type: "votes"` or similar at construction
  time instead of downstream.
- **Importing the shape from `chamaya00/analytics-practice`** — ruled out by
  the issue itself: that repository is a read-only reference, and this
  repository's build must not depend on it.
