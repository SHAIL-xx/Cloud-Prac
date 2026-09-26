import os
import boto3
from dotenv import load_dotenv

load_dotenv()

def get_s3_resource(endpoint_url=None, region_name="ap-south-1"):
    """Factory helper to obtain an S3 resource."""
    return boto3.resource(
        "s3",
        endpoint_url=endpoint_url or os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566"),
        region_name=region_name or os.getenv("AWS_DEFAULT_REGION", "ap-south-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    )

def create_bucket_if_not_exists(s3_resource, bucket_name: str, region_name: str = "ap-south-1") -> bool:
    """Creates an S3 bucket if it doesn't already exist. Returns True if created, False if existing."""
    all_buckets = [b.name for b in s3_resource.buckets.all()]
    if bucket_name not in all_buckets:
        if region_name == "us-east-1":
            s3_resource.create_bucket(Bucket=bucket_name)
        else:
            s3_resource.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region_name}
            )
        return True
    return False

def put_file(s3_resource, bucket_name: str, key: str, content: str | bytes):
    """Puts or updates an object in the specified bucket."""
    return s3_resource.Bucket(bucket_name).put_object(Key=key, Body=content)

def get_file_content(s3_resource, bucket_name: str, key: str) -> str:
    """Reads object body and decodes it as UTF-8 string."""
    obj = s3_resource.Object(bucket_name, key)
    return obj.get()["Body"].read().decode("utf-8")

def delete_file(s3_resource, bucket_name: str, key: str):
    """Deletes an object from the specified bucket."""
    return s3_resource.Object(bucket_name, key).delete()

def delete_bucket(s3_resource, bucket_name: str):
    """Deletes the specified bucket."""
    return s3_resource.Bucket(bucket_name).delete()

if __name__ == "__main__":
    s3 = get_s3_resource()
    bucket_name = "test-s3-bucket"

    # 1. Bucket creation
    created = create_bucket_if_not_exists(s3, bucket_name)
    print(f"Bucket {bucket_name} created: {created}")

    # 2. Put files
    put_file(s3, bucket_name, "file_1.txt", "This is the first sample file")
    put_file(s3, bucket_name, "file_2.txt", "This is the second sample file")

    # 3. Read & Update
    print("Read file_1:", get_file_content(s3, bucket_name, "file_1.txt"))
    put_file(s3, bucket_name, "file_1.txt", "This is the second sample file")
    print("Updated file_1:", get_file_content(s3, bucket_name, "file_1.txt"))

    # 4. Clean up
    delete_file(s3, bucket_name, "file_1.txt")
    delete_file(s3, bucket_name, "file_2.txt")
    delete_bucket(s3, bucket_name)
    print(f"Bucket {bucket_name} deleted successfully.")
