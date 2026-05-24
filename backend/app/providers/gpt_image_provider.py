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
    """Generates images via the OpenAI Images API (DALL-E 3 / DALL-E 2)."""

    provider_name = "gpt_image"

    def is_available(self) -> bool:
        return bool(image_runtime_config.api_key)

    def generate(self, request: ImageGenerationRequest) -> GeneratedImage:
        if not self.is_available():
            raise RuntimeError(
                "OpenAI API key is not configured for image generation. "
                "Set IMAGE_GEN_API_KEY in the Image API 配置 page."
            )

        base64_image, revised_prompt = self._call_dalle_api(request.finalPrompt)
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
                "model": image_runtime_config.image_model,
                "size": image_runtime_config.image_size,
                "quality": image_runtime_config.image_quality,
                "promptHash": _short_hash(request.finalPrompt),
                "promptVersion": request.promptVersion,
                "revisedPrompt": revised_prompt or request.finalPrompt,
                "mock": False,
            },
        )

    def _call_dalle_api(self, prompt: str) -> tuple[str, str | None]:
        """Call OpenAI Images API and return (base64_png, revised_prompt)."""
        payload = {
            "model": image_runtime_config.image_model,
            "prompt": prompt,
            "n": 1,
            "size": image_runtime_config.image_size,
            "quality": image_runtime_config.image_quality,
            "response_format": "b64_json",
        }

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

    def _destination_path(self, request: ImageGenerationRequest) -> Path:
        generation_id = _safe_slug(request.generationId)
        asset_type = _safe_slug(request.assetType)
        asset_name = _safe_slug(request.assetName)
        return GENERATED_ASSET_DIR / generation_id / asset_type / f"{asset_name}.png"


def _safe_slug(value: str) -> str:
    slug = "".join(c if c.isalnum() else "_" for c in value.lower())
    return "_".join(p for p in slug.split("_") if p) or "asset"


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _relative_path(path: Path) -> str:
    return path.relative_to(BACKEND_ROOT).as_posix()
