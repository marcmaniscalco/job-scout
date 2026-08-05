# job-scout

AWS serverless pipeline: SQS-triggered Lambda that scores job
descriptions for fit against a resume using AWS Bedrock, persisting
results in DynamoDB. See `README.md` for architecture/usage and
`DECISIONS.md` for the history of why things are the way they are.

## Working conventions for this project

- **This repo is public.** Never commit secrets, credentials, or
  personal data (resume content, home address, compensation figures,
  job-search specifics) — not even as "realistic-looking" example
  data in tests, docs, or code comments. `CompBaseline` is the
  pattern to follow for anything sensitive-but-config-like: a
  `NoEcho` CloudFormation parameter with no default, passed only via
  `--parameter-overrides` at deploy time, never persisted in
  `samconfig.toml` or any tracked file.
- **Project-specific context stays in this repo, not in assistant
  memory.** This project is worked on from multiple computers, so
  anything worth remembering — architecture decisions, open
  questions, conventions — belongs in `DECISIONS.md`, `README.md`, or
  here, not in a machine-local memory file that won't follow to
  another computer. Log significant decisions and deferred/open
  questions to `DECISIONS.md` (newest entry at top) as they come up,
  not just when explicitly asked to.
- **Cost-minimization is a standing principle**, not a one-time
  choice — this is a self-funded home project. Prefer AWS free-tier
  services and cheap defaults over efficiency/performance. See
  `DECISIONS.md` and the README's "Cost notes" section for the
  reasoning already applied (on-demand DynamoDB, Claude Haiku
  default, capped log retention).
- **Quality bar:** all code PEP8-formatted (ruff), linted (ruff), and
  covered by unit tests (pytest + moto for AWS mocking). Pre-commit
  hooks enforce this plus secrets scanning (detect-secrets) — run
  `make precommit` before assuming something is ready.

## Dev commands

```bash
uv sync                 # install deps
make lint                # ruff check
make format               # ruff format
make test                 # pytest
make precommit             # full pre-commit suite (lint, format, secrets scan)
make build                 # sam build --use-container (Lambda targets python3.14)
make deploy                 # sam deploy
```

`sam build` requires Docker running (container build matches the
Lambda's `python3.14` runtime, which the local dev interpreter may
not be). `src/requirements.txt` is generated automatically as part of
`sam build` — see `DECISIONS.md`'s "sam build self-generates
requirements.txt" entry — never commit it.
