from job_scout.assessment.prompts import TOOL_SPEC, build_user_message
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
