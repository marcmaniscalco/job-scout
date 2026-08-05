"""Orchestrates a Bedrock call into job_fit / compensation_fit results."""

from job_scout.clients.bedrock_client import BedrockClient
from job_scout.models import FitAssessment, JDEvent


class FitAssessor:
    def __init__(self, bedrock_client: BedrockClient, model_id: str):
        self._bedrock_client = bedrock_client
        self._model_id = model_id

    def assess(
        self, resume_text: str, jd_event: JDEvent
    ) -> dict[str, FitAssessment]:
        result = self._bedrock_client.assess_fit(resume_text, jd_event)
        return {
            "job_fit": self._to_fit_assessment(result["job_fit"]),
            "compensation_fit": self._to_fit_assessment(
                result["compensation_fit"]
            ),
        }

    def _to_fit_assessment(self, raw: dict) -> FitAssessment:
        return FitAssessment(
            score=int(raw["score"]),
            reasoning=raw["reasoning"],
            model_id=self._model_id,
        )
