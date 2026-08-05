from unittest.mock import patch

from job_scout.clients.s3_client import S3ResumeStore
from tests.conftest import BUCKET_NAME, REGION


def test_get_resume_text_fetches_and_decodes_object(resume_bucket):
    resume_bucket.put_object(
        Bucket=BUCKET_NAME, Key="resume.txt", Body=b"My resume text"
    )
    store = S3ResumeStore(BUCKET_NAME, "resume.txt", REGION)

    assert store.get_resume_text() == "My resume text"


def test_get_resume_text_caches_after_first_call(resume_bucket):
    resume_bucket.put_object(
        Bucket=BUCKET_NAME, Key="resume.txt", Body=b"My resume text"
    )
    store = S3ResumeStore(BUCKET_NAME, "resume.txt", REGION)

    with patch.object(
        store._client, "get_object", wraps=store._client.get_object
    ) as spy:
        store.get_resume_text()
        store.get_resume_text()

    assert spy.call_count == 1
