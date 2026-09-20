"""Ground truth computed from a list of PollEvents.

Filters to type "vote" before counting anything. A fixture or script that
counts raw event length instead is wrong in a way that looks right - see
analytics-practice's ADR 0002 for why this filter is the whole point.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from data_agent.poll_events import PollEvent, VoteEvent


def compute_ground_truth(events: list[PollEvent]) -> dict[str, Any]:
    votes = [event for event in events if isinstance(event, VoteEvent)]

    votes_by_pair_option: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    votes_by_variant: dict[str, int] = defaultdict(int)

    for vote in votes:
        votes_by_pair_option[vote.pairId][vote.option] += 1
        votes_by_variant[vote.variant] += 1

    return {
        "total_votes": len(votes),
        "votes_by_pair_option": {
            pair_id: dict(sorted(options.items()))
            for pair_id, options in sorted(votes_by_pair_option.items())
        },
        "votes_by_variant": dict(sorted(votes_by_variant.items())),
    }
