import os
from dataclasses import dataclass

from app.models.config_models import LlmConfigResponse, LlmConfigUpdate, PromptProvider


@dataclass
class LlmRuntimeConfig:
    provider: PromptProvider
    base_url: str
    prompt_model: str
    api_key: str

    @classmethod
    def from_environment(cls) -> "LlmRuntimeConfig":
        return cls(
            provider=os.getenv("PROMPT_PROVIDER", "openai"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            prompt_model=os.getenv("OPENAI_PROMPT_MODEL", "gpt-5-mini"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )

    def update(self, payload: LlmConfigUpdate) -> None:
        self.provider = payload.provider
        self.base_url = normalize_base_url(payload.baseUrl)
        self.prompt_model = payload.promptModel.strip() or "gpt-5-mini"
        if payload.clearApiKey:
            self.api_key = ""
        elif payload.apiKey is not None and payload.apiKey.strip():
            self.api_key = payload.apiKey.strip()

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


llm_runtime_config = LlmRuntimeConfig.from_environment()
