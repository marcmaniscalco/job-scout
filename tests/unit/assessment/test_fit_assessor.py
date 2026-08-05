from unittest.mock import MagicMock

from job_scout.assessment.fit_assessor import FitAssessor
from job_scout.models import FitAssessment, JDEvent


def test_assess_builds_fit_assessments_with_model_id():
    bedrock_client = MagicMock()
    bedrock_client.assess_fit.return_value = {
        "job_fit": {"score": 85, "reasoning": "Strong match"},
        "compensation_fit": {"score": 40, "reasoning": "Below market"},
    }
    assessor = FitAssessor(bedrock_client, model_id="haiku-4-5")
    jd_event = JDEvent(job_id="jd-1", title="Engineer", jd_text="text")

    result = assessor.assess("resume text", jd_event)

    assert result["job_fit"] == FitAssessment(
        score=85, reasoning="Strong match", model_id="haiku-4-5"
    )
    assert result["compensation_fit"] == FitAssessment(
        score=40, reasoning="Below market", model_id="haiku-4-5"
    )
    bedrock_client.assess_fit.assert_called_once_with("resume text", jd_event)
