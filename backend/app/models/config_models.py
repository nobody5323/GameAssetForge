from typing import Literal

from pydantic import BaseModel


PromptProvider = Literal["openai", "rule_fallback"]


class LlmConfigUpdate(BaseModel):
    provider: PromptProvider = "openai"
    baseUrl: str = "https://api.openai.com/v1"
    promptModel: str = "gpt-5-mini"
    apiKey: str | None = None
    clearApiKey: bool = False


class LlmConfigResponse(BaseModel):
    provider: PromptProvider
    baseUrl: str
    promptModel: str
    hasApiKey: bool
