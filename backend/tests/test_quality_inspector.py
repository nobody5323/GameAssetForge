import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.quality_models import AssetQualityReport, GenerationQualityReport
from app.providers.mock_image_provider import BACKEND_ROOT
from app.repositories.asset_repository import DB_PATH
from app.services.quality_service import (
    QualityService,
    _is_power_of_two,
    _is_solid_color_png,
    _read_png_dimensions,
)

GENERATED_ASSETS_DIR = BACKEND_ROOT / "runtime" / "storage" / "generated-assets"


def _clean_runtime_records() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    if GENERATED_ASSETS_DIR.exists():
        shutil.rmtree(GENERATED_ASSETS_DIR)


def _generate_asset(
    client: TestClient,
    monkeypatch,
    asset_type="enemy",
    asset_name="bamboo_slime",
) -> dict:
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


class TestPngHelpers:
    def test_reads_512x512_from_mock_png(self):
        from app.models.asset_models import ImageGenerationRequest
        from app.providers.mock_image_provider import MockImageProvider

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
        width, height = _read_png_dimensions(png_path)
        assert (width, height) == (512, 512)

    def test_raises_on_non_png_file(self):
        tmp = BACKEND_ROOT / "runtime" / "storage" / "not_a_png.txt"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text("hello world")
        try:
            with pytest.raises(ValueError, match="PNG"):
                _read_png_dimensions(tmp)
        finally:
            tmp.unlink()

    def test_power_of_two_values(self):
        assert _is_power_of_two(64) is True
        assert _is_power_of_two(256) is True
        assert _is_power_of_two(300) is False
        assert _is_power_of_two(0) is False

    def test_mock_png_is_solid_color(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "character", "hero")
        assert _is_solid_color_png(BACKEND_ROOT / asset["localPath"]) is True


class TestWeightedQualityScoring:
    def test_mock_asset_has_weighted_dimensions_and_tips(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "character", "hero")

        report = QualityService().inspect_asset(asset["id"])

        assert isinstance(report, AssetQualityReport)
        assert report.maxScore == 100
        assert report.totalScore < 100
        assert report.qualityGrade in {"A", "B", "C", "D", "F"}
        assert len(report.checks) == 6
        assert sum(check.weight for check in report.checks) == 100
        assert all(0 <= check.score <= 100 for check in report.checks)
        assert all(0 <= check.weightedScore <= check.weight for check in report.checks)
        assert report.promptOptimizationTips
        important = {"dimensions", "category_fit", "clarity", "prompt_alignment", "visual_quality"}
        for check in report.checks:
            if check.name in important:
                assert len(check.criteria) >= 6
            else:
                assert len(check.criteria) >= 3
            assert all(criterion.label for criterion in check.criteria)

    def test_perfect_asset_scores_high(self):
        from app.models.asset_models import AssetRecord
        from app.repositories.asset_repository import AssetRepository

        _clean_runtime_records()
        perfect = AssetRecord(
            id="asset_perfect_001",
            generationId="gen_perfect",
            assetName="hero_knight",
            assetType="character",
            style="pixel_art",
            theme="fantasy",
            finalPrompt=(
                "A pixel art hero_knight character sprite for a fantasy 2D platformer game. "
                "The character wears silver armor with a blue cape. "
                "Style: 16-bit retro pixel art with clean outlines and flat shading. "
                "Composition: side-view idle pose, 256x256 canvas, transparent background."
            ),
            promptVersion="prompt-v2",
            localPath="runtime/storage/generated-assets/gen_perfect/character/hero_knight.png",
            cloudUrl="https://cdn.example.com/assets/hero_knight.png",
            qualityScore=None,
            provider="openai",
            providerMetadata={"model": "dall-e-3", "mock": False},
        )
        png_path = BACKEND_ROOT / perfect.localPath
        _write_checker_png(png_path, width=256, height=256)

        try:
            repo = AssetRepository()
            repo.save_generation(perfect.generationId, [perfect])
            report = QualityService(repository=repo).inspect_asset(perfect.id)
            assert report.totalScore >= 95
            assert report.qualityGrade in {"S", "A"}
        finally:
            if png_path.exists():
                png_path.unlink()
            if DB_PATH.exists():
                DB_PATH.unlink()

    def test_bad_name_lowers_category_fit_dimension(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "item", "Bad Coin!")

        report = QualityService().inspect_asset(asset["id"])
        category = _find_check(report, "category_fit")

        assert not category.passed
        assert category.score < 100
        assert any("snake_case" in tip for tip in category.suggestions)


class TestGenerationReport:
    def test_aggregates_multiple_assets_with_differentiated_scores(self, monkeypatch):
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
                    {"type": "enemy", "name": "Bad Slime!", "description": "bad name"},
                ],
            },
        )
        gen_id = resp.json()["generationId"]

        report = QualityService().inspect_generation(gen_id)

        assert isinstance(report, GenerationQualityReport)
        assert report.generationId == gen_id
        assert report.assetCount == 2
        assert len(report.assets) == 2
        assert report.assets[0].totalScore != report.assets[1].totalScore

    def test_empty_generation_returns_zero(self):
        report = QualityService().inspect_generation("nonexistent_gen")
        assert report.generationId == "nonexistent_gen"
        assert report.assetCount == 0
        assert report.assets == []
        assert report.overallScore == 0


class TestFatalFormatCheck:
    def test_non_png_file_scores_zero(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "tileset", "ground_tile")
        (BACKEND_ROOT / asset["localPath"]).write_bytes(b"not a png file")

        report = QualityService().inspect_asset(asset["id"])

        assert report.totalScore == 0
        assert len(report.checks) == 1
        assert report.checks[0].name == "format"
        assert report.checks[0].score == 0

    def test_missing_file_scores_zero(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "ui", "button")
        (BACKEND_ROOT / asset["localPath"]).unlink()

        report = QualityService().inspect_asset(asset["id"])

        assert report.totalScore == 0
        assert report.checks[0].name == "format"
        assert "不存在" in report.checks[0].message


class TestQualityAPI:
    def test_inspect_endpoint_returns_weighted_report(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "item", "coin")

        resp = client.post(f"/api/quality/inspect/{asset['id']}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["assetId"] == asset["id"]
        assert data["maxScore"] == 100
        assert 0 <= data["totalScore"] <= 100
        assert data["qualityGrade"]
        assert "promptOptimizationTips" in data
        assert all("weight" in check and "weightedScore" in check for check in data["checks"])
        assert all("criteria" in check and check["criteria"] for check in data["checks"])

    def test_inspect_404_for_unknown_asset(self):
        client = TestClient(app)
        resp = client.post("/api/quality/inspect/nonexistent_asset_id")
        assert resp.status_code == 404

    def test_report_endpoint_returns_summary(self, monkeypatch):
        client = TestClient(app)
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
                "assets": [{"type": "character", "name": "hero", "description": "main char"}],
            },
        )
        gen_id = resp.json()["generationId"]

        report_resp = client.get(f"/api/quality/report/{gen_id}")

        assert report_resp.status_code == 200
        data = report_resp.json()
        assert data["generationId"] == gen_id
        assert data["assetCount"] == 1
        assert data["maxScore"] == 100


def _find_check(report_or_data, name: str):
    items = report_or_data.checks if hasattr(report_or_data, "checks") else report_or_data["checks"]
    for item in items:
        check_name = item.name if hasattr(item, "name") else item["name"]
        if check_name == name:
            return item
    raise ValueError(f"Check '{name}' not found")


def _write_checker_png(path: Path, width: int, height: int) -> None:
    import struct as _struct
    import zlib as _zlib

    sig = b"\x89PNG\r\n\x1a\n"
    color_a = (41, 173, 255)
    color_b = (255, 119, 168)
    raw_rows = []
    for y in range(height):
        row_data = b""
        for x in range(width):
            row_data += bytes(color_a if (x + y) % 2 == 0 else color_b)
        raw_rows.append(b"\x00" + row_data)

    def _chunk(t: bytes, d: bytes) -> bytes:
        crc = _zlib.crc32(t + d) & 0xFFFFFFFF
        return _struct.pack(">I", len(d)) + t + d + _struct.pack(">I", crc)

    png = b"".join([
        sig,
        _chunk(b"IHDR", _struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
        _chunk(b"IDAT", _zlib.compress(b"".join(raw_rows))),
        _chunk(b"IEND", b""),
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
