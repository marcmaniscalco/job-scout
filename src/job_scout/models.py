"""Domain data types for JD events and their persisted fit-assessment
records.
"""

from dataclasses import dataclass, field
from typing import Any


class JobStatus:
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class JDEvent:
    """A job description as received on the SQS queue."""

    job_id: str
    title: str
    jd_text: str
    company: str | None = None
    location: str | None = None
    salary: str | None = None
    source: str = "manual"
    url: str | None = None
    # Accepted now, not processed until distance_fit is implemented.
    in_office_days_per_week: int | None = None


@dataclass(frozen=True)
class FitAssessment:
    rating: str
    reasoning: str
    model_id: str

    def to_item(self) -> dict[str, Any]:
        return {
            "rating": self.rating,
            "reasoning": self.reasoning,
            "model_id": self.model_id,
        }

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> "FitAssessment":
        return cls(
            rating=item["rating"],
            reasoning=item["reasoning"],
            model_id=item["model_id"],
        )


@dataclass
class JobRecord:
    """The persisted DynamoDB record for a JD, across its lifecycle."""

    job_id: str
    title: str
    jd_text: str
    status: str
    created_at: str
    updated_at: str
    company: str | None = None
    location: str | None = None
    salary: str | None = None
    source: str = "manual"
    url: str | None = None
    in_office_days_per_week: int | None = None
    job_fit: FitAssessment | None = None
    compensation_fit: FitAssessment | None = None
    # Reserved for future distance/commute fit work; always None today.
    distance_fit: dict[str, Any] | None = field(default=None)

    def to_item(self) -> dict[str, Any]:
        item: dict[str, Any] = {
            "job_id": self.job_id,
            "title": self.title,
            "jd_text": self.jd_text,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
        }
        for key in (
            "company",
            "location",
            "salary",
            "url",
            "in_office_days_per_week",
        ):
            value = getattr(self, key)
            if value is not None:
                item[key] = value
        if self.job_fit is not None:
            item["job_fit"] = self.job_fit.to_item()
        if self.compensation_fit is not None:
            item["compensation_fit"] = self.compensation_fit.to_item()
        if self.distance_fit is not None:
            item["distance_fit"] = self.distance_fit
        return item

    @classmethod
    def from_item(cls, item: dict[str, Any]) -> "JobRecord":
        return cls(
            job_id=item["job_id"],
            title=item["title"],
            jd_text=item["jd_text"],
            status=item["status"],
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            company=item.get("company"),
            location=item.get("location"),
            salary=item.get("salary"),
            source=item.get("source", "manual"),
            url=item.get("url"),
            in_office_days_per_week=item.get("in_office_days_per_week"),
            job_fit=(
                FitAssessment.from_item(item["job_fit"])
                if "job_fit" in item
                else None
            ),
            compensation_fit=(
                FitAssessment.from_item(item["compensation_fit"])
                if "compensation_fit" in item
                else None
            ),
            distance_fit=item.get("distance_fit"),
        )
