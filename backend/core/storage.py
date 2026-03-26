"""Cloudflare R2 storage helpers via S3-compatible API."""

import boto3
from botocore.config import Config
from config import get_settings


class R2Storage:
    """Wrapper around boto3 S3 client configured for Cloudflare R2.

    The client is created lazily on first use so that importing this
    module does not crash when R2 credentials are absent (e.g. local dev
    without a .env file, or during test imports).
    """

    def __init__(self):
        self._client = None
        self._bucket = None

    def _get_client(self):
        """Return the boto3 S3 client, creating it on first call."""
        if self._client is None:
            settings = get_settings()
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.r2_endpoint_url,
                aws_access_key_id=settings.cloudflare_r2_access_key_id,
                aws_secret_access_key=settings.cloudflare_r2_secret_access_key,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )
            self._bucket = settings.cloudflare_r2_bucket
        return self._client

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload bytes to R2. Returns the object key."""
        self._get_client().put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    async def download(self, key: str) -> bytes:
        """Download an object from R2 as bytes."""
        response = self._get_client().get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed URL for temporary access."""
        return self._get_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    async def delete(self, key: str) -> None:
        """Delete an object from R2."""
        self._get_client().delete_object(Bucket=self._bucket, Key=key)

    async def list_objects(self, prefix: str) -> list[dict]:
        """List objects under a prefix."""
        response = self._get_client().list_objects_v2(Bucket=self._bucket, Prefix=prefix)
        return [
            {"key": obj["Key"], "size": obj["Size"], "modified": obj["LastModified"]}
            for obj in response.get("Contents", [])
        ]


# Singleton instance — client is created lazily on first method call
storage = R2Storage()
