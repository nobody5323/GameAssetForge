"""导出服务测试。"""

import json
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.models.asset_models import (
    AssetGenerateItem,
    AssetGenerateRequest,
)
from app.repositories.asset_repository import BACKEND_ROOT, AssetRepository
from app.services.asset_generation_service import AssetGenerationService
from app.services.export_service import ExportService


app = create_app()
client = TestClient(app)


def _generate_test_assets() -> str:
    """创建一个测试 generation 并返回 generationId。"""
    service = AssetGenerationService()
    response = service.generate(
        AssetGenerateRequest(
            projectName="test_export_game",
            gameType="platformer",
            style="pixel_art",
            theme="test forest",
            description="a test scene for export",
            targetModel="mock_seed",
            promptMode="normal",
            assets=[
                AssetGenerateItem(
                    type="enemy", name="test_slime", description="a green slime"
                ),
                AssetGenerateItem(
                    type="item", name="test_potion", description="a red potion"
                ),
            ],
        )
    )
    return response.generationId


class TestExportService:
    def test_export_creates_valid_zip(self):
        gen_id = _generate_test_assets()
        service = ExportService()
        export_response, zip_bytes = service.export_generation(gen_id)

        assert export_response.generationId == gen_id
        assert export_response.assetCount == 2
        assert export_response.manifestSize > 0
        assert export_response.totalSize > 0
        assert export_response.zipFileName == f"{gen_id}.zip"

        # 验证 zip 内容
        with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert "manifest.json" in names
            assert "enemy/test_slime.png" in names
            assert "item/test_potion.png" in names

            # 验证 manifest.json 内容
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["generationId"] == gen_id
            assert manifest["assetCount"] == 2
            assert manifest["projectName"] == "test_export_game"
            assert len(manifest["assets"]) == 2

            # 验证第一个素材条目
            asset0 = manifest["assets"][0]
            assert asset0["assetName"] in ("test_slime", "test_potion")
            assert "localPath" in asset0
            assert "finalPrompt" in asset0
            assert "qualityScore" in asset0
            assert "provider" in asset0

            # 验证 PNG 文件存在且可读
            for png_name in ["enemy/test_slime.png", "item/test_potion.png"]:
                png_data = zf.read(png_name)
                assert len(png_data) > 0
                assert png_data[:8] == b"\x89PNG\r\n\x1a\n"

    def test_export_unknown_generation_raises(self):
        service = ExportService()
        try:
            service.export_generation("nonexistent_gen_999")
            raise AssertionError("Expected ValueError")
        except ValueError as exc:
            assert "未找到" in str(exc) or "nonexistent" in str(exc)

    def test_list_exportable_generations(self):
        gen_id = _generate_test_assets()
        service = ExportService()
        generations = service.list_exportable_generations()

        assert gen_id in generations
        assert all(isinstance(g, str) for g in generations)

    def test_export_saves_manifest_and_zip_to_disk(self):
        gen_id = _generate_test_assets()
        service = ExportService()
        export_response, zip_bytes = service.export_generation(gen_id)

        from app.services.export_service import EXPORT_DIR

        zip_path = EXPORT_DIR / f"{gen_id}.zip"
        manifest_path = EXPORT_DIR / f"{gen_id}.manifest.json"

        assert zip_path.exists()
        assert manifest_path.exists()

        # 清理
        zip_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)


class TestExportAPI:
    def test_export_endpoint_returns_zip(self):
        gen_id = _generate_test_assets()
        response = client.post(f"/api/exports/{gen_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert response.headers["x-generation-id"] == gen_id
        assert int(response.headers["x-asset-count"]) == 2

        # 验证返回的是有效 zip
        with zipfile.ZipFile(BytesIO(response.content)) as zf:
            assert "manifest.json" in zf.namelist()

    def test_export_endpoint_404_for_unknown_generation(self):
        response = client.post("/api/exports/nonexistent_gen_999")
        assert response.status_code == 404

    def test_list_generations_endpoint(self):
        gen_id = _generate_test_assets()
        response = client.get("/api/exports")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert gen_id in data

    def test_export_with_zero_assets_returns_empty_manifest(self):
        # 创建一个空 generation（直接写入 repo）
        gen_id = "gen_empty_test_001"
        repo = AssetRepository()
        repo.save_generation(gen_id, [])

        service = ExportService()
        try:
            service.export_generation(gen_id)
            raise AssertionError("Expected ValueError for empty generation")
        except ValueError:
            pass  # 预期行为
