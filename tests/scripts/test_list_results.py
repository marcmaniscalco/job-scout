import csv
import json

from scripts.list_results import (
    fetch_items,
    format_json,
    format_table,
    main,
    write_csv,
)
from tests.conftest import TABLE_NAME


def seed_items(jobs_table):
    jobs_table.put_item(
        Item={
            "job_id": "jd-1",
            "status": "COMPLETED",
            "title": "A",
            "company": "Acme",
            "created_at": "2026-01-01",
            "job_fit": {"score": 80, "reasoning": "x", "model_id": "m"},
            "compensation_fit": {
                "score": 50,
                "reasoning": "y",
                "model_id": "m",
            },
        }
    )
    jobs_table.put_item(
        Item={
            "job_id": "jd-2",
            "status": "COMPLETED",
            "title": "B",
            "company": "Beta",
            "created_at": "2026-02-01",
        }
    )
    jobs_table.put_item(
        Item={
            "job_id": "jd-3",
            "status": "FAILED",
            "title": "C",
            "company": "Gamma",
            "created_at": "2026-01-15",
        }
    )


def test_fetch_items_by_status_orders_newest_first(jobs_table):
    seed_items(jobs_table)

    items = fetch_items(jobs_table, status="COMPLETED", limit=None)

    assert [i["job_id"] for i in items] == ["jd-2", "jd-1"]


def test_fetch_items_without_status_scans_and_sorts(jobs_table):
    seed_items(jobs_table)

    items = fetch_items(jobs_table, status=None, limit=None)

    assert [i["job_id"] for i in items] == ["jd-2", "jd-3", "jd-1"]


def test_format_table_handles_empty_results():
    assert format_table([]) == "No results."


def test_format_table_includes_fit_scores():
    items = [
        {
            "job_id": "jd-1",
            "status": "COMPLETED",
            "title": "A",
            "company": "Acme",
            "job_fit": {"score": 80},
            "compensation_fit": {"score": 50},
            "created_at": "t0",
        }
    ]

    output = format_table(items)

    assert "80" in output
    assert "50" in output


def test_format_json_round_trips():
    items = [{"job_id": "jd-1", "status": "COMPLETED"}]
    assert json.loads(format_json(items)) == items


def test_write_csv_writes_expected_rows(tmp_path):
    items = [
        {
            "job_id": "jd-1",
            "status": "COMPLETED",
            "title": "A",
            "company": "Acme",
            "job_fit": {"score": 80},
            "compensation_fit": {"score": 50},
            "created_at": "t0",
        }
    ]
    path = tmp_path / "out.csv"

    write_csv(items, str(path))

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["job_id"] == "jd-1"
    assert rows[0]["job_fit"] == "80"


def test_main_prints_table_output(jobs_table, capsys):
    seed_items(jobs_table)

    exit_code = main(["--table-name", TABLE_NAME, "--status", "COMPLETED"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "jd-2" in captured.out


def test_main_requires_table_name(monkeypatch):
    monkeypatch.delenv("JOB_SCOUT_TABLE_NAME", raising=False)

    exit_code = main(["--format", "table"])

    assert exit_code == 1


def test_main_csv_requires_export_path(jobs_table):
    exit_code = main(["--table-name", TABLE_NAME, "--format", "csv"])

    assert exit_code == 1
