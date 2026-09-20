"""Deterministic generator for the committed PollEvent fixture.

Index-based rather than random: the same output has to be reproducible by
inspection, not just by re-running with a fixed seed, so `docs/decisions/`
records why and the committed fixture can be checked by hand.
"""

from __future__ import annotations

from data_agent.poll_events import PollEvent, VariantSeenEvent, VoteEvent

PAIRS = ("pair-1", "pair-2", "pair-3")
OPTIONS = ("A", "B")
DIRECTIONS = ("up", "down")
VARIANTS = ("control", "treatment")

EVENT_COUNT = 24


def generate_fixture(event_count: int = EVENT_COUNT) -> list[PollEvent]:
    """Generate `event_count` PollEvents cycling deterministically over i.

    Every fifth event (i % 5 == 0) is a variant_seen event; the rest are
    votes. Field values cycle through PAIRS/OPTIONS/DIRECTIONS/VARIANTS on
    moduli chosen so pairId, option and variant don't move in lockstep.
    """
    events: list[PollEvent] = []
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
            variant_group = i % 4
            events.append(
                VoteEvent(
                    id=event_id,
                    type="vote",
                    pairId=PAIRS[i % 3],
                    option=OPTIONS[i % 2],
                    direction=DIRECTIONS[(i + 1) % 2],
                    variant=VARIANTS[0] if variant_group < 2 else VARIANTS[1],
                    timestamp=timestamp,
                )
            )
    return events
