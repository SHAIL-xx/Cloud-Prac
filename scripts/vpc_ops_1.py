import os
import boto3
from dotenv import load_dotenv

load_dotenv()

def get_ec2_client(endpoint_url=None, region_name="ap-south-1"):
    """Factory helper to obtain an EC2 client."""
    return boto3.client(
        "ec2",
        endpoint_url=endpoint_url or os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566"),
        region_name=region_name or os.getenv("AWS_DEFAULT_REGION", "ap-south-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    )

def get_or_create_vpc(ec2_client, vpc_name: str, cidr_block: str = "10.0.0.0/16") -> tuple[str, bool]:
    """Finds an existing VPC by Name tag or creates a new one."""
    resp = ec2_client.describe_vpcs(Filters=[{"Name": "tag:Name", "Values": [vpc_name]}])
    vpcs = resp.get("Vpcs", [])
    if vpcs:
        return vpcs[0]["VpcId"], False

    vpc_resp = ec2_client.create_vpc(CidrBlock=cidr_block)
    vpc_id = vpc_resp["Vpc"]["VpcId"]
    ec2_client.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": vpc_name}])
    return vpc_id, True

def get_or_create_internet_gateway(ec2_client, ig_name: str, vpc_id: str) -> tuple[str, bool]:
    """Finds an existing IGW or creates and attaches a new one to the specified VPC."""
    resp = ec2_client.describe_internet_gateways(Filters=[{"Name": "tag:Name", "Values": [ig_name]}])
    gateways = resp.get("InternetGateways", [])
    if gateways:
        return gateways[0]["InternetGatewayId"], False

    ig_resp = ec2_client.create_internet_gateway()
    ig_id = ig_resp["InternetGateway"]["InternetGatewayId"]
    ec2_client.create_tags(Resources=[ig_id], Tags=[{"Key": "Name", "Value": ig_name}])
    ec2_client.attach_internet_gateway(InternetGatewayId=ig_id, VpcId=vpc_id)
    return ig_id, True

def create_public_route_table(ec2_client, vpc_id: str, ig_id: str, rt_name: str = "public-rt") -> str:
    """Creates a route table with a 0.0.0.0/0 route pointing to the Internet Gateway."""
    rt_resp = ec2_client.create_route_table(VpcId=vpc_id)
    rt_id = rt_resp["RouteTable"]["RouteTableId"]
    ec2_client.create_tags(Resources=[rt_id], Tags=[{"Key": "Name", "Value": rt_name}])

    ec2_client.create_route(
        RouteTableId=rt_id,
        DestinationCidrBlock="0.0.0.0/0",
        GatewayId=ig_id
    )
    return rt_id

def create_subnet(ec2_client, vpc_id: str, cidr_block: str, az: str, subnet_name: str) -> str:
    """Creates a subnet and tags it with a Name."""
    subnet_resp = ec2_client.create_subnet(
        VpcId=vpc_id,
        CidrBlock=cidr_block,
        AvailabilityZone=az
    )
    subnet_id = subnet_resp["Subnet"]["SubnetId"]
    ec2_client.create_tags(Resources=[subnet_id], Tags=[{"Key": "Name", "Value": subnet_name}])
    return subnet_id

def associate_subnet_with_route_table(ec2_client, subnet_id: str, route_table_id: str) -> str:
    """Associates a subnet with a custom route table."""
    resp = ec2_client.associate_route_table(SubnetId=subnet_id, RouteTableId=route_table_id)
    return resp["AssociationId"]

def delete_vpc_stack(ec2_client, vpc_id: str, ig_id: str, route_table_id: str, subnet_ids: list[str]):
    """Cleans up the entire VPC network stack in the correct dependency order."""
    # 1. Disassociate all subnet associations from the custom route table
    if route_table_id:
        try:
            rt_desc = ec2_client.describe_route_tables(RouteTableIds=[route_table_id])
            for rt in rt_desc.get("RouteTables", []):
                for assoc in rt.get("Associations", []):
                    if not assoc.get("Main", False):  # Skip main table association
                        ec2_client.disassociate_route_table(AssociationId=assoc["RouteTableAssociationId"])
        except Exception as e:
            print(f"Warning disassociating route table: {e}")

    # 2. Delete Subnets
    for sid in subnet_ids:
        try:
            ec2_client.delete_subnet(SubnetId=sid)
        except Exception as e:
            print(f"Warning deleting subnet {sid}: {e}")

    # 3. Delete Route Table
    if route_table_id:
        try:
            ec2_client.delete_route_table(RouteTableId=route_table_id)
        except Exception as e:
            print(f"Warning deleting route table {route_table_id}: {e}")

    # 4. Detach & Delete Internet Gateway
    if ig_id:
        try:
            ec2_client.detach_internet_gateway(InternetGatewayId=ig_id, VpcId=vpc_id)
        except Exception as e:
            print(f"Warning detaching IGW {ig_id}: {e}")
        try:
            ec2_client.delete_internet_gateway(InternetGatewayId=ig_id)
        except Exception as e:
            print(f"Warning deleting IGW {ig_id}: {e}")

    # 5. Delete VPC
    if vpc_id:
        try:
            ec2_client.delete_vpc(VpcId=vpc_id)
        except Exception as e:
            print(f"Warning deleting VPC {vpc_id}: {e}")
if __name__ == "__main__":
    client = get_ec2_client()
    vpc_id, _ = get_or_create_vpc(client, "test-vpc-1")
    ig_id, _ = get_or_create_internet_gateway(client, "test-ig-1", vpc_id)
    rt_id = create_public_route_table(client, vpc_id, ig_id, "test-rt-1")

    subnets = [
        create_subnet(client, vpc_id, "10.0.1.0/24", "ap-south-1a", "subnet-1a"),
        create_subnet(client, vpc_id, "10.0.2.0/25", "ap-south-1b", "subnet-1b"),
        create_subnet(client, vpc_id, "10.0.3.0/26", "ap-south-1c", "subnet-1c"),
    ]
    print(f"Provisioned VPC: {vpc_id} with Subnets: {subnets}")
