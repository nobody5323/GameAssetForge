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
            if request.referenceImagePath:
                raise RuntimeError(
                    "DALL-E models do not support image-to-image (referenceImagePath). "
                    "Use gpt-image-2 instead."
                )
            base64_image, revised_prompt = self._call_dalle_api(request.finalPrompt)
        elif request.referenceImagePath:
            # gpt-image-2 image-to-image via micuapi.ai reference_image param
            base64_image, revised_prompt = self._call_reference_api(
                request.finalPrompt,
                request.referenceImagePath,
            )
        else:
            # gpt-image-2 text-to-image via Chat Completions
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

    # ── Images Edits API (image-to-image via micuapi.ai, multipart) ──

    def _call_reference_api(
        self,
        prompt: str,
        reference_image_path: str,
    ) -> tuple[str, str | None]:
        """Call /v1/images/edits with multipart form data for image-to-image.

        micuapi.ai supports the OpenAI Images Edits endpoint.  The reference
        image is sent as a multipart file part (not a data URL), which is the
        correct format for 1K (1024x1024) image-to-image requests.
        """
        api_key = image_runtime_config.api_key
        _require_ascii(api_key, "OpenAI API Key")

        ref_path = BACKEND_ROOT / reference_image_path
        if not ref_path.exists():
            raise RuntimeError(f"Reference image not found: {reference_image_path}")

        ref_bytes = ref_path.read_bytes()
        ext = ref_path.suffix.lower()
        mime = "image/png" if ext == ".png" else "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

        model = image_runtime_config.image_model

        # Multipart form data — the "image" field is a file tuple (filename, bytes, mime)
        files = {
            "image": (ref_path.name, ref_bytes, mime),
        }
        data_fields = {
            "model": model,
            "prompt": prompt,
            "n": "1",
            "size": image_runtime_config.image_size,
            "response_format": "b64_json",
        }

        url = f"{image_runtime_config.base_url}/images/edits"
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with httpx.Client(**image_runtime_config.get_client_kwargs()) as client:
                    response = client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Connection": "close",
                        },
                        data=data_fields,
                        files=files,
                    )
                    _raise_on_api_error(response, "Images Edits")
                return self._parse_image_response(response.json())
            except RuntimeError:
                raise
            except httpx.RequestError as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(5)
                    continue
        raise RuntimeError(
            f"Image API (Images Edits) network error — "
            f"服务器连接断开（已重试 1 次）: {last_error}"
        ) from last_error

    def _parse_image_response(self, data: dict) -> tuple[str, str | None]:
        """Extract (b64_json, revised_prompt) from an images API response."""
        image_data = data["data"][0]
        return image_data["b64_json"], image_data.get("revised_prompt")

    # ── Chat Completions API (gpt-image-2 text-to-image) ─────────────

    def _call_chat_api(
        self,
        prompt: str,
        reference_image_path: str | None = None,  # kept for backward compat, ignored
    ) -> tuple[str, str | None]:
        """Call Chat Completions API for gpt-image-2 text-to-image.

        Handles multiple response formats from different providers:
        - OpenAI official: message.annotations[].image.b64_json
        - Third-party proxies (e.g. micuapi.ai): message.content with markdown ![image](url)
        """
        api_key = image_runtime_config.api_key
        _require_ascii(api_key, "OpenAI API Key")

        model = image_runtime_config.image_model
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "n": 1,
        }

        data = self._httpx_post(
            f"{image_runtime_config.base_url}/chat/completions",
            payload,
            "Chat Completions",
        )

        message = data["choices"][0]["message"]

        # Path 1: OpenAI official format — annotations with b64_json
        try:
            annotations = message.get("annotations", [])
            for ann in annotations:
                if ann.get("type") == "image":
                    image_data = ann.get("image", {})
                    if "b64_json" in image_data:
                        return image_data["b64_json"], None
        except (KeyError, IndexError):
            pass

        # Path 2: Third-party proxy — markdown image URL in content
        content = message.get("content") or ""
        image_url = _extract_image_url(content)
        if image_url:
            image_bytes = self._download_image(image_url)
            return base64.b64encode(image_bytes).decode("ascii"), None

        # Path 3: Neither format found
        raise RuntimeError(
            f"Chat Completions API returned unexpected format for model {model}. "
            f"Response keys: {list(data.keys())}, "
            f"choices: {len(data.get('choices', []))}, "
            f"content snippet: {content[:300] if content else 'empty'}"
        )

    # ── Images API (dall-e-*) ──────────────────────────────────────

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
        if model.startswith("dall-e"):
            payload["quality"] = _dalle_quality(image_runtime_config.image_quality)

        data = self._httpx_post(
            f"{image_runtime_config.base_url}/images/generations",
            payload,
            "Images",
        )

        image_data = data["data"][0]
        revised_prompt = image_data.get("revised_prompt")
        return image_data["b64_json"], revised_prompt

    # ── HTTP helpers ───────────────────────────────────────────────

    def _httpx_post(self, url: str, payload: dict, api_label: str) -> dict:
        """Make httpx POST and return parsed JSON. Retries once on network errors."""
        api_key = image_runtime_config.api_key
        last_error: Exception | None = None
        for attempt in range(2):  # original + 1 retry
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

    def _download_image(self, url: str) -> bytes:
        """Download image bytes from a URL using httpx."""
        try:
            with httpx.Client(
                timeout=image_runtime_config.get_client_kwargs().get("timeout", 120),
                verify=True,
            ) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.content
        except RuntimeError:
            raise
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Failed to download image from {url}: {exc}"
            ) from exc

    # ── file path ──────────────────────────────────────────────────

    def _destination_path(self, request: ImageGenerationRequest) -> Path:
        generation_id = _safe_slug(request.generationId)
        asset_type = _safe_slug(request.assetType)
        asset_name = _safe_slug(request.assetName)
        return GENERATED_ASSET_DIR / generation_id / asset_type / f"{asset_name}.png"


# ── module-level helpers ───────────────────────────────────────────


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


# Matches markdown image syntax: ![alt](url)
_MD_IMAGE_RE = re.compile(r"!\[.*?\]\((\S+?)\)")
# Fallback: bare image URL (png/jpg/jpeg/webp)
_BARE_URL_RE = re.compile(
    r"(https?://\S+\.(?:png|jpg|jpeg|webp)(?:\?\S*)?)", re.IGNORECASE
)


def _extract_image_url(content: str) -> str | None:
    """Extract the first image URL from a chat completion content string."""
    if not content:
        return None
    # Try markdown image syntax first
    m = _MD_IMAGE_RE.search(content)
    if m:
        return m.group(1)
    # Fallback to bare image URL
    m = _BARE_URL_RE.search(content)
    if m:
        return m.group(1)
    return None


def _dalle_quality(value: str) -> str:
    """Normalize quality value for DALL-E Images API."""
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
    """Raise a clear error if `value` contains non-ASCII characters."""
    if not value:
        return
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise RuntimeError(
            f"{label} 包含非 ASCII 字符（{exc.start}-{exc.end}），"
            f"HTTP 认证头只支持英文和数字。请检查 Image API 配置页面中的 Key/Token 是否正确。"
        ) from None
