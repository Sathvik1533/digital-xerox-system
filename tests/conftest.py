"""
Test configuration and fixtures.
Uses pytest + moto (AWS mocking library) so tests never hit real AWS.
"""
import os
import pytest
from fastapi.testclient import TestClient
import boto3
from moto import mock_aws

# Ensure moto doesn't accidentally hit real AWS
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"

from app.main import app
from app.core.config import get_settings

@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"

@pytest.fixture(scope="function")
def aws_env(aws_credentials):
    with mock_aws():
        settings = get_settings()
        # Setup S3
        s3 = boto3.client("s3", region_name="ap-south-1")
        s3.create_bucket(
            Bucket=settings.s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "ap-south-1"},
        )
        # Setup DynamoDB
        ddb = boto3.resource("dynamodb", region_name="ap-south-1")
        table = ddb.create_table(
            TableName=settings.dynamodb_table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=settings.dynamodb_table_name)
        yield {"s3": s3, "dynamodb": ddb, "table": table}


@pytest.fixture
def client(aws_env):
    """FastAPI test client fixture with mocked AWS environment."""
    with TestClient(app) as c:
        yield c
