"""七牛云 Kodo 上传 Provider。"""

from pathlib import Path

from qiniu import Auth, BucketManager, put_file

from app.config import cloud_runtime_config
from app.providers.cloud_provider import CloudProvider, CloudUploadResult


class QiniuCloudProvider(CloudProvider):
    """七牛云 Kodo 对象存储上传。

    使用七牛 Python SDK 上传文件到指定 Bucket，
    返回公开访问 URL（基于配置的域名或测试域名）。
    """

    @property
    def provider_name(self) -> str:
        return "qiniu"

    def upload(self, file_path: str, asset_id: str, asset_name: str) -> CloudUploadResult:
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"源文件不存在：{file_path}")

        access_key = cloud_runtime_config.access_key
        secret_key = cloud_runtime_config.secret_key
        bucket_name = cloud_runtime_config.bucket

        if not (access_key and secret_key and bucket_name):
            raise RuntimeError("七牛云凭证未配置：需要 access_key、secret_key 和 bucket")

        auth = Auth(access_key, secret_key)
        key = f"{asset_id}/{source.name}"
        token = auth.upload_token(bucket_name, key, 3600)

        ret, resp = put_file(token, key, str(source))
        if resp.status_code != 200 or ret is None:
            raise RuntimeError(
                f"七牛云上传失败（{resp.status_code}）：{resp.text[:500]}"
            )

        # Build public URL
        base = cloud_runtime_config.domain.strip().rstrip("/") if cloud_runtime_config.domain else None
        if not base:
            # Fallback: construct default test domain URL
            _, bucket_info = BucketManager(auth).bucket_info(bucket_name)
            base = f"https://{bucket_name}.s3.cn-south-1.qiniucs.com"

        cloud_url = f"{base}/{key}"
        return CloudUploadResult(
            cloud_url=cloud_url,
            provider=self.provider_name,
            metadata={
                "asset_name": asset_name,
                "bucket": bucket_name,
                "key": key,
                "qiniu_hash": ret.get("hash", ""),
            },
        )
