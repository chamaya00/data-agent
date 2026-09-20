"""PollEvent shape, restated in this repository.

Restated rather than imported from chamaya00/analytics-practice: that repo is
a read-only reference and this repository's build must not depend on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union

VOTE = "vote"
VARIANT_SEEN = "variant_seen"

# The real product swipes a card left or right and splits traffic into two
# arms named "a"/"b" - see docs/decisions/0002-poll-event-schema.md. A value
# outside these sets is type-valid but describes an interaction the product
# cannot produce, which is exactly the defect this validation exists to catch.
VALID_DIRECTIONS = frozenset({"left", "right"})
VALID_VARIANTS = frozenset({"a", "b"})


@dataclass(frozen=True)
class VoteEvent:
    id: str
    type: str
    pairId: str
    option: str
    direction: str
    variant: str
    timestamp: str

    def __post_init__(self) -> None:
        if self.type != VOTE:
            raise ValueError(f"VoteEvent.type must be {VOTE!r}, got {self.type!r}")
        if self.direction not in VALID_DIRECTIONS:
            raise ValueError(
                f"VoteEvent.direction must be one of {sorted(VALID_DIRECTIONS)}, "
                f"got {self.direction!r}"
            )
        if self.variant not in VALID_VARIANTS:
            raise ValueError(
                f"VoteEvent.variant must be one of {sorted(VALID_VARIANTS)}, got {self.variant!r}"
            )


@dataclass(frozen=True)
class VariantSeenEvent:
    id: str
    type: str
    variant: str
    timestamp: str

    def __post_init__(self) -> None:
        if self.type != VARIANT_SEEN:
            raise ValueError(f"VariantSeenEvent.type must be {VARIANT_SEEN!r}, got {self.type!r}")
        if self.variant not in VALID_VARIANTS:
            raise ValueError(
                f"VariantSeenEvent.variant must be one of {sorted(VALID_VARIANTS)}, "
                f"got {self.variant!r}"
            )


PollEvent = Union[VoteEvent, VariantSeenEvent]


def poll_event_from_dict(data: dict[str, Any]) -> PollEvent:
    """Build the concrete PollEvent shape matching a raw record's "type"."""
    event_type = data.get("type")
    if event_type == VOTE:
        return VoteEvent(**data)
    if event_type == VARIANT_SEEN:
        return VariantSeenEvent(**data)
    raise ValueError(f"unknown PollEvent type: {event_type!r}")
