# job-scout

An AWS serverless pipeline that scores job descriptions (JDs) for fit
against your resume using AWS Bedrock. Drop a JD onto an SQS queue, a
Lambda runs it through Bedrock, and the scored result lands in
DynamoDB. Built to eventually integrate with a sibling project,
`job-hunter`, which will publish JD events automatically.

## How it works

1. A JSON message describing a job (title, JD text, optionally
   company/location/salary/url) is sent to the `JdQueue` SQS queue.
2. The `job-scout` Lambda is triggered, fetches your resume from S3,
   and calls Bedrock (Claude, via the Converse API) to score the JD
   on two dimensions: **job fit** and **compensation fit**.
3. The result — including the model's reasoning — is written to the
   `JobsTable` DynamoDB table.
4. You view results with `scripts/list_results.py`.

See `template.yaml` for the full infrastructure and
`src/job_scout/handler.py` for the processing flow.

## Evaluation methodology

Each JD is rated independently — never compared or ranked against
other JDs — on a five-tier scale: **Strong, Good, OK, Fair, Weak**.

- **job_fit** weights required/must-have skills heavily; "nice to
  have" gaps count for much less. The reasoning always separates
  **Strengths** and **Gaps** into explicitly labeled sections. Company
  culture is never assessed from posting text/tone alone.
- **compensation_fit** stays brief: a one-line factual note on the
  posted band (if any) plus the tier rating — not a multi-paragraph
  comp breakdown. See `CompBaseline` below for rating it against a
  personal target.

The full prompt logic lives in `src/job_scout/assessment/prompts.py`.

## What's not built yet

- **Distance/commute fit** — a third scoring dimension weighing your
  home address against the job's location and in-office days/week.
  `in_office_days_per_week` is already accepted and stored on JD
  events, but not processed. Home-address config for this is planned
  to live in SSM Parameter Store, not yet created.
- **job-hunter integration** — no automatic JD ingestion yet; JDs are
  sent manually via `scripts/send_test_jd.py`.
- Any HTTP API/UI beyond the `scripts/list_results.py` CLI.

## Setup

Requires `uv` (installed) and the AWS SAM CLI.

```bash
uv sync                 # create the venv and install dependencies
uv run pre-commit install
```

## Local checks

```bash
make lint        # ruff check
make format       # ruff format
make test         # pytest (uses moto to mock AWS)
make precommit     # full pre-commit suite, incl. secrets scan
```

## Deploying

This project targets the Lambda `python3.14` managed runtime. Local
dev may run on an older Python (SAM builds against the real runtime
via a container, see below), but the code avoids anything Python
3.14-specific.

```bash
make build         # sam build --use-container (matches the Lambda runtime)
make deploy        # sam deploy
```

`src/requirements.txt` doesn't need to exist beforehand and isn't
committed — `sam build` generates it itself from `uv.lock` as part of
the build (see `template.yaml`'s `BuildMethod: makefile` and the
`build-JobScoutFunction` target in the `Makefile`), entirely inside
the ephemeral build container.

After the first deploy, upload your resume (never commit it). Both
plain text and `.docx` are supported — the object key's extension
decides how it's read, so a `.docx` upload is parsed (paragraphs and
table cells) rather than treated as raw text:

```bash
aws s3 cp resume.txt s3://<ResumeBucketName>/resume.txt
# or, for a Word doc:
aws s3 cp resume.docx s3://<ResumeBucketName>/resume.docx
```

If you upload a `.docx`, redeploy with the matching
`ResumeObjectKey` parameter so the Lambda looks for the right key:

```bash
sam deploy --parameter-overrides ResumeObjectKey=resume.docx
```

`<ResumeBucketName>` is a stack output — see `sam list stack-outputs
--stack-name job-scout`.

### Bedrock model access

The default `BedrockModelId` parameter points at Claude Haiku's
cross-region inference profile
(`us.anthropic.claude-haiku-4-5-20251001-v1:0`), the cheapest current
tier — this project prioritizes low cost over raw model quality since
it's a self-funded home project. Before your first deploy, confirm in
the Bedrock console that you have model access enabled for Claude
Haiku in your target region. If you switch to a different model,
check whether it requires an inference-profile ID (`us.anthropic...`)
rather than a bare model ID, since Bedrock's on-demand invocation for
newer models often requires the profile form.

### Personal compensation baseline

`CompBaseline` (e.g. `"$180,000 total comp"`) is an optional
`NoEcho` parameter used to rate `compensation_fit` against your own
target instead of just judging the posted band in isolation. It
defaults to empty — omit it and compensation is rated on the posted
band alone.

**This repo is public, so the real value must never be committed.**
Don't add it to `samconfig.toml` or any other tracked file — pass it
only via `--parameter-overrides` at deploy time:

```bash
sam deploy --parameter-overrides ResumeObjectKey=resume.docx CompBaseline="$180,000 total comp"
```

Every deploy that doesn't pass it explicitly resets it back to empty
(CloudFormation doesn't remember `NoEcho` parameters across deploys
the way `samconfig.toml`-stored ones are remembered), so you'll need
to include it each time you deploy if you want it active.

## Sending a test JD

```bash
python scripts/send_test_jd.py \
  --queue-url <JdQueueUrl> \
  --title "Senior Backend Engineer" \
  --company "Acme Corp" \
  --location "Remote - US" \
  --salary "\$160k-\$190k" \
  --jd-file path/to/jd.txt
```

## Viewing results

```bash
python scripts/list_results.py --table-name <JobsTableName> --status COMPLETED
python scripts/list_results.py --table-name <JobsTableName> --format json
python scripts/list_results.py --table-name <JobsTableName> --format csv --export results.csv
```

## Cost notes

This is a solo, out-of-pocket project, so free tier is prioritized
over efficiency throughout:

- Lambda, SQS, and S3 usage at this volume falls within AWS's
  perpetual free tiers.
- DynamoDB uses on-demand (`PAY_PER_REQUEST`) billing — not literally
  free like 25/25-provisioned capacity, but sub-cent/month at this
  volume, and simpler to operate.
- The Lambda's CloudWatch log group has 14-day retention so log
  storage cost doesn't grow unbounded.
- **Bedrock has no free tier** and is the real cost center — the
  default model is Claude Haiku for that reason. Swap
  `BedrockModelId` to a larger model only if scoring quality warrants
  the extra cost.
