from typing import Literal

from pydantic import BaseModel, Field

PromptMode = Literal["normal", "professional"]
TargetModel = Literal["gpt_image", "mock_seed"]
PromptDirection = Literal["quick_start", "production_safe", "style_exploration", "high_detail"]


class PromptAssetRequest(BaseModel):
    type: str = Field(..., examples=["enemy"])
    name: str = Field(..., examples=["bamboo_slime"])
    description: str = Field(..., examples=["a small glowing slime monster"])


class PromptCompileRequest(BaseModel):
    mode: PromptMode = "normal"
    targetModel: TargetModel = "gpt_image"
    projectName: str
    gameType: str
    style: str
    theme: str
    description: str
    assets: list[PromptAssetRequest]


class PromptAssetResult(BaseModel):
    assetName: str
    assetType: str
    finalPrompt: str
    negativePrompt: str | None = None


class PromptCandidate(BaseModel):
    id: str
    direction: PromptDirection
    score: int
    tags: dict[str, list[str]]
    assets: list[PromptAssetResult]
    warnings: list[str] = []


class PromptCompileResponse(BaseModel):
    mode: PromptMode
    targetModel: TargetModel
    provider: str
    fallback: bool
    threshold: int
    candidates: list[PromptCandidate]
