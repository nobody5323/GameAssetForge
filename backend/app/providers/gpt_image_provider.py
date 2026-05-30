import base64
import hashlib
import re
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
    - dall-e-2 / dall-e-3: /v1/images/generations
    - gpt-image-2: /v1/chat/completions
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
        elif model.startswith("gpt-image"):
            base64_image, revised_prompt = self._call_chat_api(request.finalPrompt)
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

    def _call_dalle_api(self, prompt: str) -> tuple[str, str | None]:
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
        if model.startswith("dall-e"):
            payload["quality"] = image_runtime_config.image_quality

        data = self._httpx_post(
            f"{image_runtime_config.base_url}/images/generations",
            payload,
            "Images",
        )
        image_data = data["data"][0]
        return image_data["b64_json"], image_data.get("revised_prompt")

    def _call_chat_api(self, prompt: str) -> tuple[str, str | None]:
        api_key = image_runtime_config.api_key
        _require_ascii(api_key, "OpenAI API Key")

        payload = {
            "model": image_runtime_config.image_model,
            "messages": [{"role": "user", "content": prompt}],
            "n": 1,
            "size": image_runtime_config.image_size,
        }
        data = self._httpx_post(
            f"{image_runtime_config.base_url}/chat/completions",
            payload,
            "Chat Completions",
        )
        return self._parse_chat_response(data, prompt)

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

    def _parse_chat_response(self, data: dict, prompt: str) -> tuple[str, str | None]:
        # Some providers return image entries in top-level data.
        for item in data.get("data", []) or []:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "image" and isinstance(item.get("image"), dict):
                image = item["image"]
                if image.get("b64_json"):
                    return image["b64_json"], prompt
                if image.get("url"):
                    return _to_base64(self._download_image(image["url"])), prompt

        choices = data.get("choices", []) or []
        if choices:
            message = choices[0].get("message", {})
            for ann in message.get("annotations", []) or []:
                if not isinstance(ann, dict):
                    continue
                image = ann.get("image", {})
                if ann.get("type") == "image" and isinstance(image, dict):
                    if image.get("b64_json"):
                        return image["b64_json"], prompt
                    if image.get("url"):
                        return _to_base64(self._download_image(image["url"])), prompt

            content = message.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            image_url = _extract_image_url(str(content))
            if image_url:
                return _to_base64(self._download_image(image_url)), prompt

        raise RuntimeError(
            f"Chat Completions API returned unexpected format for model "
            f"{image_runtime_config.image_model}. "
            f"Expected image in data, message.annotations, or message.content. "
            f"Response keys: {list(data.keys())}, choices: {len(choices)}"
        )

    def _download_image(self, url: str) -> bytes:
        try:
            with httpx.Client(**image_runtime_config.get_client_kwargs()) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.content
        except RuntimeError:
            raise
        except httpx.RequestError as exc:
            raise RuntimeError(f"Failed to download image from {url}: {exc}") from exc

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


_MD_IMAGE_RE = re.compile(r"!\[.*?\]\((\S+?)\)")
_BARE_URL_RE = re.compile(
    r"(https?://\S+\.(?:png|jpg|jpeg|webp)(?:\?\S*)?)", re.IGNORECASE
)


def _extract_image_url(content: str) -> str | None:
    if not content:
        return None
    match = _MD_IMAGE_RE.search(content)
    if match:
        return match.group(1)
    match = _BARE_URL_RE.search(content)
    if match:
        return match.group(1)
    return None


def _to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("ascii")


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
