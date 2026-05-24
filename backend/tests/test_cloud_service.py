"""云端上传服务测试。"""

from fastapi.testclient import TestClient

from app.main import create_app
from app.models.asset_models import (
    AssetGenerateItem,
    AssetGenerateRequest,
)
from app.providers.mock_cloud_provider import MockCloudProvider
from app.services.asset_generation_service import AssetGenerationService
from app.services.cloud_service import CloudService


app = create_app()
client = TestClient(app)

# Reset cloud config to mock so these tests run with MockCloudProvider
client.put(
    "/api/config/cloud",
    json={"provider": "mock", "clearCredentials": True},
)


def _generate_test_assets() -> str:
    """创建一个测试 generation 并返回 generationId。"""
    service = AssetGenerationService()
    response = service.generate(
        AssetGenerateRequest(
            projectName="test_cloud_game",
            gameType="platformer",
            style="pixel_art",
            theme="test forest",
            description="test for cloud upload",
            targetModel="mock_seed",
            promptMode="normal",
            assets=[
                AssetGenerateItem(
                    type="enemy", name="cloud_slime", description="a green slime"
                ),
            ],
        )
    )
    return response.generationId


class TestCloudService:
    def test_upload_sets_cloud_url(self):
        gen_id = _generate_test_assets()
        service = CloudService()
        # 取第一个素材
        from app.repositories.asset_repository import AssetRepository
        repo = AssetRepository()
        assets = [a for a in repo.list_assets() if a.generationId == gen_id]
        assert len(assets) == 1

        asset = assets[0]
        assert asset.cloudUrl is None

        updated = service.upload_asset(asset.id)
        assert updated.cloudUrl is not None
        assert updated.cloudUrl.startswith("cloud://mock/")

    def test_upload_generation_uploads_all(self):
        gen_id = _generate_test_assets()
        service = CloudService()
        updated = service.upload_generation(gen_id)

        assert len(updated) >= 1
        for asset in updated:
            assert asset.cloudUrl is not None
            assert asset.cloudUrl.startswith("cloud://mock/")

    def test_upload_unknown_asset_raises(self):
        service = CloudService()
        try:
            service.upload_asset("nonexistent_asset_999")
            raise AssertionError("Expected ValueError")
        except ValueError:
            pass

    def test_upload_unknown_generation_raises(self):
        service = CloudService()
        try:
            service.upload_generation("nonexistent_gen_999")
            raise AssertionError("Expected ValueError")
        except ValueError:
            pass


class TestCloudAPI:
    def test_upload_asset_endpoint(self):
        gen_id = _generate_test_assets()
        from app.repositories.asset_repository import AssetRepository
        repo = AssetRepository()
        assets = [a for a in repo.list_assets() if a.generationId == gen_id]
        asset_id = assets[0].id

        response = client.post(f"/api/cloud/upload/{asset_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["cloudUrl"] is not None
        assert data["cloudUrl"].startswith("cloud://mock/")

    def test_upload_generation_endpoint(self):
        gen_id = _generate_test_assets()
        response = client.post(f"/api/cloud/upload-generation/{gen_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(item["cloudUrl"] is not None for item in data)

    def test_upload_asset_404(self):
        response = client.post("/api/cloud/upload/nonexistent_999")
        assert response.status_code == 404
