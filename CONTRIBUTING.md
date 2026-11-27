# Contributing

Thanks for helping. Rule-based email triage CLI (mock agent, no LLM call). This is a small, personal project, so keep changes small and easy to review.

## Before you send a change

- Run the tests from any folder: `pytest -q` (tests must not depend on the current working directory)
- Keep the offline path working: triage must run on a local mailbox file, no API key and no download.
- If you add a triage rule, ship a sample email that exercises it.

## Reporting a problem

Open an issue and include:

- The exact command you ran
- The input file, if it is about one
- What happened, and what you expected instead

Do not include API keys, private documents, or personal details.
