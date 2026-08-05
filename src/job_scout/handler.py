"""Lambda entrypoint: SQS-triggered JD fit assessment."""

import json
import logging
import sys
from functools import lru_cache
from typing import Any

from job_scout.assessment.fit_assessor import FitAssessor
from job_scout.clients.bedrock_client import BedrockClient
from job_scout.clients.dynamodb_client import DynamoDBClient
from job_scout.clients.s3_client import S3ResumeStore
from job_scout.config import get_settings
from job_scout.repository import Repository
from job_scout.validation import ValidationError, parse_jd_event

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@lru_cache
def get_repository() -> Repository:
    settings = get_settings()
    return Repository(DynamoDBClient(settings.table_name, settings.aws_region))


@lru_cache
def get_resume_store() -> S3ResumeStore:
    settings = get_settings()
    return S3ResumeStore(
        settings.resume_bucket,
        settings.resume_object_key,
        settings.aws_region,
    )


@lru_cache
def get_fit_assessor() -> FitAssessor:
    settings = get_settings()
    bedrock_client = BedrockClient(
        settings.bedrock_model_id,
        settings.aws_region,
        settings.comp_baseline,
    )
    return FitAssessor(bedrock_client, settings.bedrock_model_id)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    batch_item_failures: list[dict[str, str]] = []
    repository = get_repository()

    for record in event["Records"]:
        message_id = record["messageId"]
        job_id = None
        try:
            body = json.loads(record["body"])
            jd_event = parse_jd_event(body)
            job_id = jd_event.job_id
            repository.create_received_record(jd_event)
            repository.mark_processing(job_id)
            resume_text = get_resume_store().get_resume_text()
            result = get_fit_assessor().assess(resume_text, jd_event)
            repository.mark_completed(
                job_id, result["job_fit"], result["compensation_fit"]
            )
        except (json.JSONDecodeError, ValidationError):
            # Poison pill: retrying won't help, drop it without
            # reporting a batch item failure.
            logger.warning(
                "Dropping unprocessable message %s",
                message_id,
                exc_info=True,
            )
            continue
        except Exception:
            # Transient failure (Bedrock/DynamoDB/S3): let SQS retry
            # just this message, up to the queue's maxReceiveCount.
            logger.exception(
                "Failed processing message %s (job_id=%s)",
                message_id,
                job_id,
            )
            if job_id is not None:
                try:
                    repository.mark_failed(job_id, str(sys.exc_info()[1]))
                except Exception:
                    logger.exception(
                        "Also failed to write FAILED record for %s", job_id
                    )
            batch_item_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_item_failures}
