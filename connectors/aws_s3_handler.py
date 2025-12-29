import boto3
import io

class S3Handler:
    def __init__(self):
        print("✅ AWS S3 Handler loaded.")

    def get_buckets(self, access_key, secret_key, region):
        try:
            s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
            response = s3.list_buckets()
            return [b['Name'] for b in response.get('Buckets', [])]
        except Exception as e:
            print(f"❌ S3 Error: {e}")
            return []

    def get_files(self, access_key, secret_key, region, bucket_name):
        try:
            s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
            response = s3.list_objects_v2(Bucket=bucket_name)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            return []

    def download_file(self, access_key, secret_key, region, bucket_name, file_key):
        try:
            s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
            obj = s3.get_object(Bucket=bucket_name, Key=file_key)
            return obj['Body'].read()
        except Exception as e:
            print(f"❌ S3 Download Error: {e}")
            return b""