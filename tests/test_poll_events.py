import pytest

from data_agent.poll_events import VariantSeenEvent, VoteEvent


def _vote_kwargs(**overrides):
    kwargs = dict(
        id="evt-x",
        type="vote",
        pairId="pair-1",
        option="Coffee",
        direction="left",
        variant="a",
        timestamp="2026-01-01T00:00:00Z",
    )
    kwargs.update(overrides)
    return kwargs


def test_vote_event_rejects_a_direction_outside_left_or_right():
    with pytest.raises(ValueError):
        VoteEvent(**_vote_kwargs(direction="up"))


def test_vote_event_rejects_a_variant_outside_a_or_b():
    with pytest.raises(ValueError):
        VoteEvent(**_vote_kwargs(variant="treatment"))


def test_variant_seen_event_rejects_a_variant_outside_a_or_b():
    with pytest.raises(ValueError):
        VariantSeenEvent(
            id="evt-x",
            type="variant_seen",
            variant="control",
            timestamp="2026-01-01T00:00:00Z",
        )
