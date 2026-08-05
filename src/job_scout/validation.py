"""Validation of raw SQS message bodies into JDEvent domain objects."""

import uuid
from typing import Any

from job_scout.models import JDEvent


class ValidationError(Exception):
    """Raised when an SQS message body is not a usable JD event."""


def _require_nonempty_str(body: dict[str, Any], field_name: str) -> str:
    value = body.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            f"'{field_name}' is required and must be a non-empty string"
        )
    return value


def parse_jd_event(body: dict[str, Any]) -> JDEvent:
    """Parse and validate a raw SQS message body into a JDEvent.

    Required: title, jd_text. Everything else is optional; unknown
    extra fields are ignored so future producers (e.g. job-hunter) can
    add fields without breaking this consumer.
    """
    if not isinstance(body, dict):
        raise ValidationError("message body must be a JSON object")

    title = _require_nonempty_str(body, "title")
    jd_text = _require_nonempty_str(body, "jd_text")

    job_id = body.get("job_id")
    if not isinstance(job_id, str) or not job_id.strip():
        job_id = str(uuid.uuid4())

    in_office_days_per_week = body.get("in_office_days_per_week")
    if in_office_days_per_week is not None and not isinstance(
        in_office_days_per_week, int
    ):
        in_office_days_per_week = None

    return JDEvent(
        job_id=job_id,
        title=title,
        jd_text=jd_text,
        company=body.get("company"),
        location=body.get("location"),
        salary=body.get("salary"),
        source=body.get("source") or "manual",
        url=body.get("url"),
        in_office_days_per_week=in_office_days_per_week,
    )
