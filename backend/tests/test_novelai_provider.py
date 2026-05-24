from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from app.models.asset_models import ImageGenerationRequest
from app.providers.novelai_provider import NovelAIImageProvider

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Minimal valid 1x1 red PNG bytes
DUMMY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
    b"\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _mock_novelai_success(*args, **kwargs):
    """Return a mocked httpx.Response with PNG bytes."""

    class MockResponse:
        status_code = 200
        content = DUMMY_PNG_BYTES
        headers = {"content-type": "image/png"}

        def raise_for_status(self):
            pass

        def json(self):
            return {}

    return MockResponse()


def _mock_novelai_error(*args, **kwargs):
    """Return a mocked httpx.Response with JSON error."""

    class MockResponse:
        status_code = 401
        headers = {"content-type": "application/json"}

        def raise_for_status(self):
            raise httpx.HTTPStatusError(
                "Unauthorized",
                request=args[0] if args else None,
                response=self,
            )

        def json(self):
            return {"statusCode": 401, "message": "Invalid token"}

    return MockResponse()


@pytest.fixture(autouse=True)
def _patch_config(monkeypatch):
    """Ensure NovelAIImageProvider reports as available during tests."""
    monkeypatch.setattr(
        "app.providers.novelai_provider.image_runtime_config.novelai_token",
        "test-novelai-token",
    )
    monkeypatch.setattr(
        "app.providers.novelai_provider.image_runtime_config.image_model",
        "nai-diffusion-3",
    )
    monkeypatch.setattr(
        "app.providers.novelai_provider.image_runtime_config.image_size",
        "1024x1024",
    )
    monkeypatch.setattr(
        "app.providers.novelai_provider.image_runtime_config.base_url",
        "https://image.novelai.net",
    )


def test_novelai_provider_is_available_with_token():
    provider = NovelAIImageProvider()
    assert provider.is_available() is True


def test_novelai_provider_not_available_without_token(monkeypatch):
    monkeypatch.setattr(
        "app.providers.novelai_provider.image_runtime_config.novelai_token",
        "",
    )
    provider = NovelAIImageProvider()
    assert provider.is_available() is False


def test_novelai_provider_generates_image():
    provider = NovelAIImageProvider()

    with patch.object(
        httpx.Client, "post", side_effect=_mock_novelai_success
    ):
        result = provider.generate(
            ImageGenerationRequest(
                generationId="gen-nai-001",
                assetName="witch",
                assetType="character",
                style="pixel_art",
                theme="magic forest",
                finalPrompt="masterpiece, best quality, 1girl, witch hat, forest",
                negativePrompt="worst quality, lowres, blurry",
            )
        )

    assert result.provider == "novelai"
    assert result.assetName == "witch"
    assert result.assetType == "character"
    assert result.metadata["model"] == "nai-diffusion-3"
    assert result.metadata["mock"] is False
    assert result.metadata["promptHash"]

    generated_path = Path(result.localPath)
    assert generated_path.exists()
    assert generated_path.read_bytes().startswith(PNG_SIGNATURE)


def test_novelai_provider_error_without_token():
    """Without a token, generate() should raise RuntimeError."""
    with patch.object(
        NovelAIImageProvider,
        "is_available",
        return_value=False,
    ):
        provider = NovelAIImageProvider()
        with pytest.raises(RuntimeError, match="token is not configured"):
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


def test_novelai_provider_api_error():
    """API errors should be raised."""
    provider = NovelAIImageProvider()

    with patch.object(
        httpx.Client, "post", side_effect=_mock_novelai_error
    ):
        with pytest.raises((RuntimeError, httpx.HTTPStatusError)):
            provider.generate(
                ImageGenerationRequest(
                    generationId="gen-api-err",
                    assetName="test",
                    assetType="item",
                    style="cartoon",
                    theme="test",
                    finalPrompt="test",
                )
            )


def test_novelai_provider_path_sanitized():
    provider = NovelAIImageProvider()

    with patch.object(
        httpx.Client, "post", side_effect=_mock_novelai_success
    ):
        result = provider.generate(
            ImageGenerationRequest(
                generationId="gen nai path",
                assetName="Dark! Lord@",
                assetType="boss monster",
                style="dark_fantasy",
                theme="evil castle",
                finalPrompt="test",
            )
        )

    assert result.localPath == (
        "runtime/storage/generated-assets/gen_nai_path/boss_monster/dark_lord.png"
    )
    assert Path(result.localPath).exists()
