from job_scout.config import get_settings


def test_get_settings_reads_env_vars(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("TABLE_NAME", "jobs-table")
    monkeypatch.setenv("RESUME_BUCKET", "resume-bucket")
    monkeypatch.setenv("RESUME_OBJECT_KEY", "my-resume.txt")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "test-model")
    monkeypatch.setenv("AWS_REGION", "us-west-2")

    settings = get_settings()

    assert settings.table_name == "jobs-table"
    assert settings.resume_bucket == "resume-bucket"
    assert settings.resume_object_key == "my-resume.txt"
    assert settings.bedrock_model_id == "test-model"
    assert settings.aws_region == "us-west-2"
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
