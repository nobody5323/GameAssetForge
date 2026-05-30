import base64
import hashlib
import time
from pathlib import Path

import httpx

from app.config import image_runtime_config
from app.models.asset_models import GeneratedImage, ImageGenerationRequest
from app.providers.image_provider import ImageProvider

BACKEND_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ASSET_DIR = BACKEND_ROOT / "runtime" / "storage" / "generated-assets"


class GptImageProvider(ImageProvider):
    """Generates images via OpenAI APIs.

    Dispatches to the correct endpoint based on model name:
    - dall-e-* and gpt-image-* use /v1/images/generations

    The Responses API can also generate images through the image_generation
    tool, but GPT Image models are not sent directly to /chat/completions.
    """

    provider_name = "gpt_image"

    def is_available(self) -> bool:
        return bool(image_runtime_config.api_key)

    def generate(self, request: ImageGenerationRequest) -> GeneratedImage:
        if not self.is_available():
            raise RuntimeError(
                "OpenAI API key is not configured for image generation. "
                "Set IMAGE_GEN_API_KEY in the Image API 配置 page."
            )

        model = image_runtime_config.image_model
        if model.startswith(("dall-e", "gpt-image")):
            base64_image, revised_prompt = self._call_image_api(request.finalPrompt)
        else:
            raise RuntimeError(f"Unsupported image model: {model}")

        image_bytes = base64.b64decode(base64_image)
        destination_path = self._destination_path(request)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(image_bytes)

        return GeneratedImage(
            assetName=request.assetName,
            assetType=request.assetType,
            localPath=_relative_path(destination_path),
            provider=self.provider_name,
            metadata={
                "provider": self.provider_name,
                "model": model,
                "size": image_runtime_config.image_size,
                "quality": image_runtime_config.image_quality,
                "promptHash": _short_hash(request.finalPrompt),
                "promptVersion": request.promptVersion,
                "revisedPrompt": revised_prompt or request.finalPrompt,
                "mock": False,
            },
        )

    def _call_image_api(self, prompt: str) -> tuple[str, str | None]:
        api_key = image_runtime_config.api_key
        _require_ascii(api_key, "OpenAI API Key")

        model = image_runtime_config.image_model
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": image_runtime_config.image_size,
        }
        if model.startswith("dall-e"):
            payload["response_format"] = "b64_json"
            payload["quality"] = _dalle_quality(image_runtime_config.image_quality)
        else:
            payload["quality"] = _gpt_image_quality(image_runtime_config.image_quality)

        data = self._httpx_post(
            f"{image_runtime_config.base_url}/images/generations",
            payload,
            "Images",
        )
        image_data = data["data"][0]
        return image_data["b64_json"], image_data.get("revised_prompt")

    def _httpx_post(self, url: str, payload: dict, api_label: str) -> dict:
        api_key = image_runtime_config.api_key
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with httpx.Client(**image_runtime_config.get_client_kwargs()) as client:
                    response = client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "Connection": "close",
                        },
                        json=payload,
                    )
                    _raise_on_api_error(response, api_label)
                return response.json()
            except RuntimeError:
                raise
            except httpx.RequestError as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(5)
                    continue
        raise RuntimeError(
            f"Image API ({api_label}) network error — "
            f"服务器连接断开（已重试 1 次）: {last_error}"
        ) from last_error

    def _destination_path(self, request: ImageGenerationRequest) -> Path:
        generation_id = _safe_slug(request.generationId)
        asset_type = _safe_slug(request.assetType)
        asset_name = _safe_slug(request.assetName)
        return GENERATED_ASSET_DIR / generation_id / asset_type / f"{asset_name}.png"


def _raise_on_api_error(response: httpx.Response, api_label: str) -> None:
    if response.is_success:
        return
    try:
        body = response.text
    except Exception:
        body = "(unable to read response body)"
    raise RuntimeError(
        f"Image API ({api_label}) returned HTTP {response.status_code}: {body}"
    )


def _gpt_image_quality(value: str) -> str:
    if value in {"low", "medium", "high", "auto"}:
        return value
    if value == "hd":
        return "high"
    return "medium"


def _dalle_quality(value: str) -> str:
    if value in {"standard", "hd"}:
        return value
    if value == "high":
        return "hd"
    return "standard"


def _safe_slug(value: str) -> str:
    slug = "".join(c if c.isalnum() else "_" for c in value.lower())
    return "_".join(p for p in slug.split("_") if p) or "asset"


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _relative_path(path: Path) -> str:
    return path.relative_to(BACKEND_ROOT).as_posix()


def _require_ascii(value: str, label: str) -> None:
    if not value:
        return
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise RuntimeError(
            f"{label} 包含非 ASCII 字符（{exc.start}-{exc.end}），"
            f"HTTP 认证头只支持英文和数字。请检查 Image API 配置页面中的 Key/Token 是否正确。"
        ) from None
