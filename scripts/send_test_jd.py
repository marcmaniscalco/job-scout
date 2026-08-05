#!/usr/bin/env python
"""CLI to manually enqueue a test job description onto the job-scout
SQS queue.

Example:
    python scripts/send_test_jd.py \\
        --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/q \\
        --title "Senior Backend Engineer" --company "Acme Corp" \\
        --location "Remote - US" --salary "$160k-$190k" \\
        --jd-file jd.txt
"""

import argparse
import json
import os
import sys
import uuid
from typing import Any

import boto3


def build_message_body(args: argparse.Namespace) -> dict[str, Any]:
    jd_text = args.jd_file.read() if args.jd_file else args.jd_text
    if not jd_text or not jd_text.strip():
        raise ValueError(
            "either --jd-text or --jd-file must supply non-empty text"
        )

    body: dict[str, Any] = {
        "job_id": args.job_id or str(uuid.uuid4()),
        "title": args.title,
        "jd_text": jd_text,
        "source": args.source,
    }
    for field_name in ("company", "location", "salary", "url"):
        value = getattr(args, field_name)
        if value:
            body[field_name] = value
    return body


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Enqueue a test job description onto the job-scout SQS queue."
        )
    )
    parser.add_argument(
        "--queue-url",
        default=os.environ.get("JOB_SCOUT_QUEUE_URL"),
        help="SQS queue URL (or set JOB_SCOUT_QUEUE_URL)",
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--company")
    parser.add_argument("--location")
    parser.add_argument("--salary")
    parser.add_argument("--url")
    parser.add_argument("--job-id")
    parser.add_argument("--source", default="manual")

    jd_group = parser.add_mutually_exclusive_group(required=True)
    jd_group.add_argument("--jd-text")
    jd_group.add_argument(
        "--jd-file", type=argparse.FileType("r", encoding="utf-8")
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.queue_url:
        print(
            "error: --queue-url or JOB_SCOUT_QUEUE_URL is required",
            file=sys.stderr,
        )
        return 1

    body = build_message_body(args)
    client = boto3.client("sqs")
    response = client.send_message(
        QueueUrl=args.queue_url, MessageBody=json.dumps(body)
    )
    print(f"Sent job_id={body['job_id']} messageId={response['MessageId']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
