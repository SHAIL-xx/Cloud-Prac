import pytest
from scripts.ec2_ops_1 import (
    create_ec2_instance,
    find_instance_by_name,
    stop_instance,
    start_instance,
    terminate_instance
)

def test_ec2_instance_creation_and_discovery(ec2_resource):
    test_instance_name = "pytest-sample-instance"

    # 1. Test creation
    instance_id, created = create_ec2_instance(ec2_resource, name=test_instance_name)
    assert created is True
    assert instance_id.startswith("i-")

    # 2. Test idempotency (should detect existing instance and not recreate)
    second_id, second_created = create_ec2_instance(ec2_resource, name=test_instance_name)
    assert second_created is False
    assert second_id == instance_id

    # 3. Test discovery by name tag
    found_id = find_instance_by_name(ec2_resource, test_instance_name)
    assert found_id == instance_id

    # 4. Cleanup
    terminate_instance(ec2_resource, instance_id)

def test_ec2_lifecycle_states(ec2_resource):
    test_instance_name = "pytest-state-instance"
    instance_id, _ = create_ec2_instance(ec2_resource, name=test_instance_name)

    # Test stop, start, terminate commands complete without error
    stop_instance(ec2_resource, instance_id)
    start_instance(ec2_resource, instance_id)
    terminate_instance(ec2_resource, instance_id)

    # Verify state reflects termination
    instance = ec2_resource.Instance(instance_id)
    instance.reload()
    assert instance.state["Name"] in ["shutting-down", "terminated"]

from scripts.s3_ops_1 import (
    create_bucket_if_not_exists,
    put_file,
    get_file_content,
    delete_file,
    delete_bucket
)

def test_s3_crud_lifecycle(s3_resource):
    bucket_name = "pytest-s3-crud-bucket"
    file_1 = "file_1.txt"
    file_2 = "file_2.txt"
    content_1 = "This is the first sample file"
    content_2 = "This is the second sample file"

    # 1. Create bucket and verify idempotency
    assert create_bucket_if_not_exists(s3_resource, bucket_name) is True
    assert create_bucket_if_not_exists(s3_resource, bucket_name) is False

    # 2. Put files and assert reading content
    put_file(s3_resource, bucket_name, file_1, content_1)
    put_file(s3_resource, bucket_name, file_2, content_2)

    assert get_file_content(s3_resource, bucket_name, file_1) == content_1
    assert get_file_content(s3_resource, bucket_name, file_2) == content_2

    # 3. Update file content
    put_file(s3_resource, bucket_name, file_1, content_2)
    assert get_file_content(s3_resource, bucket_name, file_1) == content_2

    # 4. Delete files and confirm removal
    delete_file(s3_resource, bucket_name, file_1)
    delete_file(s3_resource, bucket_name, file_2)

    objects_remaining = list(s3_resource.Bucket(bucket_name).objects.all())
    assert len(objects_remaining) == 0

    # 5. Delete bucket and verify it no longer exists
    delete_bucket(s3_resource, bucket_name)
    all_bucket_names = [b.name for b in s3_resource.buckets.all()]
    assert bucket_name not in all_bucket_names

from scripts.vpc_ops_1 import (
    get_or_create_vpc,
    get_or_create_internet_gateway,
    create_public_route_table,
    create_subnet,
    associate_subnet_with_route_table,
    delete_vpc_stack
)

def test_vpc_network_stack_lifecycle(ec2_client):
    vpc_name = "pytest-vpc"
    ig_name = "pytest-igw"

    # 1. Create VPC & verify idempotency
    vpc_id, created = get_or_create_vpc(ec2_client, vpc_name, "10.0.0.0/16")
    assert created is True
    assert vpc_id.startswith("vpc-")

    vpc_id_repeat, created_repeat = get_or_create_vpc(ec2_client, vpc_name, "10.0.0.0/16")
    assert created_repeat is False
    assert vpc_id_repeat == vpc_id

    # 2. Create Internet Gateway & attach
    ig_id, ig_created = get_or_create_internet_gateway(ec2_client, ig_name, vpc_id)
    assert ig_created is True
    assert ig_id.startswith("igw-")

    # 3. Create Route Table with default route to IGW
    rt_id = create_public_route_table(ec2_client, vpc_id, ig_id, "pytest-public-rt")
    assert rt_id.startswith("rtb-")

    # Verify route exists in Route Table
    rt_info = ec2_client.describe_route_tables(RouteTableIds=[rt_id])["RouteTables"][0]
    routes = [r.get("DestinationCidrBlock") for r in rt_info["Routes"]]
    assert "0.0.0.0/0" in routes

    # 4. Create 3 Subnets across Availability Zones
    subnet_configs = [
        ("10.0.1.0/24", "ap-south-1a", "pytest-sub-1a"),
        ("10.0.2.0/25", "ap-south-1b", "pytest-sub-1b"),
        ("10.0.3.0/26", "ap-south-1c", "pytest-sub-1c"),
    ]
    created_subnets = []
    for cidr, az, sname in subnet_configs:
        sid = create_subnet(ec2_client, vpc_id, cidr, az, sname)
        assert sid.startswith("subnet-")
        created_subnets.append(sid)

        # Associate subnet with our public route table
        assoc_id = associate_subnet_with_route_table(ec2_client, sid, rt_id)
        assert assoc_id.startswith("rtbassoc-")

    assert len(created_subnets) == 3

    # 5. Clean teardown and confirm deletion
    delete_vpc_stack(ec2_client, vpc_id, ig_id, rt_id, created_subnets)

    remaining_vpcs = ec2_client.describe_vpcs(Filters=[{"Name": "tag:Name", "Values": [vpc_name]}])["Vpcs"]
    assert len(remaining_vpcs) == 0
