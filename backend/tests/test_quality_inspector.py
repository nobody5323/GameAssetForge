import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.quality_models import AssetQualityReport, GenerationQualityReport
from app.providers.mock_image_provider import BACKEND_ROOT
from app.repositories.asset_repository import DB_PATH
from app.services.quality_service import QualityService, _is_power_of_two, _is_solid_color_png, _read_png_dimensions

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


# ── 单元测试：PNG 工具函数 ──────────────────────────────────────────

class TestReadPngDimensions:
    def test_reads_512x512_from_mock_png(self):
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
        assert width == 512
        assert height == 512

    def test_raises_on_non_png_file(self):
        tmp = BACKEND_ROOT / "runtime" / "storage" / "not_a_png.txt"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text("hello world")
        try:
            with pytest.raises(ValueError, match="不是有效的 PNG 文件"):
                _read_png_dimensions(tmp)
        finally:
            tmp.unlink()


class TestPowerOfTwo:
    def test_power_of_two_values(self):
        assert _is_power_of_two(64) is True
        assert _is_power_of_two(128) is True
        assert _is_power_of_two(256) is True
        assert _is_power_of_two(512) is True
        assert _is_power_of_two(1024) is True

    def test_non_power_of_two_values(self):
        assert _is_power_of_two(100) is False
        assert _is_power_of_two(200) is False
        assert _is_power_of_two(300) is False
        assert _is_power_of_two(0) is False
        assert _is_power_of_two(3) is False


class TestSolidColorDetection:
    def test_mock_png_is_solid_color(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "character", "hero")
        png_path = BACKEND_ROOT / asset["localPath"]
        assert png_path.exists()
        assert _is_solid_color_png(png_path) is True


# ── 扣分制核心测试 ─────────────────────────────────────────────────

class TestDeductionScoring:
    """验证扣分制：满分 100，逐项扣分。"""

    def test_mock_asset_scores_around_70(self, monkeypatch):
        """Mock 素材（512x512 纯色）应因纯色+mock provider 被扣分，但尺寸达标。"""
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "character", "hero")

        service = QualityService()
        report = service.inspect_asset(asset["id"])
        assert isinstance(report, AssetQualityReport)
        assert report.maxScore == 100

        # mock 512x512 纯色: 尺寸达标 0 + 纯色扣 15 + mock provider 扣 10 + cloudUrl 扣 15
        # 预期: 100 - (15+10+15) ≈ 60 → 约 50-75 之间
        assert 50 <= report.totalScore <= 75, (
            f"预期 mock 素材得分在 50-75 之间，体现纯色+mock 的扣分，实际得分 {report.totalScore}"
        )

    def test_perfect_asset_scores_high(self, monkeypatch):
        """理论上接近完美的素材（256x256、正确命名、cloudUrl 设置、真实 provider）应得高分。"""
        from app.models.asset_models import AssetRecord

        perfect = AssetRecord(
            id="asset_perfect_001",
            generationId="gen_perfect",
            assetName="hero_knight",
            assetType="character",
            style="pixel_art",
            theme="fantasy",
            finalPrompt=(
                "A pixel art hero_knight sprite for a 2D platformer game. "
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
        png_path.parent.mkdir(parents=True, exist_ok=True)
        # 每像素交替的棋盘格（非纯色），256x256 非 mock
        _write_checker_png(png_path, width=256, height=256)

        try:
            from app.repositories.asset_repository import AssetRepository
            repo = AssetRepository()
            repo.save_generation(perfect.generationId, [perfect])

            service = QualityService(repository=repo)
            report = service.inspect_asset(perfect.id)

            # 256x256 非纯色 + cloudUrl + openai provider + 正确命名 = 应 ≥ 95
            assert report.totalScore >= 95, (
                f"预期接近完美的素材得分 ≥ 95，实际 {report.totalScore}。"
                f"检查详情：{[(c.name, c.score, c.message[:80]) for c in report.checks]}"
            )
        finally:
            if png_path.exists():
                png_path.unlink()
            if DB_PATH.exists():
                DB_PATH.unlink()

    def test_bad_naming_asset_scores_lower(self, monkeypatch):
        """命名不规范（空格+大写+特殊字符）的素材应得分更低。"""
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "item", "Bad Coin!")
        # slugify 会处理路径，但 assetName 保留原始值

        service = QualityService()
        report = service.inspect_asset(asset["id"])

        naming = _find_check(report, "naming")
        assert not naming.passed
        assert naming.score > 0, f"命名不规范应扣分，实际扣 {naming.score}"


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
        assert resp.status_code == 200
        gen_id = resp.json()["generationId"]

        service = QualityService()
        report = service.inspect_generation(gen_id)
        assert isinstance(report, GenerationQualityReport)
        assert report.generationId == gen_id
        assert report.assetCount == 2
        assert len(report.assets) == 2

        # 两个素材得分应不同（命名不同导致扣分不同）
        scores = [r.totalScore for r in report.assets]
        assert scores[0] != scores[1], (
            f"预期两个素材得分应有差异，实际得分：{scores}"
        )

    def test_empty_generation_returns_zero(self):
        service = QualityService()
        report = service.inspect_generation("nonexistent_gen")
        assert report.generationId == "nonexistent_gen"
        assert report.assetCount == 0
        assert report.assets == []
        assert report.overallScore == 0


class TestFatalCheck:
    def test_non_png_file_scores_zero(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "tileset", "ground_tile")

        # 破坏 PNG：覆盖为非 PNG 内容
        file_path = BACKEND_ROOT / asset["localPath"]
        file_path.write_bytes(b"not a png file")

        service = QualityService()
        report = service.inspect_asset(asset["id"])
        assert report.totalScore == 0
        assert len(report.checks) == 1
        assert report.checks[0].name == "png_fatal"

    def test_missing_file_scores_zero(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "ui", "button")

        file_path = BACKEND_ROOT / asset["localPath"]
        file_path.unlink()

        service = QualityService()
        report = service.inspect_asset(asset["id"])
        assert report.totalScore == 0
        assert report.checks[0].name == "png_fatal"
        assert "不存在" in report.checks[0].message


class TestQualityAPI:
    def test_inspect_endpoint_returns_deduction_based_report(self, monkeypatch):
        client = TestClient(app)
        asset = _generate_asset(client, monkeypatch, "item", "coin")

        resp = client.post(f"/api/quality/inspect/{asset['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["assetId"] == asset["id"]
        assert data["maxScore"] == 100
        assert 0 <= data["totalScore"] <= 100
        # mock 素材不应该满分
        assert data["totalScore"] < 100, "mock 素材不应得满分"

    def test_inspect_404_for_unknown_asset(self):
        client = TestClient(app)
        resp = client.post("/api/quality/inspect/nonexistent_asset_id")
        assert resp.status_code == 404

    def test_report_endpoint_returns_summary(self, monkeypatch):
        client = TestClient(app)
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
        assert data["maxScore"] == 100


# ── helpers ─────────────────────────────────────────────────────────

def _find_check(report_or_data, name: str):
    items = report_or_data.checks if hasattr(report_or_data, "checks") else report_or_data["checks"]
    for item in items:
        check_name = item.name if hasattr(item, "name") else item["name"]
        if check_name == name:
            return item
    raise ValueError(f"Check '{name}' not found")


def _write_checker_png(path: Path, width: int, height: int) -> None:
    """写入一个每像素交替的棋盘格 PNG（非纯色），模拟真实生成素材。"""
    import struct as _struct
    import zlib as _zlib

    sig = b"\x89PNG\r\n\x1a\n"
    color_a = (41, 173, 255)
    color_b = (255, 119, 168)

    raw_rows = []
    for y in range(height):
        row_data = b""
        for x in range(width):
            c = color_a if (x + y) % 2 == 0 else color_b
            row_data += bytes(c)
        raw_rows.append(b"\x00" + row_data)

    payload = b"".join(raw_rows)

    def _chunk(t: bytes, d: bytes) -> bytes:
        crc = _zlib.crc32(t + d) & 0xFFFFFFFF
        return _struct.pack(">I", len(d)) + t + d + _struct.pack(">I", crc)

    png = b"".join([
        sig,
        _chunk(b"IHDR", _struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
        _chunk(b"IDAT", _zlib.compress(payload)),
        _chunk(b"IEND", b""),
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
