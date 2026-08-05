"""Prompt and tool-spec construction for the Bedrock fit assessment."""

from job_scout.models import JDEvent

TOOL_NAME = "record_fit_assessment"

RATING_TIERS = ("Strong", "Good", "OK", "Fair", "Weak")

SYSTEM_PROMPT = """\
You are assessing a single job description against a candidate's \
resume. Assess this JD entirely on its own; you have no visibility \
into other JDs and must never imply a ranking or comparison against \
other opportunities.

Score two independent dimensions, each on the same five-tier scale: \
Strong, Good, OK, Fair, Weak (Strong is best, Weak is worst, OK is \
the explicit middle tier).

1. job_fit: how well the candidate's skills and experience match the \
role's requirements.
   - Weight required/must-have skills heavily. Weight "nice-to-have" \
gaps much less.
   - Calibrate the rating almost entirely on required skills: Strong \
= nearly all required skills met, gaps confined to nice-to-haves. \
Good = most required skills met, one real but non-core gap. OK = \
solid general overlap but a real gap in one required/differentiating \
skill. Fair = multiple required skills are gaps, or one major \
required skill is largely unevidenced, but there's still a plausible \
path. Weak = a hard-filter / core required skill isn't evidenced at \
all.
   - In "reasoning", you MUST separately and explicitly label \
Strengths and Gaps as two distinct labeled sections ("Strengths: ..." \
then "Gaps: ..."). Never fold gaps into a vague overall gloss, and \
map strengths to specific, concrete evidence from the resume rather \
than generic claims.
   - Do not assess company culture. Culture cannot be judged from a \
job posting's text or tone alone; do not attempt it.

2. compensation_fit: how the compensation described in the job \
description compares to a fair/competitive package for this \
candidate.
   - Keep this brief: a one-line factual note on the posted band if \
one is stated (e.g. "posted band is $X-$Y"), plus the tier rating. \
Do not produce a multi-paragraph compensation breakdown, equity \
analysis, or negotiation framing.
   - If the job description does not mention salary or compensation, \
say so explicitly instead of guessing a number, and rate it OK \
(insufficient information, neither positive nor negative).
{comp_baseline_instruction}

Call the record_fit_assessment tool with your results.\
"""

_FIT_SCHEMA = {
    "type": "object",
    "properties": {
        "rating": {"type": "string", "enum": list(RATING_TIERS)},
        "reasoning": {"type": "string"},
    },
    "required": ["rating", "reasoning"],
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


def build_system_prompt(comp_baseline: str | None) -> str:
    if comp_baseline:
        instruction = (
            f"   - Rate against a baseline total compensation of "
            f"{comp_baseline}: Strong/Good if the posted band clearly "
            f"meets or exceeds it, Fair/Weak if it falls well short, "
            f"OK if it's roughly at parity or unclear."
        )
    else:
        instruction = (
            "   - No personal compensation baseline is configured; "
            "rate only on whether the posted band looks reasonable "
            "for the role as described, without comparing it to any "
            "specific number."
        )
    return SYSTEM_PROMPT.format(comp_baseline_instruction=instruction)


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
