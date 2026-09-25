# Importing essential libraries
import boto3

# Creating an ec2 instance
localstack_endpoint = "http://localhost:4566"
region = "ap-south-1"
ec2 = boto3.resource(
    'ec2',
    aws_access_key_id = "test",
    aws_secret_access_key = "test",
    endpoint_url = localstack_endpoint,
    region_name = region
)

# Intializing the name of the bucket
instance_name = "test-ec2-instance"

# Checking if the instance already exists,if not creating a new one
all_my_instances = ec2.instances.all()
instance_exists = False
instance_id = None
for instance in all_my_instances:
    for tags in instance.tags:
        if tags['Key'] == 'Name' and tags['Value'] == instance_name:
            instance_exists = True
            instance_id = instance.id
            print(f"The ec2 instance with name {instance_name} already exists")
            break
    if instance_exists:
        break

if not instance_exists:
    new_instance = ec2.create_instances(
        ImageId = "ami-123456789",
        MinCount = 1,
        MaxCount = 1,
        InstanceType = "t3.micro",
        KeyName = "test",
        TagSpecifications = [
            {
                'ResourceType':'instance',
                'Tags':[
                    {
                        'Key':'Name',
                        'Value':instance_name
                    }
                ]
            }
        ]
    )
    instance_id = new_instance[0].id
    print(f"The ec2 instance with name {instance_name} and id {instance_id} has been created")

# Stopping an instance
ec2.Instance(instance_id).stop()
print(f"Instance with id {instance_id} has been stopped ")

# Starting an instance
ec2.Instance(instance_id).start()
print(f"Instance with id {instance_id} has been started ")

# Terminating an instance
ec2.Instance(instance_id).terminate()
print(f"Instance with id {instance_id} has been terminated ")

