# emailpilot

A tiny email-triage agent: it reads a JSONL file of emails, sorts each one
into **urgent / important / fyi / spam**, writes the triaged emails back out
in priority order, and drafts a short reply for urgent mail.

**Honest note:** this is a *deterministic rule-based mock* — keyword rules,
no LLM call, no API keys needed. It does not understand email the way a
language model would; it matches the keywords listed in
`src/emailpilot/rules.py`.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
emailpilot triage examples/emails.jsonl --out triaged.jsonl
```

Input is one JSON object per line:

```json
{"id": "1", "from": "manager@company.com", "subject": "Meeting tomorrow", "body": "..."}
```

Output is the same emails, sorted urgent first, then important, then fyi,
then spam last, with three extra fields per email:

- `category`: `urgent` | `important` | `fyi` | `spam`
- `draft_reply`: a short templated reply (2 sentences) for urgent emails
  only, `null` otherwise
- `triage_note`: `"mock rule-based triage, no LLM call"`

## Example output

```
$ emailpilot triage examples/emails.jsonl --out triaged.jsonl
Triaged 8 emails: 2 urgent, 2 important, 2 fyi, 2 spam. Wrote triaged.jsonl
```

```json
{"id": "3", "from": "alerts@infra.example.com", "subject": "URGENT: production outage", "body": "The checkout service is down.", "category": "urgent", "draft_reply": "Thanks for flagging this — I'm looking into the outage now and will update you as soon as I have more information. Please share any error details or affected users in the meantime.", "triage_note": "mock rule-based triage, no LLM call"}
```

## How it classifies

- **spam** — subject/body contains "win money", "free prize",
  "claim now", "lottery", "crypto giveaway", "act now!!!" — or the sender
  looks like a bulk-promo address.
- **urgent** — contains "urgent", "asap", "outage", "down", "production
  issue", "security breach", "deadline today", "escalation", or the
  subject starts with "URGENT".
- **important** — from a sender containing "manager", "team@", or "hr@",
  or the subject contains "meeting", "review", "action required", or
  "invoice".
- **fyi** — everything else (newsletters, announcements, FYI mail).

Priority order is checked spam → urgent → important → fyi in the sense
that spam wins over the rest: a "lottery" mail is spam even if it also
says "urgent".

## Tests

```bash
pytest
```
