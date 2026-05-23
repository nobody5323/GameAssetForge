import json
import os
from dataclasses import dataclass
from pathlib import Path

from app.models.config_models import LlmConfigResponse, LlmConfigUpdate, PromptProvider

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG_PATH = BACKEND_ROOT / "runtime" / "llm-config.local.json"


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


def normalize_base_url(value: str) -> str:
    base_url = value.strip().rstrip("/")
    return base_url or "https://api.openai.com/v1"


llm_runtime_config = LlmRuntimeConfig.load()
