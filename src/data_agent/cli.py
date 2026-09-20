"""Command-line entry point: ask a plain-language question about the fixture.

Prints the query the data source ran (or would have run) before the answer,
so a person reading the output can tell whether to trust it. Exits 0 when
the question was answered and 1 when it wasn't - a caller scripting this
can tell the two apart without parsing the text.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from data_agent.poll_datasource import PollEventDataSource, load_events
from data_agent.poll_qa import answer_question

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_FIXTURE_PATH = REPO_ROOT / "fixtures" / "poll_events.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="data-agent",
        description="Ask a plain-language question about the committed PollEvent fixture.",
    )
    parser.add_argument("question", help="a plain-language question about the fixture")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE_PATH,
        help="path to a PollEvent fixture file (default: the committed fixture)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(sys.argv[1:] if argv is None else argv)

    raw_events = json.loads(args.fixture.read_text())
    data_source = PollEventDataSource(load_events(raw_events))
    answer = answer_question(args.question, data_source)

    print(f"query: {answer.query}")
    print(answer.text)
    return 0 if answer.answerable else 1


if __name__ == "__main__":
    sys.exit(main())
