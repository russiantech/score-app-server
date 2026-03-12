import boto3
from .base import StorageProvider


class S3Storage(StorageProvider):

    def __init__(self, config):

        self.bucket = config.bucket_name

        self.client = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )

    def upload(self, file, filename, content_type, subdir=None):

        key = f"{subdir}/{filename}" if subdir else filename

        self.client.upload_fileobj(
            file,
            self.bucket,
            key,
            ExtraArgs={"ContentType": content_type}
        )

        return f"{self.client.meta.endpoint_url}/{self.bucket}/{key}"

    def delete(self, file_path):

        self.client.delete_object(
            Bucket=self.bucket,
            Key=file_path
        )

