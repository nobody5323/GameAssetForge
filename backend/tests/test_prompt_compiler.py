from fastapi.testclient import TestClient

from app.main import app
from app.models.prompt_models import PromptAssetResult
from app.prompt.prompt_scorer import PromptScorer
from app.prompt.tag_extractor import extract_prompt_tags
from app.models.prompt_models import PromptCompileRequest


BASE_REQUEST = {
    "mode": "normal",
    "targetModel": "gpt_image",
    "projectName": "Cyber Bamboo Platformer",
    "gameType": "platformer",
    "style": "pixel_art",
    "theme": "cyber bamboo forest",
    "description": "赛博竹林主题 2D 横版闯关游戏，需要主角、敌人、金币和地砖素材。",
    "assets": [
        {
            "type": "enemy",
            "name": "bamboo_slime",
            "description": "a small glowing slime monster",
        }
    ],
}


def test_normal_mode_returns_one_gpt_image_candidate_with_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(app)

    response = client.post("/api/prompts/compile", json=BASE_REQUEST)

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "normal"
    assert data["targetModel"] == "gpt_image"
    assert data["provider"] == "rule_fallback"
    assert data["fallback"] is True
    assert data["threshold"] == 60
    assert len(data["candidates"]) == 1
    assert data["candidates"][0]["score"] >= 60
    assert "Create a production-ready 2D game asset" in data["candidates"][0]["assets"][0]["finalPrompt"]


def test_professional_mode_returns_three_candidates_with_threshold(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(app)
    payload = {**BASE_REQUEST, "mode": "professional"}

    response = client.post("/api/prompts/compile", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["threshold"] == 80
    assert [candidate["direction"] for candidate in data["candidates"]] == [
        "production_safe",
        "style_exploration",
        "high_detail",
    ]
    assert len(data["candidates"]) == 3
    assert all(candidate["score"] >= 80 for candidate in data["candidates"])


def test_novelai_prompt_uses_tag_oriented_structure(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(app)
    payload = {**BASE_REQUEST, "targetModel": "novelai"}

    response = client.post("/api/prompts/compile", json=payload)

    assert response.status_code == 200
    asset = response.json()["candidates"][0]["assets"][0]
    assert ", " in asset["finalPrompt"]
    assert "game asset" in asset["finalPrompt"]
    assert asset["negativePrompt"]
    assert "low quality" in asset["negativePrompt"]


def test_tag_extractor_adds_english_tags_from_chinese_input():
    request = PromptCompileRequest(**BASE_REQUEST)

    tags = extract_prompt_tags(request)

    assert "pixel art" in tags["style"]
    assert "bamboo forest" in tags["theme"]
    assert "cyberpunk" in tags["theme"]
    assert "enemy sprite" in tags["subject"]


def test_low_score_prompt_includes_warning():
    scorer = PromptScorer()
    prompt = PromptAssetResult(
        assetName="coin",
        assetType="item",
        finalPrompt="coin",
    )
    score = scorer.score(
        target_model="gpt_image",
        asset_type="item",
        prompt=prompt,
        tags={
            "technical": ["centered composition"],
            "negative": ["no text"],
        },
    )

    assert score < 60
