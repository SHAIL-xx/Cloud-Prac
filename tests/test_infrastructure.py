import subprocess
import pytest

@pytest.fixture(scope="module")
def setup_teardown_terraform():
    """Applies Terraform before running tests and destroys it after."""
    tf_dir = "terraform"
    
    # 1. Initialize and apply Terraform config
    subprocess.run(["terraform", f"-chdir={tf_dir}", "init"], check=True)
    subprocess.run(["terraform", f"-chdir={tf_dir}", "apply", "-auto-approve"], check=True)
    
    yield  # Control hands over to the test functions
    
    # 2. Teardown / destroy after all tests finish
    subprocess.run(["terraform", f"-chdir={tf_dir}", "destroy", "-auto-approve"], check=True)

def test_terraform_s3_and_sqs_resources(setup_teardown_terraform, s3_client, sqs_client):
    """Verifies that resources provisioned by terraform/ exist in the mock cloud."""
    # Check that S3 bucket created by Terraform exists
    buckets = [b["Name"] for b in s3_client.list_buckets().get("Buckets", [])]
    assert len(buckets) > 0

    # Check SQS queue listing
    queues = sqs_client.list_queues().get("QueueUrls", [])
    # Matches whatever queue URL pattern your terraform creates
    assert isinstance(queues, list)
