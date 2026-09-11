"""
Local development server runner.
Initializes in-memory AWS mock (S3 bucket + DynamoDB table) and starts FastAPI.
Allows end-to-end local testing without needing live AWS credentials.
"""
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import boto3
from moto import mock_aws
import uvicorn

# Mock AWS credentials for local dev
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-south-1")
os.environ.setdefault("AWS_REGION", "ap-south-1")
os.environ.setdefault("DYNAMODB_TABLE_NAME", "digital-xerox-orders")
os.environ.setdefault("S3_BUCKET_NAME", "digital-xerox-documents")
os.environ.setdefault("ENVIRONMENT", "development")

# Start in-memory AWS mocking
mock = mock_aws()
mock.start()

# 1. Initialize S3 Bucket
s3 = boto3.client("s3", region_name="ap-south-1")
s3.create_bucket(
    Bucket="digital-xerox-documents",
    CreateBucketConfiguration={"LocationConstraint": "ap-south-1"},
)
print("✅ Local Amazon S3 initialized (Bucket: digital-xerox-documents)")

# 2. Initialize DynamoDB Table
ddb = boto3.resource("dynamodb", region_name="ap-south-1")
table = ddb.create_table(
    TableName="digital-xerox-orders",
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
table.meta.client.get_waiter("table_exists").wait(TableName="digital-xerox-orders")
print("✅ Local Amazon DynamoDB initialized (Table: digital-xerox-orders)")

print("\n" + "=" * 60)
print("🚀 Digital Xerox System — Local Dev Server Running!")
print("👉 Student UI:         http://localhost:8000/")
print("👉 Interactive Docs:   http://localhost:8000/docs")
print("👉 Health Check:       http://localhost:8000/health")
print("=" * 60 + "\n")

if __name__ == "__main__":
    from app.main import app
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        mock.stop()
