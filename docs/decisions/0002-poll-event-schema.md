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

**Value domains, not just field names.** The first version of this ADR typed
the fields and stopped there; a pull request review on #6 (2026-09-20) caught
that the committed fixture used values the real product cannot emit —
`direction` of `"up"`/`"down"` instead of a swipe's `"left"`/`"right"`,
`variant` of `"control"`/`"treatment"` instead of the arm names `"a"`/`"b"`,
and `option` of bare `"A"`/`"B"` instead of the pair's actual labels. Those
values were type-valid and passed every criterion in #6, which is why the
review calls this "wrong in a way that looks right" rather than a crash.
`VoteEvent.__post_init__` and `VariantSeenEvent.__post_init__` now reject a
`direction` or `variant` outside `VALID_DIRECTIONS = {"left", "right"}` /
`VALID_VARIANTS = {"a", "b"}`, the same way they already reject a wrong
`type`.

`option` is drawn from each pair's own two labels rather than a shared `"A"`/
`"B"` placeholder: `pair-1` is `"Coffee"`/`"Tea"`, `pair-2` is `"Cats"`/
`"Dogs"` — verified directly against `src/lib/poll.ts` in
`chamaya00/analytics-practice` by the reviewer, not re-derived here (this
repository's build still does not depend on that one). The fixture now
commits to only those two pairs rather than the earlier three: this sandbox
cannot reach that reference repository to read a third pair's real labels
(recorded in `docs/memory/engineer.md`), and inventing one would repeat the
exact defect this revision fixes — a value that is type-valid but not
something the product emits. Two pairs already satisfies #6's "multiple
pairs" criterion; a later run with access to the reference repo can extend to
`pair-3` in its own commit, regenerating both fixture and ground truth
together as this file already requires.

`src/data_agent/fixtures.py` generates the fixture by cycling deterministic
indices rather than a seeded PRNG: a `variant_seen` event on every fifth `i`,
and for each vote a `pair`/`direction` pair keyed off the count of vote
events seen so far (not `i` directly), so a swipe direction doesn't lock to
one pair and both options of both pairs appear in the fixture. The output is
fully specified by arithmetic on an index, so it can be recomputed and
checked by hand without executing anything — which is exactly what produced
the 24-event fixture committed at `fixtures/poll_events.json`.

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
