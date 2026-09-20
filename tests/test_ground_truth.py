import copy
import json
import subprocess
import sys
from pathlib import Path

from data_agent.ground_truth import compute_ground_truth
from data_agent.poll_events import poll_event_from_dict

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = REPO_ROOT / "fixtures" / "poll_events.json"
GROUND_TRUTH_PATH = REPO_ROOT / "fixtures" / "ground_truth.json"
SCRIPT_PATH = REPO_ROOT / "scripts" / "compute_poll_ground_truth.py"


def _load_raw_fixture() -> list:
    return json.loads(FIXTURE_PATH.read_text())


def test_adding_a_variant_seen_event_does_not_change_vote_count():
    raw_events = _load_raw_fixture()
    baseline = compute_ground_truth([poll_event_from_dict(r) for r in raw_events])

    with_extra = copy.deepcopy(raw_events)
    with_extra.append(
        {
            "id": "evt-extra",
            "type": "variant_seen",
            "variant": "control",
            "timestamp": "2026-01-01T00:00:24Z",
        }
    )
    changed = compute_ground_truth([poll_event_from_dict(r) for r in with_extra])

    assert changed["total_votes"] == baseline["total_votes"]
    assert changed["votes_by_pair_option"] == baseline["votes_by_pair_option"]
    assert changed["votes_by_variant"] == baseline["votes_by_variant"]


def test_ground_truth_script_output_matches_committed_file_exactly(tmp_path):
    out_path = tmp_path / "ground_truth.json"

    subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(FIXTURE_PATH), str(out_path)],
        check=True,
        cwd=REPO_ROOT,
    )

    regenerated = json.loads(out_path.read_text())
    committed = json.loads(GROUND_TRUTH_PATH.read_text())

    assert regenerated == committed
