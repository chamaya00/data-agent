"""Rule-based question answering over a PollEventDataSource.

There is no model in this loop: a question is matched against a small set
of known shapes and its named values are checked against what the fixture
actually contains (see `PollEventDataSource.distinct_values`) before any
query runs. A question whose shape isn't recognized, or that names a value
outside the fixture's domain - a variant, direction, option, or pair that
doesn't exist - is answered by saying so, never by guessing a number. The
query that was (or would have been) run is always reported alongside the
answer, so a person can tell whether to trust it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from data_agent.poll_datasource import PollEventDataSource
from data_agent.poll_events import VOTE

# Plain-language dimension name -> the PollEvent field it filters on.
_DIMENSION_FIELDS = {
    "variant": "variant",
    "direction": "direction",
    "option": "option",
    "pair": "pairId",
}

_COUNT_RE = re.compile(
    r"^how many votes did (variant|direction|option|pair)\s+(.+?)\s+get\??$",
    re.IGNORECASE,
)
_WINNER_RE = re.compile(
    r"^which option won (?:among|for)\s+(variant|direction|pair)\s+(.+?)\??$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Answer:
    text: str
    query: str
    answerable: bool


def answer_question(question: str, data_source: PollEventDataSource) -> Answer:
    """Answer a plain-language question, or say it cannot be answered."""
    question = question.strip()

    match = _COUNT_RE.match(question)
    if match:
        return _answer_count(match.group(1).lower(), match.group(2), data_source)

    match = _WINNER_RE.match(question)
    if match:
        return _answer_winner(match.group(1).lower(), match.group(2), data_source)

    return Answer(
        text="I can't answer that: I don't recognize this question's shape.",
        query="(no query - the question did not match a known shape)",
        answerable=False,
    )


def _resolve_value(dimension: str, raw_value: str, data_source: PollEventDataSource) -> str | None:
    """Normalize and validate a named value against what the fixture holds.

    Returns None (rather than raising) when the value isn't in the domain,
    since the caller needs the field name either way to report the query.
    """
    field = _DIMENSION_FIELDS[dimension]
    value = raw_value.strip().strip("'\"").rstrip("?.!")
    known_values = data_source.distinct_values(field, event_type=VOTE)
    return value if value in known_values else None


def _answer_count(dimension: str, raw_value: str, data_source: PollEventDataSource) -> Answer:
    field = _DIMENSION_FIELDS[dimension]
    value = _resolve_value(dimension, raw_value, data_source)
    if value is None:
        return Answer(
            text=f"I can't answer that: {dimension} {raw_value.strip()!r} is not a value "
            f"this fixture's {field!r} field ever takes.",
            query=f"(no query - {dimension} {raw_value.strip()!r} is outside the fixture's domain)",
            answerable=False,
        )

    query_desc = f"query(event_type={VOTE!r}, filters={{{field!r}: {value!r}}})"
    votes = data_source.query(event_type=VOTE, filters={field: value})
    return Answer(text=str(len(votes)), query=query_desc, answerable=True)


def _answer_winner(dimension: str, raw_value: str, data_source: PollEventDataSource) -> Answer:
    field = _DIMENSION_FIELDS[dimension]
    value = _resolve_value(dimension, raw_value, data_source)
    if value is None:
        return Answer(
            text=f"I can't answer that: {dimension} {raw_value.strip()!r} is not a value "
            f"this fixture's {field!r} field ever takes.",
            query=f"(no query - {dimension} {raw_value.strip()!r} is outside the fixture's domain)",
            answerable=False,
        )

    query_desc = f"query(event_type={VOTE!r}, filters={{{field!r}: {value!r}}})"
    votes = data_source.query(event_type=VOTE, filters={field: value})

    counts: dict[str, int] = {}
    for vote in votes:
        counts[vote.option] = counts.get(vote.option, 0) + 1

    if not counts:
        return Answer(
            text="I can't answer that: no votes match that filter.",
            query=query_desc,
            answerable=False,
        )

    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    top_count = ranked[0][1]
    winners = sorted(option for option, count in counts.items() if count == top_count)
    if len(winners) > 1:
        return Answer(
            text=f"I can't answer that: {winners} are tied at {top_count} votes each.",
            query=query_desc,
            answerable=False,
        )
    return Answer(text=winners[0], query=query_desc, answerable=True)
