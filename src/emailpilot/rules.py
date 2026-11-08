"""Keyword rules that classify one email.

This is a deterministic rule-based mock — no LLM call, no API key.
Priority: spam is checked first, then urgent, then important; anything
left over is fyi.
"""

import re

TRIAGE_NOTE = "mock rule-based triage, no LLM call"

SPAM_PHRASES = (
    "win money",
    "free prize",
    "claim now",
    "lottery",
    "crypto giveaway",
    "act now!!!",
)

# Sender patterns that look like bulk promo mail.
SPAM_SENDER_PATTERNS = (
    "promo",
    "noreply",
    "no-reply",
    "deals@",
    "offer@",
    "win@",
)

URGENT_PHRASES = (
    "urgent",
    "asap",
    "outage",
    "down",
    "production issue",
    "security breach",
    "deadline today",
    "escalation",
)

IMPORTANT_SENDER_PATTERNS = ("manager", "team@", "hr@")
IMPORTANT_SUBJECT_PHRASES = ("meeting", "review", "action required", "invoice")

CATEGORY_ORDER = {"urgent": 0, "important": 1, "fyi": 2, "spam": 3}

URGENT_REPLY = (
    "Thanks for flagging this — I'm looking into it now and will update you "
    "as soon as I have more information. "
    "Please share any error details or affected users in the meantime."
)


def _text(email: dict) -> str:
    return f"{email.get('subject', '')} {email.get('body', '')}".lower()


def _contains(text: str, phrase: str) -> bool:
    # Single words match on word boundaries, so "download" does not
    # trigger the "down" rule; multi-word phrases match as substrings.
    if " " in phrase:
        return phrase in text
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def _looks_like_bulk_promo(sender: str) -> bool:
    sender = sender.lower()
    return any(p in sender for p in SPAM_SENDER_PATTERNS)


def classify(email: dict) -> str:
    """Return 'urgent', 'important', 'fyi', or 'spam' for one email."""
    sender = str(email.get("from", ""))
    subject = str(email.get("subject", ""))
    text = _text(email)

    if any(p in text for p in SPAM_PHRASES) or _looks_like_bulk_promo(sender):
        return "spam"
    if subject.lower().startswith("urgent") or any(
        _contains(text, p) for p in URGENT_PHRASES
    ):
        return "urgent"
    if (
        any(p in sender.lower() for p in IMPORTANT_SENDER_PATTERNS)
        or any(p in subject.lower() for p in IMPORTANT_SUBJECT_PHRASES)
    ):
        return "important"
    return "fyi"


def draft_reply(email: dict, category: str) -> str | None:
    """A short templated reply for urgent mail only, else None."""
    if category != "urgent":
        return None
    return URGENT_REPLY


def triage(email: dict) -> dict:
    """Return a copy of the email with category, draft_reply, triage_note."""
    category = classify(email)
    result = dict(email)
    result["category"] = category
    result["draft_reply"] = draft_reply(email, category)
    result["triage_note"] = TRIAGE_NOTE
    return result


def sort_triaged(emails: list[dict]) -> list[dict]:
    """Urgent first, then important, then fyi, then spam last."""
    return sorted(emails, key=lambda e: CATEGORY_ORDER[e["category"]])
