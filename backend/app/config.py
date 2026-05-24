import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from app.models.config_models import (
    CloudConfigResponse,
    CloudConfigUpdate,
    CloudProviderType,
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
CLOUD_CONFIG_PATH = BACKEND_ROOT / "runtime" / "cloud-config.local.json"


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
    """Image generation configuration for OpenAI image providers."""

    provider: ImageGenProvider = "openai"
    base_url: str = "https://api.openai.com/v1"
    image_model: str = "dall-e-3"
    image_size: str = "1024x1024"
    image_quality: str = "standard"
    api_key: str = ""
    proxy_url: str = ""

    @classmethod
    def load(cls) -> "ImageRuntimeConfig":
        config = cls(
            provider=os.getenv("IMAGE_GEN_PROVIDER", "openai"),
            base_url=os.getenv("IMAGE_GEN_BASE_URL", "https://api.openai.com/v1"),
            image_model=os.getenv("IMAGE_GEN_MODEL", "dall-e-3"),
            image_size=os.getenv("IMAGE_GEN_SIZE", "1024x1024"),
            image_quality=os.getenv("IMAGE_GEN_QUALITY", "standard"),
            api_key=os.getenv("IMAGE_GEN_API_KEY", ""),
            proxy_url=os.getenv("IMAGE_GEN_PROXY", ""),
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
            self.api_key = ""
        elif payload.apiKey is not None and payload.apiKey.strip():
            self.api_key = payload.apiKey.strip()
        if payload.clearProxy:
            self.proxy_url = ""
        elif payload.proxyUrl is not None:
            self.proxy_url = payload.proxyUrl.strip()
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
        self.proxy_url = data.get("proxyUrl", self.proxy_url)

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
                    "proxyUrl": self.proxy_url,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    def get_client_kwargs(self) -> dict:
        """Build httpx.Client keyword arguments including proxy."""
        kwargs = {"timeout": 120, "verify": True}
        if self.proxy_url:
            _validate_ascii_url(self.proxy_url, "HTTP 代理地址")
            kwargs["proxy"] = self.proxy_url
        return kwargs

    def public_response(self) -> ImageConfigResponse:
        return ImageConfigResponse(
            provider=self.provider,
            baseUrl=self.base_url,
            imageModel=self.image_model,
            imageSize=self.image_size,
            imageQuality=self.image_quality,
            hasApiKey=bool(self.api_key),
            proxyUrl=self.proxy_url or None,
        )


def normalize_base_url(value: str) -> str:
    base_url = value.strip().rstrip("/")
    return base_url or "https://api.openai.com/v1"


# ── Cloud Upload Runtime Config ──


@dataclass
class CloudRuntimeConfig:
    """Cloud upload configuration for Mock / Qiniu providers."""

    provider: CloudProviderType = "mock"
    access_key: str = ""
    secret_key: str = ""
    bucket: str = ""
    domain: str = ""

    @classmethod
    def load(cls) -> "CloudRuntimeConfig":
        config = cls(
            provider=os.getenv("CLOUD_PROVIDER", "mock"),
            access_key=os.getenv("QINIU_ACCESS_KEY", ""),
            secret_key=os.getenv("QINIU_SECRET_KEY", ""),
            bucket=os.getenv("QINIU_BUCKET", ""),
            domain=os.getenv("QINIU_DOMAIN", ""),
        )
        config.load_local()
        return config

    def update(self, payload: CloudConfigUpdate) -> None:
        self.provider = payload.provider
        if payload.clearCredentials:
            self.access_key = ""
            self.secret_key = ""
            self.bucket = ""
            self.domain = ""
        else:
            if payload.accessKey is not None and payload.accessKey.strip():
                self.access_key = payload.accessKey.strip()
            if payload.secretKey is not None and payload.secretKey.strip():
                self.secret_key = payload.secretKey.strip()
            if payload.bucket is not None:
                self.bucket = payload.bucket.strip()
            if payload.domain is not None:
                self.domain = payload.domain.strip()
        self.save_local()

    def load_local(self) -> None:
        if not CLOUD_CONFIG_PATH.exists():
            return
        data = json.loads(CLOUD_CONFIG_PATH.read_text(encoding="utf-8"))
        self.provider = data.get("provider", self.provider)
        self.access_key = data.get("accessKey", self.access_key)
        self.secret_key = data.get("secretKey", self.secret_key)
        self.bucket = data.get("bucket", self.bucket)
        self.domain = data.get("domain", self.domain)

    def save_local(self) -> None:
        CLOUD_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CLOUD_CONFIG_PATH.write_text(
            json.dumps(
                {
                    "provider": self.provider,
                    "accessKey": self.access_key,
                    "secretKey": self.secret_key,
                    "bucket": self.bucket,
                    "domain": self.domain,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def is_qiniu_available(self) -> bool:
        return bool(self.access_key and self.secret_key and self.bucket)

    def public_response(self) -> CloudConfigResponse:
        return CloudConfigResponse(
            provider=self.provider,
            hasCredentials=self.is_qiniu_available(),
            bucket=self.bucket or None,
            domain=self.domain or None,
        )


def _validate_ascii_url(value: str, label: str) -> None:
    """Raise a clear error if `value` contains non-ASCII characters."""
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise RuntimeError(
            f"{label}（{value!r}）包含非 ASCII 字符（位置 {exc.start}-{exc.end}），"
            f"URL 只支持英文、数字和符号。请检查 Image API 配置页面。"
        ) from None


llm_runtime_config = LlmRuntimeConfig.load()
image_runtime_config = ImageRuntimeConfig.load()
cloud_runtime_config = CloudRuntimeConfig.load()
