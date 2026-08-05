from unittest.mock import MagicMock, patch

import pytest

from job_scout.clients.bedrock_client import (
    BedrockAssessmentError,
    BedrockClient,
)
from job_scout.models import JDEvent


def make_client_with_mock_runtime() -> tuple[BedrockClient, MagicMock]:
    with patch("job_scout.clients.bedrock_client.boto3.client") as boto_client:
        mock_runtime = MagicMock()
        boto_client.return_value = mock_runtime
        client = BedrockClient("test-model", "us-east-1")
    return client, mock_runtime


def canned_response(
    job_fit: dict | None = None,
    compensation_fit: dict | None = None,
    stop_reason: str = "tool_use",
) -> dict:
    return {
        "stopReason": stop_reason,
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "name": "record_fit_assessment",
                            "input": {
                                "job_fit": job_fit
                                or {"score": 80, "reasoning": "Good"},
                                "compensation_fit": compensation_fit
                                or {"score": 60, "reasoning": "Meh"},
                            },
                        }
                    }
                ]
            }
        },
    }


def test_assess_fit_parses_tool_use_input():
    client, mock_runtime = make_client_with_mock_runtime()
    mock_runtime.converse.return_value = canned_response()
    jd_event = JDEvent(job_id="jd-1", title="Engineer", jd_text="text")

    result = client.assess_fit("resume text", jd_event)

    assert result["job_fit"]["score"] == 80
    assert result["compensation_fit"]["score"] == 60
    mock_runtime.converse.assert_called_once()


def test_assess_fit_raises_when_stop_reason_is_not_tool_use():
    client, mock_runtime = make_client_with_mock_runtime()
    mock_runtime.converse.return_value = canned_response(
        stop_reason="end_turn"
    )
    jd_event = JDEvent(job_id="jd-1", title="Engineer", jd_text="text")

    with pytest.raises(BedrockAssessmentError):
        client.assess_fit("resume text", jd_event)


def test_assess_fit_raises_when_tool_use_block_missing():
    client, mock_runtime = make_client_with_mock_runtime()
    mock_runtime.converse.return_value = {
        "stopReason": "tool_use",
        "output": {"message": {"content": [{"text": "no tool here"}]}},
    }
    jd_event = JDEvent(job_id="jd-1", title="Engineer", jd_text="text")

    with pytest.raises(BedrockAssessmentError):
        client.assess_fit("resume text", jd_event)
