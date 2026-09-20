import json
from pathlib import Path

from data_agent.poll_events import VariantSeenEvent, VoteEvent, poll_event_from_dict

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "poll_events.json"


def _load_fixture() -> list:
    raw_events = json.loads(FIXTURE_PATH.read_text())
    return [poll_event_from_dict(record) for record in raw_events]


def test_every_record_matches_a_poll_event_shape():
    events = _load_fixture()
    assert events
    for event in events:
        assert isinstance(event, (VoteEvent, VariantSeenEvent))


def test_fixture_exercises_multiple_pairs_options_variants_and_both_types():
    events = _load_fixture()
    votes = [event for event in events if isinstance(event, VoteEvent)]
    variant_seens = [event for event in events if isinstance(event, VariantSeenEvent)]

    assert votes, "fixture has no vote events"
    assert variant_seens, "fixture has no variant_seen events"
    assert len({vote.pairId for vote in votes}) >= 2
    assert len({vote.option for vote in votes}) >= 2
    assert len({event.variant for event in events}) >= 2
