from job_scout.config import get_settings


def test_get_settings_reads_env_vars(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("TABLE_NAME", "jobs-table")
    monkeypatch.setenv("RESUME_BUCKET", "resume-bucket")
    monkeypatch.setenv("RESUME_OBJECT_KEY", "my-resume.txt")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("COMP_BASELINE", "$180,000 total comp")

    settings = get_settings()

    assert settings.table_name == "jobs-table"
    assert settings.resume_bucket == "resume-bucket"
    assert settings.resume_object_key == "my-resume.txt"
    assert settings.bedrock_model_id == "test-model"
    assert settings.aws_region == "us-west-2"
    assert settings.comp_baseline == "$180,000 total comp"
    get_settings.cache_clear()


def test_get_settings_treats_empty_comp_baseline_as_none(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("TABLE_NAME", "jobs-table")
    monkeypatch.setenv("RESUME_BUCKET", "resume-bucket")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")
    monkeypatch.setenv("COMP_BASELINE", "")

    settings = get_settings()

    assert settings.comp_baseline is None
    get_settings.cache_clear()


def test_get_settings_defaults_resume_object_key(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("TABLE_NAME", "jobs-table")
    monkeypatch.setenv("RESUME_BUCKET", "resume-bucket")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")
    monkeypatch.delenv("RESUME_OBJECT_KEY", raising=False)

    settings = get_settings()

    assert settings.resume_object_key == "resume.txt"
    get_settings.cache_clear()
