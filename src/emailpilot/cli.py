"""Command-line interface for emailpilot."""

import argparse
import json
import os
import sys
from collections import Counter

from emailpilot.rules import sort_triaged, triage


def _triage(args: argparse.Namespace) -> int:
    if not os.path.exists(args.input):
        print(
            f"error: input file '{args.input}' not found.",
            file=sys.stderr,
        )
        return 1

    emails = []
    with open(args.input, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                emails.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(
                    f"error: invalid JSON on line {line_no} of {args.input}: {exc}",
                    file=sys.stderr,
                )
                return 1

    triaged = sort_triaged([triage(email) for email in emails])
    with open(args.out, "w", encoding="utf-8") as f:
        for email in triaged:
            f.write(json.dumps(email) + "\n")

    counts = Counter(e["category"] for e in triaged)
    print(
        f"Triaged {len(triaged)} emails: "
        f"{counts.get('urgent', 0)} urgent, "
        f"{counts.get('important', 0)} important, "
        f"{counts.get('fyi', 0)} fyi, "
        f"{counts.get('spam', 0)} spam. "
        f"Wrote {args.out}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="emailpilot",
        description="Rule-based email triage (mock agent, no LLM call).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("triage", help="Triage a JSONL file of emails")
    p.add_argument("input", help="Input JSONL file, one email per line")
    p.add_argument("--out", required=True, help="Output JSONL file")
    p.set_defaults(func=_triage)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
