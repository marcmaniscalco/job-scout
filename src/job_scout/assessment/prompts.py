"""Prompt and tool-spec construction for the Bedrock fit assessment."""

from job_scout.models import JDEvent

TOOL_NAME = "record_fit_assessment"

SYSTEM_PROMPT = """\
You are an experienced technical recruiter assessing how well a job \
description matches a candidate's resume. You will be given the \
candidate's resume and a job description, and must score the \
opportunity on two independent dimensions:

1. job_fit: how well the candidate's skills and experience match the \
role's requirements.
2. compensation_fit: how well the compensation described in the job \
description matches what would be a fair/competitive package for \
this candidate. If the job description does not mention salary or \
compensation, say so explicitly in your reasoning instead of \
guessing a number.

For each dimension, provide an integer score from 0 (very poor fit) \
to 100 (excellent fit), and a concise reasoning explaining the score. \
Call the record_fit_assessment tool with your results.\
"""

_FIT_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "reasoning": {"type": "string"},
    },
    "required": ["score", "reasoning"],
}

TOOL_SPEC = {
    "toolSpec": {
        "name": TOOL_NAME,
        "description": (
            "Record the job-fit and compensation-fit assessment for a "
            "job description against a candidate's resume."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "job_fit": _FIT_SCHEMA,
                    "compensation_fit": _FIT_SCHEMA,
                },
                "required": ["job_fit", "compensation_fit"],
            }
        },
    }
}


def build_user_message(resume_text: str, jd_event: JDEvent) -> str:
    salary_line = jd_event.salary or "(not specified in the job posting)"
    return (
        f"# Candidate resume\n{resume_text}\n\n"
        f"# Job description\n"
        f"Title: {jd_event.title}\n"
        f"Company: {jd_event.company or '(unspecified)'}\n"
        f"Location: {jd_event.location or '(unspecified)'}\n"
        f"Salary: {salary_line}\n\n"
        f"{jd_event.jd_text}"
    )
