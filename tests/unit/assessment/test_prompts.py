from job_scout.assessment.prompts import (
    RATING_TIERS,
    TOOL_SPEC,
    build_system_prompt,
    build_user_message,
)
from job_scout.models import JDEvent


def test_build_user_message_includes_resume_and_jd_fields():
    jd_event = JDEvent(
        job_id="jd-1",
        title="Backend Engineer",
        jd_text="Build scalable systems.",
        company="Acme",
        location="Remote",
        salary="$150k-$180k",
    )

    message = build_user_message("My resume content", jd_event)

    assert "My resume content" in message
    assert "Backend Engineer" in message
    assert "Acme" in message
    assert "Remote" in message
    assert "$150k-$180k" in message
    assert "Build scalable systems." in message


def test_build_user_message_flags_missing_salary():
    jd_event = JDEvent(job_id="jd-1", title="Engineer", jd_text="text")

    message = build_user_message("resume", jd_event)

    assert "not specified" in message


def test_tool_spec_requires_job_fit_and_compensation_fit():
    schema = TOOL_SPEC["toolSpec"]["inputSchema"]["json"]
    assert set(schema["required"]) == {"job_fit", "compensation_fit"}


def test_tool_spec_rating_enum_matches_rating_tiers():
    schema = TOOL_SPEC["toolSpec"]["inputSchema"]["json"]
    for key in ("job_fit", "compensation_fit"):
        assert schema["properties"][key]["properties"]["rating"][
            "enum"
        ] == list(RATING_TIERS)


def test_build_system_prompt_includes_baseline_when_configured():
    prompt = build_system_prompt("$180,000 total comp")

    assert "$180,000 total comp" in prompt
    assert "No personal compensation baseline" not in prompt


def test_build_system_prompt_omits_baseline_when_not_configured():
    prompt = build_system_prompt(None)

    assert "No personal compensation baseline is configured" in prompt


def test_build_system_prompt_instructs_independent_assessment():
    prompt = build_system_prompt(None)

    assert "on its own" in prompt


def test_build_system_prompt_requires_strengths_and_gaps_labels():
    prompt = build_system_prompt(None)

    assert "Strengths" in prompt
    assert "Gaps" in prompt


def test_build_system_prompt_excludes_culture_assessment():
    prompt = build_system_prompt(None)

    assert "culture" in prompt.lower()
    assert "cannot be judged" in prompt.lower()
