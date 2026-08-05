from job_scout.clients.dynamodb_client import DynamoDBClient
from job_scout.models import FitAssessment, JDEvent, JobStatus
from job_scout.repository import Repository
from tests.conftest import REGION, TABLE_NAME


def make_repository() -> Repository:
    return Repository(DynamoDBClient(TABLE_NAME, REGION))


def test_create_received_record_persists_item(jobs_table):
    repo = make_repository()
    jd_event = JDEvent(job_id="jd-1", title="Engineer", jd_text="text")

    record = repo.create_received_record(jd_event)

    assert record.status == JobStatus.RECEIVED
    item = jobs_table.get_item(Key={"job_id": "jd-1"})["Item"]
    assert item["status"] == JobStatus.RECEIVED
    assert item["title"] == "Engineer"


def test_mark_processing_updates_status(jobs_table):
    repo = make_repository()
    jd_event = JDEvent(job_id="jd-1", title="Engineer", jd_text="text")
    repo.create_received_record(jd_event)

    repo.mark_processing("jd-1")

    item = jobs_table.get_item(Key={"job_id": "jd-1"})["Item"]
    assert item["status"] == JobStatus.PROCESSING


def test_mark_completed_stores_fit_results(jobs_table):
    repo = make_repository()
    jd_event = JDEvent(job_id="jd-1", title="Engineer", jd_text="text")
    repo.create_received_record(jd_event)
    job_fit = FitAssessment(score=80, reasoning="Good", model_id="m1")
    compensation_fit = FitAssessment(score=50, reasoning="Low", model_id="m1")

    repo.mark_completed("jd-1", job_fit, compensation_fit)

    item = jobs_table.get_item(Key={"job_id": "jd-1"})["Item"]
    assert item["status"] == JobStatus.COMPLETED
    assert item["job_fit"]["score"] == 80
    assert item["compensation_fit"]["score"] == 50


def test_mark_failed_stores_error_message(jobs_table):
    repo = make_repository()
    jd_event = JDEvent(job_id="jd-1", title="Engineer", jd_text="text")
    repo.create_received_record(jd_event)

    repo.mark_failed("jd-1", "Bedrock timed out")

    item = jobs_table.get_item(Key={"job_id": "jd-1"})["Item"]
    assert item["status"] == JobStatus.FAILED
    assert item["error_message"] == "Bedrock timed out"
