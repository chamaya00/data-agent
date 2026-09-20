"""Deterministic generator for the committed PollEvent fixture.

Index-based rather than random: the same output has to be reproducible by
inspection, not just by re-running with a fixed seed, so `docs/decisions/`
records why and the committed fixture can be checked by hand.

Value domains are drawn from what the real product can actually emit - see
docs/decisions/0002-poll-event-schema.md - not from arbitrary placeholders
that happen to be type-valid.
"""

from __future__ import annotations

from data_agent.poll_events import PollEvent, VariantSeenEvent, VoteEvent

# (pairId, left option, right option) - only pairs whose labels are verified
# against the real product's PAIRS list, per the pull request #8 review.
PAIRS = (
    ("pair-1", "Coffee", "Tea"),
    ("pair-2", "Cats", "Dogs"),
)
DIRECTIONS = ("left", "right")
VARIANTS = ("a", "b")

EVENT_COUNT = 24


def generate_fixture(event_count: int = EVENT_COUNT) -> list[PollEvent]:
    """Generate `event_count` PollEvents cycling deterministically over i.

    Every fifth event (i % 5 == 0) is a variant_seen event; the rest are
    votes. A vote's pair and direction cycle on the count of vote events seen
    so far (not on i directly), so a swipe direction doesn't lock to one pair
    - both options of both pairs appear in the fixture.
    """
    events: list[PollEvent] = []
    vote_index = 0
    for i in range(event_count):
        event_id = f"evt-{i:04d}"
        timestamp = f"2026-01-01T00:00:{i:02d}Z"
        if i % 5 == 0:
            variant = VARIANTS[0] if i % 10 == 0 else VARIANTS[1]
            events.append(
                VariantSeenEvent(
                    id=event_id,
                    type="variant_seen",
                    variant=variant,
                    timestamp=timestamp,
                )
            )
        else:
            pair_id, left, right = PAIRS[vote_index % len(PAIRS)]
            direction = DIRECTIONS[(vote_index // 2) % 2]
            option = left if direction == "left" else right
            variant = VARIANTS[0] if vote_index % 4 < 2 else VARIANTS[1]
            events.append(
                VoteEvent(
                    id=event_id,
                    type="vote",
                    pairId=pair_id,
                    option=option,
                    direction=direction,
                    variant=variant,
                    timestamp=timestamp,
                )
            )
            vote_index += 1
    return events
