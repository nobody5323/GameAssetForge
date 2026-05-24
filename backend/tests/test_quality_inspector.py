import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.quality_models import AssetQualityReport, GenerationQualityReport
from app.providers.mock_image_provider import BACKEND_ROOT
from app.repositories.asset_repository import DB_PATH
from app.services.quality_service import QualityService, _read_png_dimensions

GENERATED_ASSETS_DIR = BACKEND_ROOT / "runtime" / "storage" / "generated-assets"


def _clean_runtime_records() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    if GENERATED_ASSETS_DIR.exists():
        shutil.rmtree(GENERATED_ASSETS_DIR)


def _generate_asset(client: TestClient, monkeypatch, asset_type="enemy", asset_name="bamboo_slime") -> dict:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
    _clean_runtime_records()
    resp = client.post(
        "/api/assets/generate",
        json={
            "projectName": "Test Game",
            "gameType": "platformer",
            "style": "pixel_art",
            "theme": "test theme",
            "description": "a test game",
            "targetModel": "mock_seed",
            "promptMode": "normal",
            "assets": [{"type": asset_type, "name": asset_name, "description": "test asset"}],
        },
    )
    assert resp.status_code == 200
    return resp.json()["assets"][0]


# ── unit tests ──────────────────────────────────────────────────────

class TestReadPngDimensions:
    def test_reads_dimensions_from_valid_png(self):
        service = QualityService()
        # use the mock provider to create a real png
        from app.providers.mock_image_provider import MockImageProvider
        from app.models.asset_models import ImageGenerationRequest

        provider = MockImageProvider()
        result = provider.generate(
            ImageGenerationRequest(
                generationId="dim_test",
                assetName="test",
                assetType="character",
                style="pixel_art",
                theme="test",
                finalPrompt="test prompt for dimension check",
            )
        )
        png_path = BACKEND_ROOT / result.localPath
        assert png_path.exists()
        width, height = _read_png_dimensions(png_path)
        assert width == 64
        assert height == 64

    def test_raises_on_non_png_file(self):
        tmp = BACKEND_ROOT / "runtime" / "storage" / "not_a_png.txt"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text("hello world")
        try:
            with pytest.raises(ValueError, match="不是有效的 PNG 文件"):
                _read_png_dimensions(tmp)
        finally:
            tmp.unlink()


class TestQualityService:
    def test_inspect_asset_scores_passing_checks(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "character", "hero")

        service = QualityService()
        report = service.inspect_asset(asset["id"])
        assert isinstance(report, AssetQualityReport)
        assert report.assetId == asset["id"]
        assert report.assetName == "hero"
        assert report.assetType == "character"
        assert len(report.checks) == 7

        # format + dimensions should pass for mock PNG
        fmt = _find_check(report, "file_format")
        assert fmt.passed
        assert fmt.score == 15

        dim = _find_check(report, "image_dimensions")
        assert dim.passed
        assert dim.score == 15

        # naming: "hero" is valid snake_case
        naming = _find_check(report, "naming_convention")
        assert naming.passed
        assert naming.score == 10

        # category dir
        cat = _find_check(report, "category_directory")
        assert cat.passed
        assert cat.score == 15

        # prompt record
        prompt = _find_check(report, "prompt_record")
        assert prompt.passed
        assert prompt.score == 15

        # manifest readiness
        manifest = _find_check(report, "manifest_readiness")
        assert manifest.passed
        assert manifest.score == 15

        # cloud readiness — no cloudUrl yet
        cloud = _find_check(report, "cloud_readiness")
        assert not cloud.passed
        assert cloud.score == 0

        # total: 15+15+10+15+15+15+0 = 85
        assert report.totalScore == 85
        assert report.maxScore == 100

    def test_inspect_generation_returns_aggregated_report(self, monkeypatch):
        client = TestClient(app)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("PROMPT_PROVIDER", "openai")
        _clean_runtime_records()
        resp = client.post(
            "/api/assets/generate",
            json={
                "projectName": "Test Game",
                "gameType": "platformer",
                "style": "pixel_art",
                "theme": "test theme",
                "description": "a test game",
                "targetModel": "mock_seed",
                "promptMode": "normal",
                "assets": [
                    {"type": "character", "name": "hero", "description": "main char"},
                    {"type": "enemy", "name": "slime", "description": "a slime"},
                ],
            },
        )
        assert resp.status_code == 200
        gen_id = resp.json()["generationId"]

        service = QualityService()
        report = service.inspect_generation(gen_id)
        assert isinstance(report, GenerationQualityReport)
        assert report.generationId == gen_id
        assert report.assetCount == 2
        assert len(report.assets) == 2
        assert report.overallScore > 0
        # each asset gets 85/100 → overall 85
        assert report.overallScore == 85
        assert report.passCount == 2
        assert report.failCount == 0

    def test_inspect_generation_not_found_returns_empty(self):
        service = QualityService()
        report = service.inspect_generation("nonexistent_gen")
        assert report.generationId == "nonexistent_gen"
        assert report.assetCount == 0
        assert report.assets == []
        assert report.overallScore == 0


class TestQualityAPI:
    def test_inspect_endpoint_returns_report(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "item", "coin")

        resp = client.post(f"/api/quality/inspect/{asset['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["assetId"] == asset["id"]
        assert len(data["checks"]) == 7
        assert data["totalScore"] == 85

    def test_inspect_endpoint_404_for_unknown_asset(self):
        client = TestClient(app)
        resp = client.post("/api/quality/inspect/nonexistent_asset_id")
        assert resp.status_code == 404
        assert "未找到素材" in resp.json()["detail"]

    def test_report_endpoint_returns_generation_summary(self, monkeypatch):
        client = TestClient(app)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("PROMPT_PROVIDER", "openai")
        _clean_runtime_records()
        resp = client.post(
            "/api/assets/generate",
            json={
                "projectName": "Test Game",
                "gameType": "platformer",
                "style": "pixel_art",
                "theme": "test",
                "description": "test",
                "targetModel": "mock_seed",
                "promptMode": "normal",
                "assets": [
                    {"type": "character", "name": "hero", "description": "main char"},
                ],
            },
        )
        gen_id = resp.json()["generationId"]

        report_resp = client.get(f"/api/quality/report/{gen_id}")
        assert report_resp.status_code == 200
        data = report_resp.json()
        assert data["generationId"] == gen_id
        assert data["assetCount"] == 1
        assert data["passCount"] == 1
        assert data["failCount"] == 0

    def test_report_endpoint_empty_for_unknown_generation(self):
        client = TestClient(app)
        resp = client.get("/api/quality/report/nonexistent_gen")
        assert resp.status_code == 200
        data = resp.json()
        assert data["assetCount"] == 0
        assert data["assets"] == []

    def test_naming_convention_flags_spaces_and_uppercase(self, monkeypatch):
        client = TestClient(app)
        # We need an asset with a bad name — use the API to create one
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("PROMPT_PROVIDER", "openai")
        _clean_runtime_records()
        resp = client.post(
            "/api/assets/generate",
            json={
                "projectName": "Test",
                "gameType": "platformer",
                "style": "pixel_art",
                "theme": "test",
                "description": "test",
                "targetModel": "mock_seed",
                "promptMode": "normal",
                "assets": [{"type": "item", "name": "Bad Name!", "description": "test"}],
            },
        )
        asset = resp.json()["assets"][0]
        # After slugify, the name becomes "bad_name_" — but the record stores original "Bad Name!"
        inspect_resp = client.post(f"/api/quality/inspect/{asset['id']}")
        data = inspect_resp.json()
        naming = _find_check(data, "naming_convention")
        assert not naming["passed"]
        assert naming["score"] < 10

    def test_missing_file_reports_format_failure(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "tileset", "ground_tile")

        # delete the file
        file_path = BACKEND_ROOT / asset["localPath"]
        file_path.unlink()

        service = QualityService()
        report = service.inspect_asset(asset["id"])
        fmt = _find_check(report, "file_format")
        assert not fmt.passed
        assert fmt.score == 0
        assert "不存在" in fmt.message


# ── helpers ─────────────────────────────────────────────────────────

def _find_check(report_or_data, name: str):
    items = report_or_data.checks if hasattr(report_or_data, "checks") else report_or_data["checks"]
    for item in items:
        check_name = item.name if hasattr(item, "name") else item["name"]
        if check_name == name:
            return item
    raise ValueError(f"Check '{name}' not found")
