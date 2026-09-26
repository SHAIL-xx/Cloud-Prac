import os
import boto3
import pytest
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
KEY = os.getenv("AWS_ACCESS_KEY_ID", "test")
SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

@pytest.fixture(scope="session")
def ec2_resource():
    """Provides an EC2 resource client configured for LocalStack."""
    return boto3.resource(
        "ec2",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id=KEY,
        aws_secret_access_key=SECRET
    )

@pytest.fixture(scope="session")
def s3_resource():
    """Provides an S3 resource configured for LocalStack."""
    return boto3.resource(
        "s3",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id=KEY,
        aws_secret_access_key=SECRET
    )

@pytest.fixture(scope="session")
def sqs_client():
    """Returns an SQS client configured for the mock cloud."""
    return boto3.client(
        "sqs",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id=KEY,
        aws_secret_access_key=SECRET
    )
