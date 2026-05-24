from fastapi.testclient import TestClient

from app.main import app
from app.models.prompt_models import PromptAssetResult, PromptCompileRequest
from app.prompt.prompt_scorer import PromptScorer
from app.prompt.tag_extractor import extract_prompt_tags


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
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
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
    assert data["candidates"][0]["direction"] == "quick_start"
    assert data["candidates"][0]["score"] >= 60
    assert "Create a simple 2D game asset concept" in data["candidates"][0]["assets"][0]["finalPrompt"]
    assert "Direction profile:" not in data["candidates"][0]["assets"][0]["finalPrompt"]


def test_professional_mode_returns_three_candidates_with_threshold(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
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
    scores = [candidate["score"] for candidate in data["candidates"]]
    assert all(score >= 80 for score in scores)
    assert len(set(scores)) > 1
    assert max(scores) < 100


def test_mock_seed_prompt_uses_local_provider_profile(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
    client = TestClient(app)
    payload = {**BASE_REQUEST, "targetModel": "mock_seed"}

    response = client.post("/api/prompts/compile", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["targetModel"] == "mock_seed"
    assert data["provider"] == "rule_fallback"
    assert data["fallback"] is True
    prompt = data["candidates"][0]["assets"][0]["finalPrompt"]
    assert "Mock Seed Prompt Profile" in prompt
    assert "External model call: disabled" in prompt
    assert "Seed selection:" in prompt
    assert "Copy target:" in prompt
    assert "Metadata to attach:" in prompt
    assert "provider=mock" in prompt
    assert "return the localPath" in prompt


def test_tag_extractor_adds_english_tags_from_chinese_input():
    request = PromptCompileRequest(**BASE_REQUEST)

    tags = extract_prompt_tags(request)

    assert "pixel art" in tags["style"]
    assert "bamboo forest" in tags["theme"]
    assert "cyberpunk" in tags["theme"]
    assert "monster" in tags["subject"]


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


def test_scorer_penalizes_overcomplex_showcase_prompts():
    scorer = PromptScorer()
    tags = {
        "technical": [
            "centered composition",
            "clear silhouette",
            "readable at small size",
            "simple background",
            "game-ready asset",
        ],
        "negative": ["no text", "no watermark", "no blurry edges", "no cropped subject"],
        "theme": ["cyber bamboo forest"],
        "subject": ["enemy sprite", "bamboo slime"],
    }
    production_prompt = PromptAssetResult(
        assetName="bamboo_slime",
        assetType="enemy",
        finalPrompt=(
            "Create a production-ready 2D game asset.\n"
            "Subject: bamboo slime enemy sprite.\n"
            "Direction profile: production_safe.\n"
            "Style tags: pixel art, limited palette, crisp edges.\n"
            "Theme tags: cyber bamboo forest.\n"
            "Technical requirements: centered composition, clear silhouette, readable at small size, simple background, game-ready asset.\n"
            "Avoid: no text, no watermark, no blurry edges, no cropped subject."
        ),
    )
    showcase_prompt = PromptAssetResult(
        assetName="bamboo_slime",
        assetType="enemy",
        finalPrompt=(
            "Create a production-ready 2D game asset.\n"
            "Subject: bamboo slime enemy sprite.\n"
            "Direction profile: high_detail.\n"
            "Style tags: pixel art, limited palette, crisp edges.\n"
            "Theme tags: cyber bamboo forest.\n"
            "Technical requirements: centered composition, clear silhouette, readable at small size, simple background, game-ready asset.\n"
            "Add ornate surface texture, cinematic scene, complex background, many tiny details.\n"
            "Avoid: no text, no watermark, no blurry edges, no cropped subject."
        ),
    )

    assert scorer.score(
        target_model="gpt_image",
        asset_type="enemy",
        prompt=production_prompt,
        tags=tags,
    ) > scorer.score(
        target_model="gpt_image",
        asset_type="enemy",
        prompt=showcase_prompt,
        tags=tags,
    )


def test_normal_mode_is_less_strict_than_professional(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PROMPT_PROVIDER", "openai")
    client = TestClient(app)

    normal = client.post("/api/prompts/compile", json=BASE_REQUEST).json()["candidates"][0]
    professional = client.post(
        "/api/prompts/compile",
        json={**BASE_REQUEST, "mode": "professional"},
    ).json()["candidates"][0]

    assert normal["direction"] == "quick_start"
    assert professional["direction"] == "production_safe"
    assert normal["score"] < professional["score"]
    assert len(normal["assets"][0]["finalPrompt"]) < len(professional["assets"][0]["finalPrompt"])
