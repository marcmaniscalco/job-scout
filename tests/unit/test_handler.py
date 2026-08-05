import json
from unittest.mock import MagicMock, patch

import pytest

from job_scout import handler
from job_scout.clients.bedrock_client import BedrockAssessmentError
from job_scout.models import FitAssessment


def sqs_record(body: dict, message_id: str = "msg-1") -> dict:
    return {"messageId": message_id, "body": json.dumps(body)}


@pytest.fixture
def mock_repository():
    with patch.object(handler, "get_repository") as get_repo:
        repo = MagicMock()
        get_repo.return_value = repo
        yield repo


@pytest.fixture
def mock_resume_store():
    with patch.object(handler, "get_resume_store") as get_store:
        store = MagicMock()
        store.get_resume_text.return_value = "resume text"
        get_store.return_value = store
        yield store


@pytest.fixture
def mock_fit_assessor():
    with patch.object(handler, "get_fit_assessor") as get_assessor:
        assessor = MagicMock()
        assessor.assess.return_value = {
            "job_fit": FitAssessment(
                rating="Good", reasoning="Good", model_id="m1"
            ),
            "compensation_fit": FitAssessment(
                rating="OK", reasoning="Meh", model_id="m1"
            ),
        }
        get_assessor.return_value = assessor
        yield assessor


def test_happy_path_marks_completed_and_reports_no_failures(
    mock_repository, mock_resume_store, mock_fit_assessor
):
    event = {
        "Records": [sqs_record({"title": "Engineer", "jd_text": "Do stuff"})]
    }

    result = handler.lambda_handler(event, None)

    assert result == {"batchItemFailures": []}
    mock_repository.create_received_record.assert_called_once()
    mock_repository.mark_processing.assert_called_once()
    mock_repository.mark_completed.assert_called_once()
    mock_repository.mark_failed.assert_not_called()


def test_malformed_json_is_dropped_without_batch_failure(
    mock_repository, mock_resume_store, mock_fit_assessor
):
    event = {"Records": [{"messageId": "msg-1", "body": "not json"}]}

    result = handler.lambda_handler(event, None)

    assert result == {"batchItemFailures": []}
    mock_repository.create_received_record.assert_not_called()


def test_missing_required_field_is_dropped_without_batch_failure(
    mock_repository, mock_resume_store, mock_fit_assessor
):
    event = {"Records": [sqs_record({"title": "Engineer"})]}

    result = handler.lambda_handler(event, None)

    assert result == {"batchItemFailures": []}
    mock_repository.create_received_record.assert_not_called()


def test_bedrock_failure_reports_batch_item_failure_and_marks_failed(
    mock_repository, mock_resume_store, mock_fit_assessor
):
    mock_fit_assessor.assess.side_effect = BedrockAssessmentError("boom")
    event = {
        "Records": [
            sqs_record(
                {"title": "Engineer", "jd_text": "Do stuff"},
                message_id="msg-2",
            )
        ]
    }

    result = handler.lambda_handler(event, None)

    assert result == {"batchItemFailures": [{"itemIdentifier": "msg-2"}]}
    mock_repository.mark_failed.assert_called_once()
    mock_repository.mark_completed.assert_not_called()


def test_error_writing_failed_record_does_not_crash_batch(
    mock_repository, mock_resume_store, mock_fit_assessor
):
    mock_fit_assessor.assess.side_effect = BedrockAssessmentError("boom")
    mock_repository.mark_failed.side_effect = Exception("dynamo down")
    event = {
        "Records": [
            sqs_record(
                {"title": "Engineer", "jd_text": "Do stuff"},
                message_id="msg-3",
            )
        ]
    }

    result = handler.lambda_handler(event, None)

    assert result == {"batchItemFailures": [{"itemIdentifier": "msg-3"}]}


def test_multiple_records_only_failing_one_is_reported(
    mock_repository, mock_resume_store, mock_fit_assessor
):
    mock_fit_assessor.assess.side_effect = [
        {
            "job_fit": FitAssessment(
                rating="Good", reasoning="ok", model_id="m"
            ),
            "compensation_fit": FitAssessment(
                rating="OK", reasoning="ok", model_id="m"
            ),
        },
        BedrockAssessmentError("boom"),
    ]
    event = {
        "Records": [
            sqs_record(
                {"title": "Engineer", "jd_text": "Do stuff"},
                message_id="msg-ok",
            ),
            sqs_record(
                {"title": "Engineer 2", "jd_text": "Do more stuff"},
                message_id="msg-bad",
            ),
        ]
    }

    result = handler.lambda_handler(event, None)

    assert result == {"batchItemFailures": [{"itemIdentifier": "msg-bad"}]}
