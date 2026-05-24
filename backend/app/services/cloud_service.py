"""云端上传服务 — 协调 Provider 上传并更新素材 cloudUrl。"""

from pathlib import Path

from app.models.asset_models import AssetRecord
from app.providers.cloud_provider import CloudProvider
from app.providers.mock_cloud_provider import MockCloudProvider
from app.repositories.asset_repository import AssetRepository

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class CloudService:
    """云端上传服务。"""

    def __init__(
        self,
        provider: CloudProvider | None = None,
        repository: AssetRepository | None = None,
    ) -> None:
        self._provider = provider or MockCloudProvider()
        self._repository = repository or AssetRepository()

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    def upload_asset(self, asset_id: str) -> AssetRecord:
        """上传单个素材到云端并更新 cloudUrl。"""
        asset = self._find_asset(asset_id)
        file_path = str(BACKEND_ROOT / asset.localPath)

        result = self._provider.upload(file_path, asset.id, asset.assetName)
        asset.cloudUrl = result.cloud_url
        self._repository.update_asset(asset)

        return asset

    def upload_generation(self, generation_id: str) -> list[AssetRecord]:
        """上传整个 generation 的所有素材。"""
        all_assets = self._repository.list_assets()
        gen_assets = [a for a in all_assets if a.generationId == generation_id]

        if not gen_assets:
            raise ValueError(f"未找到 generation：{generation_id}")

        updated: list[AssetRecord] = []
        for asset in gen_assets:
            try:
                updated.append(self.upload_asset(asset.id))
            except Exception:
                pass  # 单个失败不阻塞整体

        return updated

    def _find_asset(self, asset_id: str) -> AssetRecord:
        asset = self._repository.find_asset(asset_id)
        if asset is None:
            raise ValueError(f"未找到素材：{asset_id}")
        return asset
