import base64
import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from app.models.asset_models import ImageGenerationRequest
from app.providers.gpt_image_provider import GptImageProvider

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# A tiny valid 1x1 red PNG encoded in base64
DUMMY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/P"
    "wIhoQAAAABJRU5ErkJggg=="
)

DUMMY_API_RESPONSE = {
    "data": [
        {
            "b64_json": DUMMY_PNG_BASE64,
            "revised_prompt": "A revised prompt for a game asset.",
        }
    ]
}

DUMMY_CHAT_RESPONSE = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": None,
                "annotations": [
                    {
                        "type": "image",
                        "image": {
                            "b64_json": DUMMY_PNG_BASE64,
                        },
                    }
                ],
            }
        }
    ]
}


def _mock_dalle_post(*args, **kwargs):
    """Return a mocked httpx.Response for DALL-E Images API."""

    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        @property
        def is_success(self):
            return True

        def json(self):
            return DUMMY_API_RESPONSE

        @property
        def text(self):
            return json.dumps(DUMMY_API_RESPONSE)

    return MockResponse()


def _mock_chat_post(*args, **kwargs):
    """Return a mocked httpx.Response for gpt-image-2 Chat Completions API."""

    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        @property
        def is_success(self):
            return True

        def json(self):
            return DUMMY_CHAT_RESPONSE

        @property
        def text(self):
            return json.dumps(DUMMY_CHAT_RESPONSE)

    return MockResponse()


def _mock_error_post(*args, **kwargs):
    """Return an error httpx.Response to simulate API failure."""

    class MockResponse:
        status_code = 500

        def raise_for_status(self):
            raise httpx.HTTPStatusError(
                "Server error", request=args[0] if args else None, response=self
            )

        @property
        def is_success(self):
            return False

        def json(self):
            return {"error": "internal error"}

        @property
        def text(self):
            # Use ensure_ascii=False so Chinese text is readable (matches real API behavior)
            return json.dumps(
                {"error": "没有按照预期生成图片，请重新调整提示词后重试"},
                ensure_ascii=False,
            )

    return MockResponse()


@pytest.fixture(autouse=True)
def _patch_config(monkeypatch):
    """Ensure GptImageProvider reports as available during tests."""
    monkeypatch.setattr(
        "app.providers.gpt_image_provider.image_runtime_config.api_key",
        "sk-test-key",
    )
    monkeypatch.setattr(
        "app.providers.gpt_image_provider.image_runtime_config.image_model",
        "dall-e-3",
    )
    monkeypatch.setattr(
        "app.providers.gpt_image_provider.image_runtime_config.image_size",
        "1024x1024",
    )
    monkeypatch.setattr(
        "app.providers.gpt_image_provider.image_runtime_config.image_quality",
        "standard",
    )
    monkeypatch.setattr(
        "app.providers.gpt_image_provider.image_runtime_config.base_url",
        "https://api.openai.com/v1",
    )


# ── Availability ──


def test_gpt_provider_is_available_with_key():
    provider = GptImageProvider()
    assert provider.is_available() is True


def test_gpt_provider_not_available_without_key(monkeypatch):
    monkeypatch.setattr(
        "app.providers.gpt_image_provider.image_runtime_config.api_key",
        "",
    )
    provider = GptImageProvider()
    assert provider.is_available() is False


# ── DALL-E (Images API) ──


def test_dalle_generates_image():
    provider = GptImageProvider()

    with patch.object(httpx.Client, "post", side_effect=_mock_dalle_post):
        result = provider.generate(
            ImageGenerationRequest(
                generationId="gen-dalle-001",
                assetName="slime",
                assetType="enemy",
                style="pixel_art",
                theme="cyber forest",
                finalPrompt="A cute pixel-art green slime enemy.",
            )
        )

    assert result.provider == "gpt_image"
    assert result.assetName == "slime"
    assert result.assetType == "enemy"
    assert result.metadata["model"] == "dall-e-3"
    assert result.metadata["mock"] is False
    assert result.metadata["revisedPrompt"] == "A revised prompt for a game asset."
    assert result.metadata["promptHash"]

    # Verify the image file was saved
    generated_path = Path(result.localPath)
    assert generated_path.exists()
    png_bytes = generated_path.read_bytes()
    assert png_bytes.startswith(PNG_SIGNATURE)
    assert base64.b64decode(DUMMY_PNG_BASE64) == png_bytes


def test_dalle_error_without_key():
    """Without an API key, generate() should raise RuntimeError."""
    with patch.object(
        GptImageProvider,
        "is_available",
        return_value=False,
    ):
        provider = GptImageProvider()
        with pytest.raises(RuntimeError, match="API key is not configured"):
            provider.generate(
                ImageGenerationRequest(
                    generationId="gen-err",
                    assetName="test",
                    assetType="item",
                    style="cartoon",
                    theme="test",
                    finalPrompt="test",
                )
            )


def test_dalle_path_sanitized():
    """Asset names with special characters should be sanitized."""
    provider = GptImageProvider()

    with patch.object(httpx.Client, "post", side_effect=_mock_dalle_post):
        result = provider.generate(
            ImageGenerationRequest(
                generationId="gen path test",
                assetName="Boss! Portal@2",
                assetType="dark boss",
                style="dark_fantasy",
                theme="ruined gate",
                finalPrompt="test",
            )
        )

    assert result.localPath == (
        "runtime/storage/generated-assets/gen_path_test/dark_boss/boss_portal_2.png"
    )
    assert Path(result.localPath).exists()


# ── gpt-image-2 (Chat Completions API) ──


def test_gpt_image2_generates_image(monkeypatch):
    """gpt-image-2 model should use chat completions endpoint and return image."""
    monkeypatch.setattr(
        "app.providers.gpt_image_provider.image_runtime_config.image_model",
        "gpt-image-2",
    )
    provider = GptImageProvider()

    with patch.object(httpx.Client, "post", side_effect=_mock_chat_post):
        result = provider.generate(
            ImageGenerationRequest(
                generationId="gen-gpt2-001",
                assetName="knight",
                assetType="character",
                style="fantasy",
                theme="medieval",
                finalPrompt="A brave knight in shining armor.",
            )
        )

    assert result.provider == "gpt_image"
    assert result.assetName == "knight"
    assert result.assetType == "character"
    assert result.metadata["model"] == "gpt-image-2"
    assert result.metadata["mock"] is False
    assert result.metadata["promptHash"]

    # Verify the image file was saved
    generated_path = Path(result.localPath)
    assert generated_path.exists()
    png_bytes = generated_path.read_bytes()
    assert png_bytes.startswith(PNG_SIGNATURE)
    assert base64.b64decode(DUMMY_PNG_BASE64) == png_bytes


# ── Error handling ──


def test_api_error_returns_runtime_error_with_body(monkeypatch):
    """API 5xx should raise RuntimeError with the response body."""
    provider = GptImageProvider()

    with patch.object(httpx.Client, "post", side_effect=_mock_error_post):
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate(
                ImageGenerationRequest(
                    generationId="gen-err",
                    assetName="test",
                    assetType="item",
                    style="cartoon",
                    theme="test",
                    finalPrompt="test prompt",
                )
            )

    error_msg = str(exc_info.value)
    assert "HTTP 500" in error_msg
    assert "没有按照预期生成图片" in error_msg
