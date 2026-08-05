from job_scout.models import FitAssessment, JobRecord, JobStatus


def test_fit_assessment_round_trip():
    fit = FitAssessment(
        rating="Strong", reasoning="Strong match", model_id="m1"
    )
    assert FitAssessment.from_item(fit.to_item()) == fit


def test_job_record_round_trip_without_fit_results():
    record = JobRecord(
        job_id="abc",
        title="Engineer",
        jd_text="Do engineering things.",
        status=JobStatus.RECEIVED,
        created_at="2026-08-04T00:00:00+00:00",
        updated_at="2026-08-04T00:00:00+00:00",
    )
    item = record.to_item()

    assert "job_fit" not in item
    assert "compensation_fit" not in item
    assert "distance_fit" not in item
    assert "company" not in item

    rebuilt = JobRecord.from_item(item)
    assert rebuilt == record


def test_job_record_round_trip_with_fit_results():
    job_fit = FitAssessment(
        rating="Strong", reasoning="Great fit", model_id="m1"
    )
    compensation_fit = FitAssessment(
        rating="Fair", reasoning="Below market", model_id="m1"
    )
    record = JobRecord(
        job_id="abc",
        title="Engineer",
        jd_text="Do engineering things.",
        status=JobStatus.COMPLETED,
        created_at="2026-08-04T00:00:00+00:00",
        updated_at="2026-08-04T00:05:00+00:00",
        company="Acme",
        location="Remote",
        salary="$150k",
        job_fit=job_fit,
        compensation_fit=compensation_fit,
    )
    item = record.to_item()

    assert item["job_fit"] == job_fit.to_item()
    assert item["compensation_fit"] == compensation_fit.to_item()
    assert JobRecord.from_item(item) == record


def test_job_record_from_item_ignores_absent_optional_fields():
    item = {
        "job_id": "abc",
        "title": "Engineer",
        "jd_text": "text",
        "status": JobStatus.RECEIVED,
        "created_at": "t0",
        "updated_at": "t0",
    }
    record = JobRecord.from_item(item)
    assert record.company is None
    assert record.job_fit is None
    assert record.distance_fit is None
    assert record.source == "manual"
