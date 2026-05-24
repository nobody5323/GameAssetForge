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


# ── Image Generation Config ──

ImageGenProvider = Literal["openai", "novelai"]


class ImageConfigUpdate(BaseModel):
    provider: ImageGenProvider = "openai"
    baseUrl: str = "https://api.openai.com/v1"
    imageModel: str = "dall-e-3"
    imageSize: str = "1024x1024"
    imageQuality: str = "standard"
    apiKey: str | None = None
    clearApiKey: bool = False


class ImageConfigResponse(BaseModel):
    provider: ImageGenProvider
    baseUrl: str
    imageModel: str
    imageSize: str
    imageQuality: str
    hasApiKey: bool
