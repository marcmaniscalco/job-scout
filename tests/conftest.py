import boto3
import pytest
from moto import mock_aws

TABLE_NAME = "test-jobs-table"
BUCKET_NAME = "test-resume-bucket"
QUEUE_NAME = "test-jd-queue"
REGION = "us-east-1"


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)


@pytest.fixture
def aws_mock(aws_credentials):
    with mock_aws():
        yield


@pytest.fixture
def jobs_table(aws_mock):
    resource = boto3.resource("dynamodb", region_name=REGION)
    table = resource.create_table(
        TableName=TABLE_NAME,
        BillingMode="PAY_PER_REQUEST",
        KeySchema=[{"AttributeName": "job_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "job_id", "AttributeType": "S"},
            {"AttributeName": "status", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "StatusCreatedAtIndex",
                "KeySchema": [
                    {"AttributeName": "status", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )
    table.wait_until_exists()
    return table


@pytest.fixture
def resume_bucket(aws_mock):
    client = boto3.client("s3", region_name=REGION)
    client.create_bucket(Bucket=BUCKET_NAME)
    return client


@pytest.fixture
def sqs_queue(aws_mock):
    client = boto3.client("sqs", region_name=REGION)
    response = client.create_queue(QueueName=QUEUE_NAME)
    return client, response["QueueUrl"]
