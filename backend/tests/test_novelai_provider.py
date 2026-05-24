import io
from pathlib import Path
from unittest.mock import patch

import httpx
import msgpack
import pytest

from app.models.asset_models import ImageGenerationRequest
from app.providers.novelai_provider import NovelAIImageProvider

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff\xe0"

# Minimal valid 1x1 red PNG bytes
DUMMY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
    b"\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82"
)

# Minimal JPEG bytes (1x1 white pixel)
DUMMY_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
    b"\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d"
    b"\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00"
    b"\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x001\x00\x00\x01"
    b"\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02"
    b"\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03"
    b"\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B"
    b"\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789"
    b":CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a"
    b"\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8"
    b"\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6"
    b"\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3"
    b"\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9"
    b"\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xff\x00?\x00\x1f\xff"
    b"\xd9"
)


def _build_v4_msgpack_stream(image_bytes: bytes, steps: int = 3) -> bytes:
    """Build a realistic V4 msgpack stream with step frames and a final image."""
    buf = io.BytesIO()
    sigma = 20000.0
    for step in range(steps):
        frame = {
            b"event_type": b"intermediate",
            b"samp_ix": 0,
            b"step_ix": step,
            b"gen_id": 12345,
            b"sigma": sigma,
            b"image": image_bytes,
        }
        packed = msgpack.packb(frame)
        buf.write(packed)
        sigma = sigma * 0.1  # sigma decreases per step
    return buf.getvalue()


def _mock_v4_novelai_success(*args, **kwargs):
    """Return a mocked httpx.Response with V4 msgpack stream."""

    class MockResponse:
        status_code = 200
        content = _build_v4_msgpack_stream(DUMMY_JPEG_BYTES, steps=3)
        headers = {"content-type": "application/msgpack"}

        def raise_for_status(self):
            pass

        def json(self):
            return {}

    return MockResponse()


def _mock_v3_novelai_success(*args, **kwargs):
    """Return a mocked httpx.Response with PNG bytes (V3)."""

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


def _mock_v4_novelai_msgpack_error(*args, **kwargs):
    """Return V4 stream with an error frame."""

    class MockResponse:
        status_code = 200
        headers = {"content-type": "application/msgpack"}

        @property
        def content(self):
            buf = io.BytesIO()
            error_frame = {
                b"event_type": b"error",
                b"code": b"500",
                b"message": b"Error generating image, an internal error occurred",
            }
            buf.write(msgpack.packb(error_frame))
            return buf.getvalue()

        def raise_for_status(self):
            pass

        def json(self):
            return {}

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


# ── Availability tests ──────────────────────────────────────────────


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


# ── V3 generation tests ─────────────────────────────────────────────


def test_v3_provider_generates_image():
    provider = NovelAIImageProvider()

    with patch.object(
        httpx.Client, "post", side_effect=_mock_v3_novelai_success
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


def test_v3_provider_path_sanitized():
    provider = NovelAIImageProvider()

    with patch.object(
        httpx.Client, "post", side_effect=_mock_v3_novelai_success
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


# ── V4 generation tests ─────────────────────────────────────────────


def test_v4_provider_generates_image(monkeypatch):
    """V4.5 Full model should use streaming endpoint and return JPEG image bytes."""
    monkeypatch.setattr(
        "app.providers.novelai_provider.image_runtime_config.image_model",
        "nai-diffusion-4-5-full",
    )
    provider = NovelAIImageProvider()

    with patch.object(
        httpx.Client, "post", side_effect=_mock_v4_novelai_success
    ):
        result = provider.generate(
            ImageGenerationRequest(
                generationId="gen-v4-001",
                assetName="warrior",
                assetType="character",
                style="anime",
                theme="battlefield",
                finalPrompt="1girl, warrior, armor",
                negativePrompt="lowres, bad anatomy",
            )
        )

    assert result.provider == "novelai"
    assert result.assetName == "warrior"
    assert result.metadata["model"] == "nai-diffusion-4-5-full"
    assert result.metadata["mock"] is False

    generated_path = Path(result.localPath)
    assert generated_path.exists()
    # V4 returns JPEG bytes from the stream
    saved_bytes = generated_path.read_bytes()
    assert saved_bytes.startswith(DUMMY_JPEG_BYTES[:4])


def test_v4_provider_msgpack_error(monkeypatch):
    """V4 msgpack stream with error frames should raise RuntimeError."""
    monkeypatch.setattr(
        "app.providers.novelai_provider.image_runtime_config.image_model",
        "nai-diffusion-4-5-full",
    )
    provider = NovelAIImageProvider()

    with patch.object(
        httpx.Client, "post", side_effect=_mock_v4_novelai_msgpack_error
    ):
        with pytest.raises(RuntimeError, match="NovelAI generation error"):
            provider.generate(
                ImageGenerationRequest(
                    generationId="gen-v4-err",
                    assetName="test",
                    assetType="item",
                    style="anime",
                    theme="test",
                    finalPrompt="test",
                )
            )


# ── Error handling tests ────────────────────────────────────────────


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
