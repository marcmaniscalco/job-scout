import pytest

from job_scout.validation import ValidationError, parse_jd_event


def test_parse_jd_event_with_full_payload():
    body = {
        "job_id": "jd-1",
        "title": "Backend Engineer",
        "jd_text": "Build things.",
        "company": "Acme",
        "location": "Remote",
        "salary": "$150k",
        "source": "manual",
        "url": "https://example.com/jobs/1",
        "in_office_days_per_week": 2,
    }
    event = parse_jd_event(body)
    assert event.job_id == "jd-1"
    assert event.title == "Backend Engineer"
    assert event.jd_text == "Build things."
    assert event.company == "Acme"
    assert event.in_office_days_per_week == 2


def test_parse_jd_event_generates_job_id_when_missing():
    body = {"title": "Backend Engineer", "jd_text": "Build things."}
    event = parse_jd_event(body)
    assert event.job_id
    assert event.source == "manual"


def test_parse_jd_event_passes_through_unknown_fields_without_error():
    body = {
        "title": "Backend Engineer",
        "jd_text": "Build things.",
        "future_job_hunter_field": "some value",
    }
    event = parse_jd_event(body)
    assert event.title == "Backend Engineer"


@pytest.mark.parametrize(
    "body",
    [
        {"jd_text": "Build things."},
        {"title": "Backend Engineer"},
        {"title": "", "jd_text": "Build things."},
        {"title": "Backend Engineer", "jd_text": "   "},
        {"title": 123, "jd_text": "Build things."},
    ],
)
def test_parse_jd_event_rejects_missing_or_invalid_required_fields(body):
    with pytest.raises(ValidationError):
        parse_jd_event(body)


def test_parse_jd_event_rejects_non_dict_body():
    with pytest.raises(ValidationError):
        parse_jd_event(["not", "a", "dict"])


def test_parse_jd_event_ignores_non_int_in_office_days():
    body = {
        "title": "Backend Engineer",
        "jd_text": "Build things.",
        "in_office_days_per_week": "two",
    }
    event = parse_jd_event(body)
    assert event.in_office_days_per_week is None
