import boto3
from fastapi import UploadFile
from app.core.config import get_settings

class S3Repository:
    def __init__(self):
        settings = get_settings()
        self.bucket = settings.s3_bucket_name
        
        s3_kwargs = {
            "region_name": settings.aws_region,
        }
        if settings.s3_endpoint_url:
            s3_kwargs["endpoint_url"] = settings.s3_endpoint_url
        if settings.aws_access_key_id:
            s3_kwargs["aws_access_key_id"] = settings.aws_access_key_id
            s3_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            
        self.s3_client = boto3.client("s3", **s3_kwargs)

    def upload_file(self, file_obj, s3_key: str, content_type: str | None = None) -> str:
        """Upload a file-like object to S3."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.s3_client.upload_fileobj(
            file_obj,
            self.bucket,
            s3_key,
            ExtraArgs=extra_args if extra_args else None
        )
        return s3_key

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """Generate a time-limited presigned GET URL for controlled private access (FR-DOC-003)."""
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expiration
        )

    def file_exists(self, s3_key: str) -> bool:
        """Check if an object exists in the S3 bucket."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except Exception:
            return False
