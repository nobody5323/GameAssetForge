import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from app.models.config_models import (
    ImageConfigResponse,
    ImageConfigUpdate,
    ImageGenProvider,
    LlmConfigResponse,
    LlmConfigUpdate,
    PromptProvider,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG_PATH = BACKEND_ROOT / "runtime" / "llm-config.local.json"
IMAGE_CONFIG_PATH = BACKEND_ROOT / "runtime" / "image-config.local.json"


@dataclass
class LlmRuntimeConfig:
    provider: PromptProvider
    base_url: str
    prompt_model: str
    api_key: str

    @classmethod
    def load(cls) -> "LlmRuntimeConfig":
        config = cls(
            provider=os.getenv("PROMPT_PROVIDER", "openai"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            prompt_model=os.getenv("OPENAI_PROMPT_MODEL", "gpt-5-mini"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )
        config.load_local()
        return config

    def update(self, payload: LlmConfigUpdate) -> None:
        self.provider = payload.provider
        self.base_url = normalize_base_url(payload.baseUrl)
        self.prompt_model = payload.promptModel.strip() or "gpt-5-mini"
        if payload.clearApiKey:
            self.api_key = ""
        elif payload.apiKey is not None and payload.apiKey.strip():
            self.api_key = payload.apiKey.strip()
        self.save_local()

    def load_local(self) -> None:
        if not LOCAL_CONFIG_PATH.exists():
            return
        data = json.loads(LOCAL_CONFIG_PATH.read_text(encoding="utf-8"))
        self.provider = data.get("provider", self.provider)
        self.base_url = normalize_base_url(data.get("baseUrl", self.base_url))
        self.prompt_model = data.get("promptModel", self.prompt_model)
        self.api_key = data.get("apiKey", self.api_key)

    def save_local(self) -> None:
        LOCAL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOCAL_CONFIG_PATH.write_text(
            json.dumps(
                {
                    "provider": self.provider,
                    "baseUrl": self.base_url,
                    "promptModel": self.prompt_model,
                    "apiKey": self.api_key,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def public_response(self) -> LlmConfigResponse:
        return LlmConfigResponse(
            provider=self.provider,
            baseUrl=self.base_url,
            promptModel=self.prompt_model,
            hasApiKey=bool(self.api_key),
        )


# ── Image Generation Runtime Config ──


@dataclass
class ImageRuntimeConfig:
    """Image generation configuration for DALL-E / NovelAI providers."""

    provider: ImageGenProvider = "openai"
    base_url: str = "https://api.openai.com/v1"
    image_model: str = "dall-e-3"
    image_size: str = "1024x1024"
    image_quality: str = "standard"
    api_key: str = ""
    # NovelAI-specific token (stored separately but surfaced via the same config)
    novelai_token: str = ""

    @classmethod
    def load(cls) -> "ImageRuntimeConfig":
        config = cls(
            provider=os.getenv("IMAGE_GEN_PROVIDER", "openai"),
            base_url=os.getenv("IMAGE_GEN_BASE_URL", "https://api.openai.com/v1"),
            image_model=os.getenv("IMAGE_GEN_MODEL", "dall-e-3"),
            image_size=os.getenv("IMAGE_GEN_SIZE", "1024x1024"),
            image_quality=os.getenv("IMAGE_GEN_QUALITY", "standard"),
            api_key=os.getenv("IMAGE_GEN_API_KEY", ""),
            novelai_token=os.getenv("NOVELAI_TOKEN", ""),
        )
        config.load_local()
        return config

    def update(self, payload: ImageConfigUpdate) -> None:
        self.provider = payload.provider
        self.base_url = normalize_base_url(payload.baseUrl)
        self.image_model = payload.imageModel.strip() or "dall-e-3"
        self.image_size = payload.imageSize.strip() or "1024x1024"
        self.image_quality = payload.imageQuality.strip() or "standard"
        if payload.clearApiKey:
            if self.provider == "novelai":
                self.novelai_token = ""
            else:
                self.api_key = ""
        elif payload.apiKey is not None and payload.apiKey.strip():
            if self.provider == "novelai":
                self.novelai_token = payload.apiKey.strip()
            else:
                self.api_key = payload.apiKey.strip()
        self.save_local()

    def load_local(self) -> None:
        if not IMAGE_CONFIG_PATH.exists():
            return
        data = json.loads(IMAGE_CONFIG_PATH.read_text(encoding="utf-8"))
        self.provider = data.get("provider", self.provider)
        self.base_url = normalize_base_url(data.get("baseUrl", self.base_url))
        self.image_model = data.get("imageModel", self.image_model)
        self.image_size = data.get("imageSize", self.image_size)
        self.image_quality = data.get("imageQuality", self.image_quality)
        self.api_key = data.get("apiKey", self.api_key)
        self.novelai_token = data.get("novelaiToken", self.novelai_token)

    def save_local(self) -> None:
        IMAGE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        IMAGE_CONFIG_PATH.write_text(
            json.dumps(
                {
                    "provider": self.provider,
                    "baseUrl": self.base_url,
                    "imageModel": self.image_model,
                    "imageSize": self.image_size,
                    "imageQuality": self.image_quality,
                    "apiKey": self.api_key,
                    "novelaiToken": self.novelai_token,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def is_available(self) -> bool:
        """Check if the configured provider has credentials."""
        if self.provider == "novelai":
            return bool(self.novelai_token)
        return bool(self.api_key)

    def public_response(self) -> ImageConfigResponse:
        return ImageConfigResponse(
            provider=self.provider,
            baseUrl=self.base_url,
            imageModel=self.image_model,
            imageSize=self.image_size,
            imageQuality=self.image_quality,
            hasApiKey=bool(self.novelai_token or self.api_key),
        )


def normalize_base_url(value: str) -> str:
    base_url = value.strip().rstrip("/")
    return base_url or "https://api.openai.com/v1"


llm_runtime_config = LlmRuntimeConfig.load()
image_runtime_config = ImageRuntimeConfig.load()
