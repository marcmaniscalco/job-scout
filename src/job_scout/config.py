"""Runtime configuration loaded from Lambda environment variables."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    table_name: str
    resume_bucket: str
    resume_object_key: str
    bedrock_model_id: str
    aws_region: str
    comp_baseline: str | None


@lru_cache
def get_settings() -> Settings:
    return Settings(
        table_name=os.environ["TABLE_NAME"],
        resume_bucket=os.environ["RESUME_BUCKET"],
        resume_object_key=os.environ.get("RESUME_OBJECT_KEY", "resume.txt"),
        bedrock_model_id=os.environ["BEDROCK_MODEL_ID"],
        aws_region=os.environ.get(
            "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        ),
        comp_baseline=os.environ.get("COMP_BASELINE") or None,
    )
