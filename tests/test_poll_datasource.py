import json
from pathlib import Path

import pytest

from data_agent.poll_datasource import (
    PollEventDataSource,
    QueryTimeout,
    RowCapExceeded,
    load_events,
)
from data_agent.poll_events import VARIANT_SEEN, VOTE

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "poll_events.json"


def _load_fixture_events():
    return load_events(json.loads(FIXTURE_PATH.read_text()))


def test_schema_returns_poll_event_shape_without_running_a_query():
    # No data source is even constructed with real events: schema() is a
    # staticmethod, so there is nothing here for a query to run against.
    schema = PollEventDataSource.schema()

    assert schema[VOTE] == {
        "id": "str",
        "type": "str",
        "pairId": "str",
        "option": "str",
        "direction": "str",
        "variant": "str",
        "timestamp": "str",
    }
    assert schema[VARIANT_SEEN] == {
        "id": "str",
        "type": "str",
        "variant": "str",
        "timestamp": "str",
    }


def test_query_rejects_once_it_exceeds_the_row_cap():
    events = _load_fixture_events()
    # The fixture has far more than one vote; a cap of 1 must be exceeded.
    data_source = PollEventDataSource(events, row_cap=1)

    with pytest.raises(RowCapExceeded):
        data_source.query(event_type=VOTE)


def test_query_under_the_row_cap_succeeds():
    events = _load_fixture_events()
    data_source = PollEventDataSource(events, row_cap=1000)

    votes = data_source.query(event_type=VOTE)

    assert len(votes) == 19  # matches fixtures/ground_truth.json's total_votes


def test_query_raises_once_it_runs_past_the_timeout():
    events = _load_fixture_events()
    # A fake clock: the first call sets the deadline, the second call (made
    # while scanning the very first event) reports far past it. This makes
    # the timeout deterministic instead of depending on real wall time.
    clock_calls = iter([0.0, 100.0])
    data_source = PollEventDataSource(
        events, timeout_seconds=1.0, clock=lambda: next(clock_calls)
    )

    with pytest.raises(QueryTimeout):
        data_source.query()


def test_sample_truncates_to_the_row_cap():
    events = _load_fixture_events()
    data_source = PollEventDataSource(events, row_cap=3)

    assert len(data_source.sample(1000)) == 3


def test_distinct_values_reports_the_fixtures_real_option_labels():
    events = _load_fixture_events()
    data_source = PollEventDataSource(events)

    options = data_source.distinct_values("option", event_type=VOTE)

    assert options == {"Coffee", "Tea", "Cats", "Dogs"}
