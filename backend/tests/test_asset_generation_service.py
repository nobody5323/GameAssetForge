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
