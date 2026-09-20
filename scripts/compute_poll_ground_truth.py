#!/usr/bin/env python3
"""Regenerate the committed ground truth from the committed poll-event fixture.

Usage: uv run python scripts/compute_poll_ground_truth.py [fixture] [out]

With no arguments, reads fixtures/poll_events.json and overwrites
fixtures/ground_truth.json. Both paths are optional so the test suite can
point this at a scratch file instead of the committed one when re-running it
to diff its output.

Filters to type "vote" before counting anything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from data_agent.ground_truth import compute_ground_truth
from data_agent.poll_events import poll_event_from_dict

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURE_PATH = REPO_ROOT / "fixtures" / "poll_events.json"
DEFAULT_GROUND_TRUTH_PATH = REPO_ROOT / "fixtures" / "ground_truth.json"


def main(argv: list[str]) -> None:
    fixture_path = Path(argv[0]) if len(argv) > 0 else DEFAULT_FIXTURE_PATH
    out_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_GROUND_TRUTH_PATH

    raw_events = json.loads(fixture_path.read_text())
    events = [poll_event_from_dict(record) for record in raw_events]
    ground_truth = compute_ground_truth(events)
    out_path.write_text(json.dumps(ground_truth, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
