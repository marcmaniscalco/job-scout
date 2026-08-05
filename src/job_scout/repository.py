"""Domain-level DynamoDB status transitions for a JD's lifecycle."""

from datetime import UTC, datetime

from job_scout.clients.dynamodb_client import DynamoDBClient
from job_scout.models import FitAssessment, JDEvent, JobRecord, JobStatus


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class Repository:
    def __init__(self, dynamodb_client: DynamoDBClient):
        self._client = dynamodb_client

    def create_received_record(self, jd_event: JDEvent) -> JobRecord:
        now = _now_iso()
        record = JobRecord(
            job_id=jd_event.job_id,
            title=jd_event.title,
            jd_text=jd_event.jd_text,
            status=JobStatus.RECEIVED,
            created_at=now,
            updated_at=now,
            company=jd_event.company,
            location=jd_event.location,
            salary=jd_event.salary,
            source=jd_event.source,
            url=jd_event.url,
            in_office_days_per_week=jd_event.in_office_days_per_week,
        )
        self._client.put_item(record.to_item())
        return record

    def mark_processing(self, job_id: str) -> None:
        self._client.update_item(
            job_id,
            {"status": JobStatus.PROCESSING, "updated_at": _now_iso()},
        )

    def mark_completed(
        self,
        job_id: str,
        job_fit: FitAssessment,
        compensation_fit: FitAssessment,
    ) -> None:
        self._client.update_item(
            job_id,
            {
                "status": JobStatus.COMPLETED,
                "updated_at": _now_iso(),
                "job_fit": job_fit.to_item(),
                "compensation_fit": compensation_fit.to_item(),
            },
        )

    def mark_failed(self, job_id: str, error_message: str) -> None:
        self._client.update_item(
            job_id,
            {
                "status": JobStatus.FAILED,
                "updated_at": _now_iso(),
                "error_message": error_message,
            },
        )
