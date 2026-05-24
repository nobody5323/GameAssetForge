import base64
import hashlib
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
    - dall-e-2 / dall-e-3  →  /v1/images/generations  (Images API)
    - gpt-image-2          →  /v1/chat/completions     (Chat Completions API)
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

        if model.startswith("dall-e"):
            base64_image, revised_prompt = self._call_dalle_api(request.finalPrompt)
        else:
            # gpt-image-2 (and future non-DALL-E models) use chat completions
            base64_image, revised_prompt = self._call_chat_api(request.finalPrompt)

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

    def _call_chat_api(self, prompt: str) -> tuple[str, str | None]:
        """Call Chat Completions API for gpt-image-2 and return (base64, revised_prompt)."""
        api_key = image_runtime_config.api_key
        _require_ascii(api_key, "OpenAI API Key")

        model = image_runtime_config.image_model
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ],
            "n": 1,
            "size": image_runtime_config.image_size,
        }

        with httpx.Client(**image_runtime_config.get_client_kwargs()) as client:
            response = client.post(
                f"{image_runtime_config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            _raise_on_api_error(response, "Chat Completions")

        data = response.json()

        # gpt-image-2 returns image data in message.annotations
        try:
            annotations = data["choices"][0]["message"].get("annotations", [])
            for ann in annotations:
                if ann.get("type") == "image":
                    image_data = ann.get("image", {})
                    if "b64_json" in image_data:
                        return image_data["b64_json"], None
        except (KeyError, IndexError):
            pass

        raise RuntimeError(
            f"Chat Completions API returned unexpected format for model {model}. "
            f"Expected image in message.annotations. "
            f"Response keys: {list(data.keys())}, "
            f"choices: {len(data.get('choices', []))}"
        )

    def _call_dalle_api(self, prompt: str) -> tuple[str, str | None]:
        """Call OpenAI Images API and return (base64_png, revised_prompt)."""
        api_key = image_runtime_config.api_key
        _require_ascii(api_key, "OpenAI API Key")

        model = image_runtime_config.image_model
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": image_runtime_config.image_size,
            "response_format": "b64_json",
        }
        # Quality is only supported by DALL-E models, not gpt-image-*
        if model.startswith("dall-e"):
            payload["quality"] = image_runtime_config.image_quality

        with httpx.Client(**image_runtime_config.get_client_kwargs()) as client:
            response = client.post(
                f"{image_runtime_config.base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {image_runtime_config.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            _raise_on_api_error(response, "Images")

        data = response.json()
        image_data = data["data"][0]
        revised_prompt = image_data.get("revised_prompt")
        return image_data["b64_json"], revised_prompt

    def _destination_path(self, request: ImageGenerationRequest) -> Path:
        generation_id = _safe_slug(request.generationId)
        asset_type = _safe_slug(request.assetType)
        asset_name = _safe_slug(request.assetName)
        return GENERATED_ASSET_DIR / generation_id / asset_type / f"{asset_name}.png"


def _raise_on_api_error(response: httpx.Response, api_label: str) -> None:
    """Check response status and raise RuntimeError with the API error body."""
    if response.is_success:
        return
    try:
        body = response.text
    except Exception:
        body = "(unable to read response body)"
    raise RuntimeError(
        f"Image API ({api_label}) returned HTTP {response.status_code}: {body}"
    )


def _safe_slug(value: str) -> str:
    slug = "".join(c if c.isalnum() else "_" for c in value.lower())
    return "_".join(p for p in slug.split("_") if p) or "asset"


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _relative_path(path: Path) -> str:
    return path.relative_to(BACKEND_ROOT).as_posix()


def _require_ascii(value: str, label: str) -> None:
    """Raise a clear error if `value` contains non-ASCII characters (e.g. Chinese)."""
    if not value:
        return
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise RuntimeError(
            f"{label} 包含非 ASCII 字符（{exc.start}-{exc.end}），"
            f"HTTP 认证头只支持英文和数字。请检查 Image API 配置页面中的 Key/Token 是否正确。"
        ) from None
