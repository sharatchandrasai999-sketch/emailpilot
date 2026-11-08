"""Tests for emailpilot."""

import json
from pathlib import Path

import pytest

from emailpilot.cli import main
from emailpilot.rules import TRIAGE_NOTE, classify, sort_triaged, triage

SAMPLES = str(Path(__file__).resolve().parent.parent / "examples" / "emails.jsonl")


def _email(sender, subject, body):
    return {"id": "x", "from": sender, "subject": subject, "body": body}


def test_outage_email_is_urgent():
    email = _email("alerts@infra.example.com", "Production outage",
                   "The checkout service is down.")
    assert classify(email) == "urgent"


def test_urgent_subject_prefix_is_urgent():
    email = _email("boss@company.com", "URGENT: read this",
                   "Please reply today.")
    assert classify(email) == "urgent"


def test_lottery_email_is_spam():
    email = _email("winner@lottery-prize.net", "You won!",
                   "Claim now to receive your lottery prize.")
    assert classify(email) == "spam"


def test_meeting_email_from_manager_is_important():
    email = _email("manager@company.com", "Meeting tomorrow",
                   "Let's meet to review the plan.")
    assert classify(email) == "important"


def test_newsletter_is_fyi():
    email = _email("newsletter@techweekly.com", "This week in AI",
                   "Top stories this week.")
    assert classify(email) == "fyi"


def test_download_does_not_trigger_down_rule():
    email = _email("newsletter@techweekly.com", "Weekly digest",
                   "Download the new report from the link below.")
    assert classify(email) == "fyi"


def test_output_sorted_urgent_first():
    emails = [
        _email("a@b.com", "Newsletter", "weekly news"),
        _email("a@b.com", "Outage", "service is down"),
        _email("a@b.com", "You won the lottery", "claim now"),
        _email("manager@company.com", "Meeting", "tomorrow"),
    ]
    result = [t["category"] for t in sort_triaged([triage(e) for e in emails])]
    assert result == ["urgent", "important", "fyi", "spam"]


def test_draft_reply_only_for_urgent():
    urgent = triage(_email("a@b.com", "Outage", "service is down"))
    fyi = triage(_email("a@b.com", "Newsletter", "weekly news"))
    assert urgent["draft_reply"] is not None
    assert len(urgent["draft_reply"].split(". ")) >= 2
    assert fyi["draft_reply"] is None
    assert urgent["triage_note"] == TRIAGE_NOTE
    assert fyi["triage_note"] == TRIAGE_NOTE


def test_cli_end_to_end_on_sample_file(tmp_path, capsys):
    out = tmp_path / "triaged.jsonl"
    rc = main(["triage", SAMPLES, "--out", str(out)])
    assert rc == 0
    lines = [json.loads(l) for l in out.read_text().splitlines()]
    assert len(lines) == 8
    assert {e["category"] for e in lines} == {"urgent", "important", "fyi", "spam"}
    categories = [e["category"] for e in lines]
    assert categories == sorted(
        categories, key=lambda c: {"urgent": 0, "important": 1, "fyi": 2, "spam": 3}[c]
    )
    assert sum(1 for e in lines if e["category"] == "urgent") >= 2
    assert sum(1 for e in lines if e["category"] == "spam") >= 1
    assert "8 emails" in capsys.readouterr().out


def test_missing_input_file_errors_cleanly(capsys):
    rc = main(["triage", "no-such-file.jsonl", "--out", "out.jsonl"])
    assert rc == 1
    assert "not found" in capsys.readouterr().err
