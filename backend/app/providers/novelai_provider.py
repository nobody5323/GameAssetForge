import hashlib
import io
import random
from pathlib import Path

import httpx
import msgpack

from app.config import image_runtime_config
from app.models.asset_models import GeneratedImage, ImageGenerationRequest
from app.providers.image_provider import ImageProvider

BACKEND_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ASSET_DIR = BACKEND_ROOT / "runtime" / "storage" / "generated-assets"

NOVELAI_DEFAULT_ENDPOINT = "https://image.novelai.net"

# Default negative prompt for V4+ (UC preset 0 quality tags)
V4_DEFAULT_NEGATIVE_PROMPT = (
    "blurry, lowres, error, film grain, scan artifacts, "
    "worst quality, bad quality, jpeg artifacts, very displeasing, "
    "chromatic aberration, logo, dated, signature, multiple views, gigantic breasts"
)

# Quality tags prepended to prompt for V4+ (Danbooru tag convention)
V4_QUALITY_TAGS = "masterpiece, best quality, amazing quality, very aesthetic, absurdres, rating:general"


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
        """Call NovelAI image generation API and return raw image bytes."""
        model = image_runtime_config.image_model
        width, height = _parse_size(image_runtime_config.image_size)
        is_v4_plus = _is_v4_or_newer(model)

        if is_v4_plus:
            return self._call_v4_stream(request, model, width, height)
        else:
            return self._call_v3_generate(request, model, width, height)

    def _call_v4_stream(
        self, request: ImageGenerationRequest, model: str, width: int, height: int
    ) -> bytes:
        """Call V4/V4.5 streaming endpoint and extract final image from msgpack stream."""
        # Build prompt with quality tags (V4 convention)
        prompt = request.finalPrompt
        if "rating:" not in prompt.lower():
            prompt = f"{prompt}, {V4_QUALITY_TAGS}"

        negative_prompt = request.negativePrompt or V4_DEFAULT_NEGATIVE_PROMPT

        params = {
            "negative_prompt": negative_prompt,
            "qualityToggle": True,
            "ucPreset": 0,
            "width": width,
            "height": height,
            "n_samples": 1,
            "steps": 28,
            "scale": 5.5,
            "dynamic_thresholding": False,
            "seed": random.randint(0, 2**32 - 1),
            "sampler": "k_euler_ancestral",
            "cfg_rescale": 0.0,
            "noise_schedule": "karras",
            "controlnet_strength": 1.0,
            "add_original_image": True,
            "params_version": 3,
            "autoSmea": False,
            "characterPrompts": [],
            "v4_prompt": {
                "caption": {
                    "base_caption": prompt,
                    "char_captions": [],
                },
                "use_coords": False,
                "use_order": True,
            },
            "v4_negative_prompt": {
                "caption": {
                    "base_caption": negative_prompt,
                    "char_captions": [],
                },
                "legacy_uc": False,
            },
            "use_coords": False,
            "legacy_uc": False,
            "normalize_reference_strength_multiple": True,
            "deliberate_euler_ancestral_bug": False,
            "prefer_brownian": True,
            "legacy": False,
            "legacy_v3_extend": False,
            "stream": "msgpack",
        }

        payload = {
            "input": prompt,
            "model": model,
            "action": "generate",
            "parameters": params,
        }

        endpoint = _novelai_endpoint()
        kwargs = image_runtime_config.get_client_kwargs()
        kwargs.setdefault("timeout", 180)

        with httpx.Client(**kwargs) as client:
            response = client.post(
                f"{endpoint}/ai/generate-image-stream",
                headers={
                    "Authorization": f"Bearer {image_runtime_config.novelai_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        return _parse_v4_stream_response(response)

    def _call_v3_generate(
        self, request: ImageGenerationRequest, model: str, width: int, height: int
    ) -> bytes:
        """Call V3 generate endpoint (returns PNG or ZIP)."""
        params = {
            "width": width,
            "height": height,
            "scale": 5,
            "sampler": "k_euler",
            "steps": 28,
            "n_samples": 1,
            "ucPreset": 0,
            "qualityToggle": True,
            "add_original_image": False,
            "cfg_rescale": 0,
            "uncond_scale": 1,
            "sm": False,
            "sm_dyn": False,
            "noise_schedule": "native",
            "dynamic_thresholding": False,
        }

        payload = {
            "input": request.finalPrompt,
            "model": model,
            "action": "generate",
            "parameters": params,
        }

        if request.negativePrompt:
            params["negative_prompt"] = request.negativePrompt

        endpoint = _novelai_endpoint()
        kwargs = image_runtime_config.get_client_kwargs()
        kwargs.setdefault("timeout", 120)

        with httpx.Client(**kwargs) as client:
            response = client.post(
                f"{endpoint}/ai/generate-image",
                headers={
                    "Authorization": f"Bearer {image_runtime_config.novelai_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        return _parse_v3_response(response)

    def _destination_path(self, request: ImageGenerationRequest) -> Path:
        generation_id = _safe_slug(request.generationId)
        asset_type = _safe_slug(request.assetType)
        asset_name = _safe_slug(request.assetName)
        return GENERATED_ASSET_DIR / generation_id / asset_type / f"{asset_name}.png"


def _parse_v4_stream_response(response) -> bytes:
    """Parse NovelAI V4/V4.5 msgpack stream response.

    The stream contains intermediate step images (JPEG) at each denoising step.
    We extract the final image (lowest sigma value).
    """
    content_type = response.headers.get("content-type", "")

    # JSON error response
    if "application/json" in content_type:
        try:
            error_data = response.json()
        except Exception:
            response.raise_for_status()
            raise RuntimeError(
                f"NovelAI API error ({response.status_code}): {response.text[:500]}"
            )
        raise RuntimeError(
            f"NovelAI API error ({response.status_code}): "
            f"{error_data.get('message', str(error_data))}"
        )

    if response.status_code != 200:
        body_preview = response.text[:500] if hasattr(response, "text") else str(response.content[:500])
        raise RuntimeError(
            f"NovelAI API error ({response.status_code}): {body_preview}"
        )

    # Decode msgpack stream
    return _decode_v4_msgpack_stream(response.content)


def _decode_v4_msgpack_stream(data: bytes) -> bytes:
    """Decode V4/V4.5 msgpack stream and extract the final generated image.

    The stream contains multiple frames per denoising step.
    Each step frame has: event_type, samp_ix, step_ix, gen_id, sigma, image.
    We collect all image frames and return the one with the lowest sigma (final step).

    Falls back to raw byte scanning if msgpack parsing fails mid-stream.
    """
    last_image = None
    last_sigma = float("inf")
    error_messages = []

    def _try_extract_image(msg):
        nonlocal last_image, last_sigma
        if not isinstance(msg, dict):
            return
        # Check for error frames
        event_type = msg.get(b"event_type") or msg.get("event_type")
        if event_type and event_type in (b"error", "error"):
            msg_text = msg.get(b"message") or msg.get("message") or str(msg)
            if isinstance(msg_text, bytes):
                msg_text = msg_text.decode("utf-8", errors="replace")
            error_messages.append(str(msg_text))
            return
        # Extract image from step frames
        img = msg.get(b"image") or msg.get("image")
        if isinstance(img, bytes) and _is_image_data(img):
            sigma = msg.get(b"sigma") or msg.get("sigma") or float("inf")
            if isinstance(sigma, (int, float)) and sigma < last_sigma:
                last_sigma = sigma
                last_image = img

    # Primary: parse as msgpack stream
    try:
        unpacker = msgpack.Unpacker(io.BytesIO(data), raw=True, strict_map_key=False, use_list=False)
        for msg in unpacker:
            _try_extract_image(msg)
    except Exception:
        # Msgpack stream often has non-standard trailing data; if we already
        # extracted the image, that's fine — just use it.
        pass

    # Fallback: scan raw bytes for the largest JPEG/PNG blob
    if last_image is None:
        last_image = _scan_raw_for_image(data)

    if error_messages and last_image is None:
        raise RuntimeError(
            f"NovelAI generation error: {'; '.join(error_messages[-3:])}"
        )

    if last_image is None:
        raise RuntimeError(
            "NovelAI msgpack response did not contain recognizable image data"
        )

    return last_image


def _scan_raw_for_image(data: bytes) -> bytes | None:
    """Fallback: scan raw bytes for the largest embedded JPEG or PNG image."""
    import re

    best = None
    best_len = 0

    # Find JPEG markers: FF D8 FF ... FF D9
    for match in re.finditer(b"\xff\xd8\xff.{32,}?\xff\xd9", data, re.DOTALL):
        img = match.group()
        if len(img) > best_len:
            best = img
            best_len = len(img)

    if best:
        return best

    # Find PNG markers: 89 50 4E 47 ... 49 45 4E 44 AE 42 60 82
    for match in re.finditer(b"\x89PNG\r\n\x1a\n.{32,}?IEND\xaeB`\x82", data, re.DOTALL):
        img = match.group()
        if len(img) > best_len:
            best = img
            best_len = len(img)

    return best


def _parse_v3_response(response) -> bytes:
    """Parse NovelAI V3 API response, handling JSON errors, PNG, and ZIP."""
    content_type = response.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            error_data = response.json()
        except Exception:
            response.raise_for_status()
            raise RuntimeError(
                f"NovelAI API error ({response.status_code}): {response.text[:500]}"
            )
        raise RuntimeError(
            f"NovelAI API error ({response.status_code}): "
            f"{error_data.get('message', str(error_data))}"
        )

    if response.status_code != 200:
        body_preview = response.text[:500] if hasattr(response, "text") else str(response.content[:500])
        raise RuntimeError(
            f"NovelAI API error ({response.status_code}): {body_preview}"
        )

    content = response.content
    # V3 returns raw PNG, or ZIP for multiple images
    if content[:4] == b"PK\x03\x04":  # ZIP magic bytes
        import zipfile

        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = zf.namelist()
            if not names:
                raise RuntimeError("NovelAI returned empty ZIP archive")
            return zf.read(names[0])
    return content


def _is_v4_or_newer(model: str) -> bool:
    """Check if the model is V4 or newer (uses streaming endpoint with msgpack)."""
    return "diffusion-4" in model


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


def _is_image_data(data: bytes) -> bool:
    """Check if bytes look like image data (JPEG, PNG, or other common formats)."""
    if len(data) < 64:
        return False
    # JPEG: starts with FF D8 FF
    if data[:3] == b"\xff\xd8\xff":
        return True
    # PNG: starts with 89 50 4E 47
    if data[:4] == b"\x89PNG":
        return True
    # WebP: RIFF....WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    # GIF: GIF89a or GIF87a
    if data[:6] in (b"GIF89a", b"GIF87a"):
        return True
    # BMP
    if data[:2] == b"BM":
        return True
    return False


def _relative_path(path: Path) -> str:
    return path.relative_to(BACKEND_ROOT).as_posix()
