import base64
import hashlib
import re
from pathlib import Path

import httpx

from app.config import image_runtime_config
from app.models.asset_models import GeneratedImage, ImageGenerationRequest
from app.providers.image_provider import ImageProvider

BACKEND_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ASSET_DIR = BACKEND_ROOT / "runtime" / "storage" / "generated-assets"


class GptImageProvider(ImageProvider):
    """Generates images via OpenAI Images API (DALL-E) or Chat Completions API (gpt-image-2)."""

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
            image_bytes = base64.b64decode(base64_image)
        elif model.startswith("gpt-image"):
            image_bytes, revised_prompt = self._call_chat_api(request.finalPrompt)
        else:
            raise RuntimeError(f"Unsupported image model: {model}")

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

    # ── DALL-E API (legacy) ──

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

        with httpx.Client(**image_runtime_config.get_client_kwargs()) as client:
            response = client.post(
                f"{image_runtime_config.base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {image_runtime_config.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        image_data = data["data"][0]
        revised_prompt = image_data.get("revised_prompt")
        return image_data["b64_json"], revised_prompt

    # ── Chat Completions API (gpt-image-2) ──

    def _call_chat_api(self, prompt: str) -> tuple[bytes, str | None]:
        max_attempts = 2
        last_error: Exception | None = None

        for attempt in range(max_attempts):
            try:
                response = self._httpx_post(prompt)
                _raise_on_api_error(response, "Chat Completions")
                data = response.json()
                return self._parse_chat_response(data, prompt)
            except httpx.RequestError as exc:
                last_error = RuntimeError(
                    f"Image API (Chat Completions) network error — 服务器连接断开: {exc}"
                )
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(5)
                    continue
                raise last_error
            except RuntimeError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(5)
                    continue

        raise last_error  # type: ignore[misc]

    def _httpx_post(self, prompt: str) -> httpx.Response:
        api_key = image_runtime_config.api_key
        _require_ascii(api_key, "OpenAI API Key")

        payload = {
            "model": image_runtime_config.image_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        kwargs = image_runtime_config.get_client_kwargs()
        kwargs.setdefault("timeout", 300)
        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Connection": "close",
        })

        with httpx.Client(**kwargs) as client:
            return client.post(
                f"{image_runtime_config.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )

    def _parse_chat_response(self, data: dict, prompt: str) -> tuple[bytes, str | None]:
        # Path 1: OpenAI native annotations format
        annotations = data.get("data", [])
        if annotations and isinstance(annotations, list):
            for item in annotations:
                if isinstance(item, dict) and item.get("type") == "image" and item.get("image"):
                    b64 = item["image"].get("b64_json")
                    if b64:
                        return base64.b64decode(b64), prompt
                    url = item["image"].get("url")
                    if url:
                        return self._download_image(url), prompt

        # Path 2: Standard OpenAI message.annotations
        choices = data.get("choices", [])
        if choices:
            choice = choices[0]
            message = choice.get("message", {})
            annotations_list = message.get("annotations", [])
            for ann in annotations_list:
                if isinstance(ann, dict) and ann.get("type") == "image" and ann.get("image"):
                    b64 = ann["image"].get("b64_json")
                    if b64:
                        return base64.b64decode(b64), prompt
                    url = ann["image"].get("url")
                    if url:
                        return self._download_image(url), prompt

        # Path 3: micuapi.ai proxy — markdown URL in message.content
        content = ""
        if choices:
            msg = choices[0].get("message", {})
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
        img_url = _extract_image_url(str(content))
        if img_url:
            return self._download_image(img_url), prompt

        raise RuntimeError(
            f"Chat Completions API returned unexpected format for model "
            f"{image_runtime_config.image_model}. "
            f"Expected image in message.annotations or message.content. "
            f"Response keys: {list(data.keys())}, choices: {len(choices)}"
        )

    def _download_image(self, url: str) -> bytes:
        with httpx.Client(**image_runtime_config.get_client_kwargs()) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content

    # ── Helpers ──

    def _destination_path(self, request: ImageGenerationRequest) -> Path:
        generation_id = _safe_slug(request.generationId)
        asset_type = _safe_slug(request.assetType)
        asset_name = _safe_slug(request.assetName)
        return GENERATED_ASSET_DIR / generation_id / asset_type / f"{asset_name}.png"


# ── Module-level helpers ──

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


def _extract_image_url(text: str) -> str | None:
    """Extract image URL from markdown or plain URL in text content."""
    md_match = re.search(r"!\[.*?\]\(([^)]+)\)", text)
    if md_match:
        url = md_match.group(1)
        if url.endswith((".png", ".jpg", ".jpeg", ".webp")):
            return url
    url_match = re.search(r"https?://\S+\.(?:png|jpg|jpeg|webp)", text)
    if url_match:
        return url_match.group(0)
    return None


def _raise_on_api_error(response: httpx.Response, label: str) -> None:
    if not response.is_success:
        body = ""
        try:
            body = response.text
        except Exception:
            pass
        raise RuntimeError(
            f"{label} API returned {response.status_code}: {body[:500]}"
        )
