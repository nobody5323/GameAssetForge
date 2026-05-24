"""Mock 云端上传 Provider — 模拟上传到云端。"""

import shutil
from pathlib import Path

from app.providers.cloud_provider import CloudProvider, CloudUploadResult

BACKEND_ROOT = Path(__file__).resolve().parents[2]
MOCK_CLOUD_DIR = BACKEND_ROOT / "runtime" / "mock-cloud"


class MockCloudProvider(CloudProvider):
    """模拟云端上传。

    将文件复制到 backend/runtime/mock-cloud/ 目录，
    返回 cloud://mock/{asset_id}/{filename} 格式的模拟 URL。
    """

    @property
    def provider_name(self) -> str:
        return "mock_cloud"

    def upload(self, file_path: str, asset_id: str, asset_name: str) -> CloudUploadResult:
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"源文件不存在：{file_path}")

        dest_dir = MOCK_CLOUD_DIR / asset_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / source.name
        shutil.copy2(source, dest_file)

        cloud_url = f"cloud://mock/{asset_id}/{source.name}"
        return CloudUploadResult(
            cloud_url=cloud_url,
            provider=self.provider_name,
            metadata={
                "mock_cloud_dir": str(dest_dir),
                "original_path": str(source),
                "asset_name": asset_name,
            },
        )
