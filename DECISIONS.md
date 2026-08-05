# Decisions

A running log of non-obvious architecture/design decisions for
job-scout — what was decided, why, and what was considered and
rejected. Newest first. This complements git history: commits capture
*what* changed, this captures *why*, including cases where we talked
something through and deliberately didn't change code.

---

## 2026-08-05 — JD deduplication: open, not yet decided

**Discussion:** Wanted a way to avoid processing/storing the same job
posting twice. Two exact-match approaches were considered and both
rejected: matching on `url` fails because the same job can be posted
at multiple different URLs (e.g. a LinkedIn mirror vs. the company's
own careers page); matching on a hash of the JD text fails for the
same reason, since reposts are rarely byte-identical even when
they're the same underlying job.

**Where it's left:** No automated dedup has been built. Leaning
toward *not* building true entity-resolution automatically for now —
this is a low-volume, manually-curated pipeline (you're the one
entering JDs, not a scraper), so the risk of true accidental
duplicates is naturally low. Options on the table if it becomes a
real annoyance:
- Soft-flag possible duplicates in `list_results.py` by matching
  `company` + `title` (heuristic, not a hard block — avoids silently
  merging two genuinely different roles that share a title).
- Real semantic dedup via Bedrock embeddings (bigger lift, actually
  handles reworded reposts, fits the project's embedded-AI learning
  goal — but overkill for current volume).

**Status:** Open. Revisit if duplicates actually start happening.

## 2026-08-05 — DynamoDB key schema: kept as job_id-only partition key

**Decision:** Did not switch to `company` (PK) + `job_id` (SK).

**Why:** The concern that prompted this (two companies reusing the
same `job_id`) turned out to really be about JD *content*
deduplication, not key collisions — see the entry above, which is the
actual fix for that concern. A composite key would also have forced
`company` to become a required field (DynamoDB partition keys can't
be empty) and required threading `company` through every
`repository.py` method (`mark_processing`, `mark_completed`,
`mark_failed` currently address items by `job_id` alone), for a
problem it wouldn't have fully solved anyway.

**Status:** Decided (no change made — table schema unchanged).

## 2026-08-05 — Resending the same job_id: no protection yet, but a plan

**Discussion:** Resending an SQS message with the same `job_id` today
fully overwrites the prior record (unconditional `PutItem` in
`create_received_record`) — including wiping a prior `COMPLETED`
result and resetting `created_at` — with no idempotency protection
against SQS's own at-least-once redelivery either.

**Recommendation (not yet implemented):** Add a conditional
`PutItem` (`attribute_not_exists(job_id)`) so a duplicate `job_id` is
rejected as a poison pill (logged, dropped, not retried) instead of
silently clobbering a result. Intentional re-scoring (e.g. after
updating the resume or the eval rules) should go through omitting
`job_id` — it already auto-generates a fresh `uuid4` — which
naturally preserves the old assessment as history instead of
destroying it.

**Status:** Recommended, not yet implemented.

## 2026-08-05 — JD evaluation rules encoded into the Bedrock prompt

**Decision:** Replaced the generic 0-100 `score` with a five-tier
`Strong/Good/OK/Fair/Weak` `rating` for both `job_fit` and
`compensation_fit`. `job_fit` reasoning must separately label
`Strengths:` and `Gaps:`. Each JD is assessed independently — the
model is explicitly told never to compare or rank JDs against each
other. Culture is explicitly excluded from `job_fit` (can't be judged
from posting text/tone alone). `compensation_fit` is kept brief (a
one-line factual band note + rating, not a comp breakdown).

**Why:** These are Marc's own established JD-evaluation rules
(sourced from prior memory, `jd-eval-independent.md`), now encoded
directly in `src/job_scout/assessment/prompts.py` so Bedrock actually
follows them instead of using a generic recruiter framing.

**Status:** Done — deployed and verified against a real test JD.

## 2026-08-05 — Personal compensation baseline kept out of git entirely

**Decision:** Added `CompBaseline` as a `NoEcho` CloudFormation
parameter with an empty default. It must be passed via
`--parameter-overrides` at deploy time only — never stored in
`samconfig.toml`, `template.yaml`, or any other committed file.

**Why:** The repo is **public** (confirmed via the GitHub API). A
personal compensation figure is sensitive financial data that
shouldn't be inferable from a public repo, unlike `ResumeObjectKey`
(e.g. `resume.docx`), which is fine to persist in `samconfig.toml`.
Caught and fixed a real near-miss here: a similar-looking placeholder
number was initially committed into test fixtures and README
examples before being caught and swapped for an obviously-fake one.

**Status:** Done.

## 2026-08-05 — Local dev scripts need `botocore[crt]`

**Decision:** Added `botocore[crt]` as a **dev-only** dependency.

**Why:** `scripts/send_test_jd.py` and `scripts/list_results.py`
failed locally with `MissingDependencyException` — this AWS account
uses the browser-based `aws login` credential provider, which needs
botocore's `crt` extra. The deployed Lambda is unaffected (it uses
its execution role's container credential provider, never this
path), so this only needed to go in the dev dependency group, not the
Lambda's `requirements.txt`.

**Status:** Done.

## 2026-08-04 — `.docx` resume support

**Decision:** `S3ResumeStore` parses `.docx` (paragraphs + table
cells, via `python-docx`) when the resume object key ends in
`.docx`, alongside the original plain-text path.

**Why:** The real resume is a Word document, not plain text — a raw
UTF-8 decode of a `.docx` object (a ZIP archive under the hood) would
either throw or hand Bedrock a garbage prompt.

**Status:** Done.

## 2026-08-04 — Multi-tenant support: deferred

**Discussion:** job-scout should eventually support multiple users,
not just Marc. Two directions were discussed: a shared
table/queue/bucket tagged by `user_id` vs. fully isolated per-tenant
stacks. Leaning toward the shared-table approach when the time comes
— smaller lift, keeps cost down (isolated stacks would multiply AWS
resource cost per user, cutting against the cost-minimization
principle below).

**Status:** Deferred — no code changes made. No concrete second user
or auth mechanism exists yet to design against. (Also saved to
assistant memory so future sessions don't introduce single-tenant
assumptions that would be painful to unwind later.)

## 2026-08-04 — Initial scaffold: cost-minimization defaults

**Decision:** DynamoDB `PAY_PER_REQUEST` (not literally free like
25/25-provisioned, but simpler and sub-cent/month at this volume);
Claude Haiku as the default `BedrockModelId` (cheapest current tier —
Bedrock has no free tier at all, unlike Lambda/SQS/S3 which are
effectively free at this volume); explicit 14-day CloudWatch log
retention (SAM's default is unbounded, which quietly accrues storage
cost over years).

**Why:** This is an out-of-pocket home project — free tier /
lowest cost is prioritized over efficiency throughout. A
"productize it later" pass can revisit these trade-offs.

**Status:** Done.

## 2026-08-04 — `sam build` self-generates `requirements.txt`

**Decision:** `src/requirements.txt` is gitignored, not committed.
`template.yaml` sets `CodeUri: .` and `Metadata: BuildMethod:
makefile` on `JobScoutFunction`, so `sam build` itself runs a
`build-JobScoutFunction` Makefile target that installs `uv`, exports
`requirements.txt` from `uv.lock`, and installs it — all inside the
ephemeral build container.

**Why:** Avoids a generated file needing to stay in sync with
`uv.lock` in git. Required `CodeUri: .` (not `src/`) specifically
because SAM's container build only mounts the `CodeUri` directory —
`pyproject.toml`/`uv.lock` at the repo root wouldn't otherwise be
visible inside the container for `uv export` to work.

**Status:** Done, verified with a clean `sam build` (no
pre-existing `requirements.txt`) producing a correct artifact.

## 2026-08-04 — Event source: SQS (not SNS or EventBridge)

**Decision:** SQS standard queue + DLQ, `ReportBatchItemFailures`
enabled, `BatchSize: 5`.

**Why:** Simplest option with built-in DLQ/retry, trivial to
manually send messages to for testing. EventBridge would be the
better long-term fit for multi-producer/multi-consumer routing with
`job-hunter`, but that integration doesn't exist yet — SQS can be
fronted by EventBridge/SNS later without changing how the Lambda
parses its payload.

**Status:** Done.

## 2026-08-04 — Results viewing: CLI script (not API Gateway)

**Decision:** `scripts/list_results.py` queries DynamoDB directly via
boto3. No API Gateway, no HTTP API, no UI.

**Why:** Solo use, no need for the extra infrastructure a read API
would add. Revisit if `job-hunter` needs to consume results over
HTTP.

**Status:** Done.
