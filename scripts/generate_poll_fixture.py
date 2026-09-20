#!/usr/bin/env python3
"""Regenerate the committed poll-event fixture.

Usage: uv run python scripts/generate_poll_fixture.py

Writes fixtures/poll_events.json from data_agent.fixtures.generate_fixture().
Run this and commit the result whenever the generator changes - and
regenerate fixtures/ground_truth.json (scripts/compute_poll_ground_truth.py)
in the same commit, since it is derived from this file.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from data_agent.fixtures import generate_fixture

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "poll_events.json"


def main() -> None:
    events = [asdict(event) for event in generate_fixture()]
    FIXTURE_PATH.write_text(json.dumps(events, indent=2) + "\n")


if __name__ == "__main__":
    main()
