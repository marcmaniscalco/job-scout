#!/usr/bin/env python
"""CLI to list/print/export job-scout JD processing results from
DynamoDB.

Example:
    python scripts/list_results.py --table-name job-scout-JobsTable \\
        --status COMPLETED --format table
"""

import argparse
import csv
import json
import os
import sys
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

GSI_STATUS_CREATED_AT = "StatusCreatedAtIndex"
VALID_STATUSES = ("RECEIVED", "PROCESSING", "COMPLETED", "FAILED")
DISPLAY_COLUMNS = (
    "job_id",
    "status",
    "title",
    "company",
    "job_fit",
    "compensation_fit",
    "created_at",
)


def fetch_items(
    table: Any, status: str | None, limit: int | None
) -> list[dict[str, Any]]:
    """Query by status via the GSI, or scan and sort client-side."""
    if status:
        kwargs: dict[str, Any] = {
            "IndexName": GSI_STATUS_CREATED_AT,
            "KeyConditionExpression": Key("status").eq(status),
            "ScanIndexForward": False,
        }
        if limit is not None:
            kwargs["Limit"] = limit
        response = table.query(**kwargs)
        return response.get("Items", [])

    kwargs = {}
    if limit is not None:
        kwargs["Limit"] = limit
    response = table.scan(**kwargs)
    items = response.get("Items", [])
    return sorted(
        items, key=lambda item: item.get("created_at", ""), reverse=True
    )


def _fit_summary(item: dict[str, Any], key: str) -> str:
    fit = item.get(key)
    if not fit:
        return "-"
    return f"{fit.get('score')}"


def format_table(items: list[dict[str, Any]]) -> str:
    if not items:
        return "No results."
    rows = [
        [
            item.get("job_id", ""),
            item.get("status", ""),
            item.get("title", ""),
            item.get("company", ""),
            _fit_summary(item, "job_fit"),
            _fit_summary(item, "compensation_fit"),
            item.get("created_at", ""),
        ]
        for item in items
    ]
    widths = [
        max(len(str(row[i])) for row in ([DISPLAY_COLUMNS] + rows))
        for i in range(len(DISPLAY_COLUMNS))
    ]
    header = "  ".join(
        str(DISPLAY_COLUMNS[i]).ljust(widths[i])
        for i in range(len(DISPLAY_COLUMNS))
    )
    separator = "  ".join("-" * w for w in widths)
    body_lines = [
        "  ".join(str(row[i]).ljust(widths[i]) for i in range(len(row)))
        for row in rows
    ]
    return "\n".join([header, separator, *body_lines])


def format_json(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, indent=2, default=str)


def write_csv(items: list[dict[str, Any]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DISPLAY_COLUMNS)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "job_id": item.get("job_id", ""),
                    "status": item.get("status", ""),
                    "title": item.get("title", ""),
                    "company": item.get("company", ""),
                    "job_fit": _fit_summary(item, "job_fit"),
                    "compensation_fit": _fit_summary(item, "compensation_fit"),
                    "created_at": item.get("created_at", ""),
                }
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List job-scout JD processing results from DynamoDB."
    )
    parser.add_argument(
        "--table-name", default=os.environ.get("JOB_SCOUT_TABLE_NAME")
    )
    parser.add_argument("--status", choices=VALID_STATUSES)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--format", choices=("table", "json", "csv"), default="table"
    )
    parser.add_argument(
        "--export",
        help="File path to write output to instead of stdout "
        "(required for --format csv)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.table_name:
        print(
            "error: --table-name or JOB_SCOUT_TABLE_NAME is required",
            file=sys.stderr,
        )
        return 1
    if args.format == "csv" and not args.export:
        print("error: --format csv requires --export <path>", file=sys.stderr)
        return 1

    table = boto3.resource("dynamodb").Table(args.table_name)
    items = fetch_items(table, args.status, args.limit)

    if args.format == "csv":
        write_csv(items, args.export)
        print(f"Wrote {len(items)} result(s) to {args.export}")
        return 0

    output = (
        format_json(items) if args.format == "json" else format_table(items)
    )
    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote {len(items)} result(s) to {args.export}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
