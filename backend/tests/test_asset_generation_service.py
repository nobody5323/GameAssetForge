import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.providers.mock_image_provider import BACKEND_ROOT
from app.repositories.asset_repository import DB_PATH


GENERATED_ASSETS_DIR = BACKEND_ROOT / "runtime" / "storage" / "generated-assets"


def _clean_runtime_records() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    if GENERATED_ASSETS_DIR.exists():
        shutil.rmtree(GENERATED_ASSETS_DIR)


def test_generate_assets_creates_mock_files_and_repository_records(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
    _clean_runtime_records()
    client = TestClient(app)

    response = client.post(
        "/api/assets/generate",
        json={
            "projectName": "Cyber Bamboo Platformer",
            "gameType": "platformer",
            "style": "pixel_art",
            "theme": "cyber bamboo forest",
            "description": "赛博竹林主题 2D 横版闯关游戏，需要主角、敌人、金币和地砖素材。",
            "targetModel": "mock_seed",
            "promptMode": "normal",
            "assets": [
                {
                    "type": "enemy",
                    "name": "bamboo_slime",
                    "description": "a small glowing slime monster",
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["generationId"].startswith("gen_")
    assert data["provider"] == "mock"
    assert data["promptProvider"] == "rule_fallback"
    assert data["fallback"] is True
    assert len(data["assets"]) == 1

    asset = data["assets"][0]
    assert asset["id"].startswith("asset_")
    assert asset["generationId"] == data["generationId"]
    assert asset["assetName"] == "bamboo_slime"
    assert asset["assetType"] == "enemy"
    assert asset["provider"] == "mock"
    assert asset["providerMetadata"]["mock"] is True
    assert asset["providerMetadata"]["promptHash"]
    assert "Mock Seed Prompt Profile" in asset["finalPrompt"]
    assert (BACKEND_ROOT / asset["localPath"]).exists()

    static_response = client.get(f"/{asset['localPath']}")
    assert static_response.status_code == 200
    assert static_response.headers["content-type"] == "image/png"
    assert static_response.content.startswith(b"\x89PNG\r\n\x1a\n")

    repository_data = DB_PATH.read_text(encoding="utf-8")
    assert data["generationId"] in repository_data
    assert asset["id"] in repository_data


def test_list_assets_returns_all_assets(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
    _clean_runtime_records()
    client = TestClient(app)

    # Generate two different asset types first
    client.post(
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
                {"type": "character", "name": "hero", "description": "main character"},
                {"type": "enemy", "name": "slime", "description": "a slime"},
            ],
        },
    )

    # GET all assets (no filter)
    response = client.get("/api/assets")
    assert response.status_code == 200
    assets = response.json()
    assert len(assets) == 2
    asset_types = {a["assetType"] for a in assets}
    assert asset_types == {"character", "enemy"}


def test_list_assets_filters_by_category(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
    _clean_runtime_records()
    client = TestClient(app)

    client.post(
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
                {"type": "character", "name": "hero", "description": "main character"},
                {"type": "enemy", "name": "slime", "description": "a slime"},
                {"type": "item", "name": "coin", "description": "a coin"},
            ],
        },
    )

    response = client.get("/api/assets?category=character")
    assert response.status_code == 200
    assets = response.json()
    assert len(assets) == 1
    assert assets[0]["assetType"] == "character"
    assert assets[0]["assetName"] == "hero"


def test_list_assets_empty_category_returns_empty_list(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
    _clean_runtime_records()
    client = TestClient(app)

    client.post(
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
                {"type": "character", "name": "hero", "description": "main character"},
            ],
        },
    )

    response = client.get("/api/assets?category=tileset")
    assert response.status_code == 200
    assets = response.json()
    assert assets == []


def test_list_assets_includes_all_fields(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
    _clean_runtime_records()
    client = TestClient(app)

    client.post(
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
                {"type": "item", "name": "coin", "description": "a coin"},
            ],
        },
    )

    response = client.get("/api/assets")
    assert response.status_code == 200
    assets = response.json()
    assert len(assets) == 1
    asset = assets[0]
    assert "id" in asset
    assert "generationId" in asset
    assert "assetName" in asset
    assert "assetType" in asset
    assert "style" in asset
    assert "theme" in asset
    assert "finalPrompt" in asset
    assert "promptVersion" in asset
    assert "localPath" in asset
    assert "provider" in asset
    assert "providerMetadata" in asset


def test_regenerate_falls_back_to_mock_when_gpt_image_disconnects(monkeypatch):
    from app.models.asset_models import AssetRecord
    from app.services.asset_generation_service import AssetGenerationService

    _clean_runtime_records()
    service = AssetGenerationService()
    monkeypatch.setattr(service.gpt_provider, "is_available", lambda: True)

    def _disconnect(_request):
        raise RuntimeError(
            "Image API (Chat Completions) network error — 服务器连接断开（已重试 1 次）"
        )

    monkeypatch.setattr(service.gpt_provider, "generate", _disconnect)
    original = AssetRecord(
        id="asset_original_asuna",
        generationId="gen_original",
        projectName="Test Game",
        assetName="asuna",
        assetType="character",
        style="pixel_art",
        theme="fantasy",
        finalPrompt="asuna character sprite",
        promptVersion="prompt-v1",
        localPath="runtime/storage/generated-assets/gen_original/character/asuna.png",
        provider="gpt_image",
        providerMetadata={"model": "gpt-image-2", "mock": False},
    )

    result = service.regenerate_asset(original, "skill_release")

    assert result.assetName == "asuna_skill_release"
    assert result.provider == "mock"
    assert result.parentAssetId == original.id
    assert result.providerMetadata["fallbackFrom"] == "gpt_image"
    assert "服务器连接断开" in result.providerMetadata["fallbackReason"]
    assert (BACKEND_ROOT / result.localPath).exists()
