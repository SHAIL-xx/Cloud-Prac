import os
import boto3
from dotenv import load_dotenv

load_dotenv()

def get_ec2_resource(endpoint_url=None, region_name="ap-south-1"):
    """Creates an EC2 resource client using environment variables."""
    return boto3.resource(
        "ec2",
        endpoint_url=endpoint_url or os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566"),
        region_name=region_name or os.getenv("AWS_DEFAULT_REGION", "ap-south-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    )

def find_instance_by_name(ec2, name):
    """Finds an active/existing instance ID by its Name tag, ignoring terminated ones."""
    for instance in ec2.instances.all():
        # Ignore instances that are already dead or shutting down
        if instance.state["Name"] in ["shutting-down", "terminated"]:
            continue

        if instance.tags:
            for tag in instance.tags:
                if tag.get("Key") == "Name" and tag.get("Value") == name:
                    return instance.id
    return None

def create_ec2_instance(ec2, name="test-ec2-instance", image_id="ami-123456789", instance_type="t3.micro"):
    """Provisions a new instance if one does not already exist."""
    existing_id = find_instance_by_name(ec2, name)
    if existing_id:
        print(f"The ec2 instance with name {name} already exists (ID: {existing_id})")
        return existing_id, False

    instances = ec2.create_instances(
        ImageId=image_id,
        MinCount=1,
        MaxCount=1,
        InstanceType=instance_type,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": name}]
            }
        ]
    )
    instance_id = instances[0].id
    print(f"The ec2 instance with name {name} and id {instance_id} has been created")
    return instance_id, True

def stop_instance(ec2, instance_id):
    """Stops an EC2 instance."""
    instance = ec2.Instance(instance_id)
    instance.stop()
    return instance_id

def start_instance(ec2, instance_id):
    """Starts an EC2 instance."""
    instance = ec2.Instance(instance_id)
    instance.start()
    return instance_id

def terminate_instance(ec2, instance_id):
    """Terminates an EC2 instance."""
    instance = ec2.Instance(instance_id)
    instance.terminate()
    return instance_id

if __name__ == "__main__":
    # Runs ONLY when executed directly, ignored when imported by pytest
    ec2 = get_ec2_resource()
    name = "test-ec2-instance"

    instance_id, created = create_ec2_instance(ec2, name)
    stop_instance(ec2, instance_id)
    start_instance(ec2, instance_id)
    terminate_instance(ec2, instance_id)
