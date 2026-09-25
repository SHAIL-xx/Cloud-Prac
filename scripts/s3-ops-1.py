# Importing essential libraries
import boto3

# Creating a s3 bucket
localstack_endpoint = "http://localhost:4566"
region = "ap-south-1"
my_bucket = "test-s3-bucket"
s3 = boto3.resource(
    's3',
    aws_access_key_id = "test",
    aws_secret_access_key = "test",
    endpoint_url = localstack_endpoint,
    region_name = region
)

# Checking if bucket exists,if not creating new one
all_my_buckets = [bucket.name for bucket in s3.buckets.all()]
if my_bucket not in all_my_buckets:
    print(f"The bucket does not exist.Creating a new bucket with name {my_bucket}")
    s3.create_bucket(Bucket = my_bucket,CreateBucketConfiguration = {'LocationConstraint':'ap-south-1'})
    print(f"The bucket with name {my_bucket} created successfully")
else:
    print(f"The bucket with name {my_bucket} already exists")

# Creating files to insert in the bucket
file_name_1 = "file_1.txt"
file_content_1 = "This is the first sample file"
file_name_2 = "file_2.txt"
file_content_2 = "This is the second sample file"

# Inserting the files inside the bucket
s3.Bucket(my_bucket).put_object(Key = file_name_1,Body = file_content_1)
s3.Bucket(my_bucket).put_object(Key = file_name_2,Body = file_content_2)
print(f"Inserting two files {file_name_1} and {file_name_2} in {my_bucket} successfully")

# Read and print the file from the bucket
obj = s3.Object(my_bucket,file_name_1)
body = obj.get()['Body'].read()
print(body)

# Update the files from file 1 to file 2
s3.Object(my_bucket,file_name_1).put(Body = file_content_2)
obj = s3.Object(my_bucket,file_name_1)
body = obj.get()['Body'].read()
print(body)

# Deleting the files from the bucket
s3.Object(my_bucket,file_name_1).delete()
s3.Object(my_bucket,file_name_2).delete()
print(f"{file_name_1} and {file_name_2} deleted successfully")

# Deleting the bucket
bucket = s3.Bucket(my_bucket)
bucket.delete()
print(f"Bucket with name {my_bucket} deleted ")
