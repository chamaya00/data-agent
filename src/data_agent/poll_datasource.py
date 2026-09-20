"""Read-only data-source abstraction over a list of PollEvents.

Exposes a schema description, a filtered query, and sampling. The row cap
and timeout are enforced here, in the abstraction itself, rather than left
to a prompt asking a model to behave - see issue #4. A caller (the CLI, or
anything else built on this) cannot opt out of either guarantee; it can only
choose a larger or smaller cap/timeout at construction time.
"""

from __future__ import annotations

import dataclasses
import time
from collections.abc import Callable, Iterable, Mapping, Sequence

from data_agent.poll_events import (
    VARIANT_SEEN,
    VOTE,
    PollEvent,
    VariantSeenEvent,
    VoteEvent,
    poll_event_from_dict,
)

DEFAULT_ROW_CAP = 1000
DEFAULT_TIMEOUT_SECONDS = 5.0

_EVENT_TYPES: Mapping[str, type] = {VOTE: VoteEvent, VARIANT_SEEN: VariantSeenEvent}


class RowCapExceeded(Exception):
    """Raised when a query would return more rows than the configured cap."""


class QueryTimeout(Exception):
    """Raised when a query runs past the configured timeout."""


class PollEventDataSource:
    """Read-only access to a fixed sequence of PollEvents."""

    def __init__(
        self,
        events: Sequence[PollEvent],
        *,
        row_cap: int = DEFAULT_ROW_CAP,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._events = tuple(events)
        self._row_cap = row_cap
        self._timeout_seconds = timeout_seconds
        self._clock = clock

    @staticmethod
    def schema() -> dict[str, dict[str, str]]:
        """Return the PollEvent shape by field name and type.

        Introspects the dataclasses directly - no event is read and no
        query runs, so this is available even before any data is loaded.
        """
        return {
            event_type: {field.name: field.type for field in dataclasses.fields(event_cls)}
            for event_type, event_cls in _EVENT_TYPES.items()
        }

    def query(
        self,
        event_type: str | None = None,
        filters: Mapping[str, str] | None = None,
    ) -> list[PollEvent]:
        """Return events matching `event_type` and all of `filters`.

        Raises `QueryTimeout` if scanning runs past the configured timeout,
        and `RowCapExceeded` if the match count would exceed the row cap -
        both checked while scanning, not after the fact.
        """
        filters = filters or {}
        deadline = self._clock() + self._timeout_seconds
        results: list[PollEvent] = []
        for event in self._events:
            if self._clock() > deadline:
                raise QueryTimeout(f"query exceeded its {self._timeout_seconds}s timeout")
            if event_type is not None and getattr(event, "type", None) != event_type:
                continue
            if not all(getattr(event, key, None) == value for key, value in filters.items()):
                continue
            results.append(event)
            if len(results) > self._row_cap:
                raise RowCapExceeded(f"query exceeded its row cap of {self._row_cap}")
        return results

    def sample(self, n: int) -> list[PollEvent]:
        """Return up to `n` events, truncated to the row cap."""
        return list(self._events[: min(n, self._row_cap)])

    def distinct_values(self, field: str, event_type: str | None = None) -> frozenset[str]:
        """Return the distinct values `field` actually takes in this data.

        This is how a caller learns a real domain (e.g. which `option`
        labels exist) instead of guessing one - subject to the same cap
        and timeout as any other query, since it scans the same data.
        """
        events = self.query(event_type=event_type)
        return frozenset(
            getattr(event, field) for event in events if hasattr(event, field)
        )


def load_events(raw_events: Iterable[Mapping[str, object]]) -> list[PollEvent]:
    """Build PollEvents from raw dict records (e.g. a parsed fixture file)."""
    return [poll_event_from_dict(dict(record)) for record in raw_events]
