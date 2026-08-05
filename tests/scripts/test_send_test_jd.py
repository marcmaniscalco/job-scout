import json

import pytest

from scripts.send_test_jd import build_message_body, main, parse_args


def test_build_message_body_from_jd_text():
    args = parse_args(
        [
            "--queue-url",
            "https://example.com/queue",
            "--title",
            "Engineer",
            "--jd-text",
            "Do things",
            "--company",
            "Acme",
        ]
    )

    body = build_message_body(args)

    assert body["title"] == "Engineer"
    assert body["jd_text"] == "Do things"
    assert body["company"] == "Acme"
    assert body["source"] == "manual"
    assert "job_id" in body


def test_build_message_body_uses_provided_job_id():
    args = parse_args(
        [
            "--queue-url",
            "https://example.com/queue",
            "--title",
            "Engineer",
            "--jd-text",
            "Do things",
            "--job-id",
            "jd-42",
        ]
    )

    body = build_message_body(args)

    assert body["job_id"] == "jd-42"


def test_build_message_body_rejects_blank_jd_text():
    args = parse_args(
        [
            "--queue-url",
            "https://example.com/queue",
            "--title",
            "Engineer",
            "--jd-text",
            "   ",
        ]
    )

    with pytest.raises(ValueError):
        build_message_body(args)


def test_main_sends_message_to_queue(sqs_queue):
    client, queue_url = sqs_queue

    exit_code = main(
        [
            "--queue-url",
            queue_url,
            "--title",
            "Engineer",
            "--jd-text",
            "Do things",
        ]
    )

    assert exit_code == 0
    messages = client.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=1
    )
    body = json.loads(messages["Messages"][0]["Body"])
    assert body["title"] == "Engineer"


def test_main_returns_error_without_queue_url(monkeypatch):
    monkeypatch.delenv("JOB_SCOUT_QUEUE_URL", raising=False)

    exit_code = main(["--title", "Engineer", "--jd-text", "Do things"])

    assert exit_code == 1
