import hashlib
from pathlib import Path

import httpx

from app.config import image_runtime_config
from app.models.asset_models import GeneratedImage, ImageGenerationRequest
from app.providers.image_provider import ImageProvider

BACKEND_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ASSET_DIR = BACKEND_ROOT / "runtime" / "storage" / "generated-assets"

NOVELAI_DEFAULT_ENDPOINT = "https://image.novelai.net"


class NovelAIImageProvider(ImageProvider):
    """Generates images via the NovelAI image generation API (NAI Diffusion)."""

    provider_name = "novelai"

    def is_available(self) -> bool:
        return bool(image_runtime_config.novelai_token)

    def generate(self, request: ImageGenerationRequest) -> GeneratedImage:
        if not self.is_available():
            raise RuntimeError(
                "NovelAI token is not configured for image generation. "
                "Set it in the Image API 配置 page."
            )

        png_bytes = self._call_novelai_api(request)
        destination_path = self._destination_path(request)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(png_bytes)

        return GeneratedImage(
            assetName=request.assetName,
            assetType=request.assetType,
            localPath=_relative_path(destination_path),
            provider=self.provider_name,
            metadata={
                "provider": self.provider_name,
                "model": image_runtime_config.image_model,
                "size": image_runtime_config.image_size,
                "endpoint": _novelai_endpoint(),
                "promptHash": _short_hash(request.finalPrompt),
                "promptVersion": request.promptVersion,
                "mock": False,
            },
        )

    def _call_novelai_api(self, request: ImageGenerationRequest) -> bytes:
        """Call NovelAI image generation API and return raw PNG bytes."""
        width, height = _parse_size(image_runtime_config.image_size)
        payload = {
            "input": request.finalPrompt,
            "model": image_runtime_config.image_model,
            "action": "generate",
            "parameters": {
                "width": width,
                "height": height,
                "scale": 5,
                "sampler": "k_euler",
                "steps": 28,
                "n_samples": 1,
                "ucPreset": 0,
                "qualityToggle": True,
                "sm": False,
                "sm_dyn": False,
                "add_original_image": False,
                "cfg_rescale": 0,
                "noise_schedule": "native",
                "dynamic_thresholding": False,
                "uncond_scale": 1,
            },
        }

        # Add negative prompt if present
        if request.negativePrompt:
            payload["parameters"]["negative_prompt"] = request.negativePrompt

        endpoint = _novelai_endpoint()
        with httpx.Client(**image_runtime_config.get_client_kwargs()) as client:
            response = client.post(
                f"{endpoint}/ai/generate-image",
                headers={
                    "Authorization": f"Bearer {image_runtime_config.novelai_token}",
                    "Content-Type": "application/json",
                    "Accept": "image/png",
                },
                json=payload,
            )

        # NovelAI returns binary PNG on success, JSON error on failure
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            error_data = response.json()
            raise RuntimeError(
                f"NovelAI API error ({response.status_code}): "
                f"{error_data.get('message', str(error_data))}"
            )

        if response.status_code != 200:
            response.raise_for_status()

        return response.content

    def _destination_path(self, request: ImageGenerationRequest) -> Path:
        generation_id = _safe_slug(request.generationId)
        asset_type = _safe_slug(request.assetType)
        asset_name = _safe_slug(request.assetName)
        return GENERATED_ASSET_DIR / generation_id / asset_type / f"{asset_name}.png"


def _novelai_endpoint() -> str:
    base = image_runtime_config.base_url.strip().rstrip("/")
    if base and base != "https://api.openai.com/v1":
        return base
    return NOVELAI_DEFAULT_ENDPOINT


def _parse_size(size_str: str) -> tuple[int, int]:
    """Parse 'WxH' or 'W*H' size string into (width, height)."""
    import re

    parts = re.split(r"[xX*×]", size_str)
    if len(parts) == 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            pass
    return 1024, 1024


def _safe_slug(value: str) -> str:
    slug = "".join(c if c.isalnum() else "_" for c in value.lower())
    return "_".join(p for p in slug.split("_") if p) or "asset"


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _relative_path(path: Path) -> str:
    return path.relative_to(BACKEND_ROOT).as_posix()
