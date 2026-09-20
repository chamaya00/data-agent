import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI_MODULE = "data_agent.cli"


def _run_cli(question: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", CLI_MODULE, question],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_answerable_question_prints_the_ground_truth_answer_and_the_query():
    # fixtures/ground_truth.json's votes_by_variant.a is 10.
    result = _run_cli("how many votes did variant a get?")

    assert "10" in result.stdout
    assert "query:" in result.stdout
    assert "variant" in result.stdout
    assert result.returncode == 0


def test_which_option_won_question_matches_hand_verified_fixture_counts():
    # Hand-counted from fixtures/poll_events.json: variant b votes are
    # Tea x5 (evt-0003/0008/0013/0018/0023) and Dogs x4 (evt-0004/0009/
    # 0014/0019) - a clean, non-tied winner.
    result = _run_cli("which option won among variant b?")

    assert "Tea" in result.stdout
    assert "query:" in result.stdout
    assert result.returncode == 0


def test_unanswerable_variant_outside_domain_states_non_answerability():
    result = _run_cli("how many votes did variant treatment get?")

    assert "can't answer" in result.stdout
    assert result.returncode == 1
    # No digit anywhere in the output: this must not produce a number.
    assert not any(character.isdigit() for character in result.stdout)


def test_unanswerable_option_outside_domain_states_non_answerability():
    result = _run_cli("how many votes did option Pizza get?")

    assert "can't answer" in result.stdout
    assert result.returncode == 1
    assert not any(character.isdigit() for character in result.stdout)
