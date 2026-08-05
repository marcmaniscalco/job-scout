"""Thin wrapper around the Bedrock Converse API for fit assessment."""

from typing import Any

import boto3

from job_scout.assessment.prompts import (
    SYSTEM_PROMPT,
    TOOL_NAME,
    TOOL_SPEC,
    build_user_message,
)
from job_scout.models import JDEvent


class BedrockAssessmentError(Exception):
    """Raised when Bedrock doesn't return a usable tool-use response."""


class BedrockClient:
    def __init__(self, model_id: str, region_name: str | None = None):
        self._model_id = model_id
        self._client = boto3.client("bedrock-runtime", region_name=region_name)

    def assess_fit(
        self, resume_text: str, jd_event: JDEvent
    ) -> dict[str, Any]:
        response = self._client.converse(
            modelId=self._model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"text": build_user_message(resume_text, jd_event)}
                    ],
                }
            ],
            toolConfig={
                "tools": [TOOL_SPEC],
                "toolChoice": {"tool": {"name": TOOL_NAME}},
            },
            inferenceConfig={"maxTokens": 2000, "temperature": 0.2},
        )
        return self._parse_tool_input(response)

    @staticmethod
    def _parse_tool_input(response: dict[str, Any]) -> dict[str, Any]:
        if response.get("stopReason") != "tool_use":
            raise BedrockAssessmentError(
                f"expected stopReason 'tool_use', got "
                f"{response.get('stopReason')!r}"
            )
        content = (
            response.get("output", {}).get("message", {}).get("content", [])
        )
        for block in content:
            tool_use = block.get("toolUse")
            if tool_use and tool_use.get("name") == TOOL_NAME:
                return tool_use["input"]
        raise BedrockAssessmentError(
            f"no '{TOOL_NAME}' tool_use block found in Bedrock response"
        )
