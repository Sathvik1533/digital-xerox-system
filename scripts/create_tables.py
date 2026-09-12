# ==============================================================================
# scripts/create_tables.py
# Provision / verify cloud resources (DynamoDB Table & Private S3 Bucket)
#
# Safe and idempotent: Checks if resources exist before creating.
# ==============================================================================
import os
import sys
import boto3
from botocore.exceptions import ClientError

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import get_settings


def create_dynamodb_table(dynamodb_client, table_name: str):
    print(f'[*] Checking DynamoDB table: {table_name}...')
    try:
        dynamodb_client.describe_table(TableName=table_name)
        print(f'    Table "{table_name}" already exists and is active.')
        return
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            print(f'[!] Error checking DynamoDB table: {e}')
            raise

    print(f'[*] Creating DynamoDB table: {table_name} (BillingMode: PAY_PER_REQUEST)...')
    dynamodb_client.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
        ],
        BillingMode='PAY_PER_REQUEST',
    )
    print(f'[*] Waiting for DynamoDB table "{table_name}" to become ACTIVE...')
    waiter = dynamodb_client.get_waiter('table_exists')
    waiter.wait(TableName=table_name)
    print(f'[+] DynamoDB table "{table_name}" created successfully.')


def create_s3_bucket(s3_client, bucket_name: str, region: str):
    print(f'[*] Checking S3 bucket: {bucket_name} in region {region}...')
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f'    S3 bucket "{bucket_name}" already exists and is accessible.')
        return
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code not in ['404', 'NoSuchBucket']:
            print(f'[!] Error checking S3 bucket: {e}')
            raise

    print(f'[*] Creating private S3 bucket: {bucket_name} in {region}...')
    bucket_config = {}
    if region != 'us-east-1':
        bucket_config['CreateBucketConfiguration'] = {'LocationConstraint': region}

    s3_client.create_bucket(Bucket=bucket_name, **bucket_config)

    # Enforce private bucket security (Block all public access)
    print(f'[*] Enforcing S3 Block Public Access on "{bucket_name}"...')
    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True,
        },
    )
    print(f'[+] S3 bucket "{bucket_name}" created and secured successfully.')


def main():
    settings = get_settings()
    region = settings.aws_region
    table_name = settings.dynamodb_table_name
    bucket_name = settings.s3_bucket_name

    print('==================================================================')
    print('  Digital Xerox System — AWS Cloud Provisioning Verification')
    print('==================================================================')
    print(f'  Target Region:  {region}')
    print(f'  DynamoDB Table: {table_name}')
    print(f'  S3 Bucket:      {bucket_name}')
    print('==================================================================')
    print('')

    boto_kwargs = {'region_name': region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        boto_kwargs['aws_access_key_id'] = settings.aws_access_key_id
        boto_kwargs['aws_secret_access_key'] = settings.aws_secret_access_key

    dynamodb_client = boto3.client('dynamodb', **boto_kwargs)
    s3_client = boto3.client('s3', **boto_kwargs)

    create_dynamodb_table(dynamodb_client, table_name)
    create_s3_bucket(s3_client, bucket_name, region)

    print('')
    print('[+] Verification complete! Cloud resources are ready.')


if __name__ == '__main__':
    main()
