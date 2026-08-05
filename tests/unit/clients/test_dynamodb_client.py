from job_scout.clients.dynamodb_client import DynamoDBClient
from tests.conftest import REGION, TABLE_NAME


def make_client() -> DynamoDBClient:
    return DynamoDBClient(TABLE_NAME, REGION)


def test_put_and_get_item(jobs_table):
    client = make_client()
    client.put_item({"job_id": "jd-1", "status": "RECEIVED"})

    item = client.get_item("jd-1")
    assert item["status"] == "RECEIVED"


def test_get_item_returns_none_when_missing(jobs_table):
    client = make_client()
    assert client.get_item("does-not-exist") is None


def test_update_item_sets_attributes(jobs_table):
    client = make_client()
    client.put_item({"job_id": "jd-1", "status": "RECEIVED"})

    client.update_item("jd-1", {"status": "PROCESSING", "updated_at": "t1"})

    item = client.get_item("jd-1")
    assert item["status"] == "PROCESSING"
    assert item["updated_at"] == "t1"


def test_query_by_status_returns_matching_items_newest_first(jobs_table):
    client = make_client()
    client.put_item(
        {"job_id": "jd-1", "status": "COMPLETED", "created_at": "2026-01-01"}
    )
    client.put_item(
        {"job_id": "jd-2", "status": "COMPLETED", "created_at": "2026-02-01"}
    )
    client.put_item(
        {"job_id": "jd-3", "status": "FAILED", "created_at": "2026-01-15"}
    )

    items = client.query_by_status("COMPLETED")

    assert [item["job_id"] for item in items] == ["jd-2", "jd-1"]


def test_scan_all_returns_every_item(jobs_table):
    client = make_client()
    client.put_item({"job_id": "jd-1", "status": "RECEIVED"})
    client.put_item({"job_id": "jd-2", "status": "COMPLETED"})

    items = client.scan_all()

    assert {item["job_id"] for item in items} == {"jd-1", "jd-2"}
