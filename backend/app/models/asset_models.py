from pydantic import BaseModel, Field

from app.models.prompt_models import PromptMode, TargetModel


class ImageGenerationRequest(BaseModel):
    generationId: str = Field(..., examples=["gen_demo_001"])
    assetName: str = Field(..., examples=["bamboo_slime"])
    assetType: str = Field(..., examples=["enemy"])
    style: str = Field(..., examples=["pixel_art"])
    theme: str = Field(..., examples=["cyber bamboo forest"])
    finalPrompt: str
    negativePrompt: str | None = None
    promptVersion: str = "prompt-v1"


class GeneratedImage(BaseModel):
    assetName: str
    assetType: str
    localPath: str
    provider: str
    metadata: dict[str, str | int | bool]


class AssetGenerateItem(BaseModel):
    type: str = Field(..., examples=["enemy"])
    name: str = Field(..., examples=["bamboo_slime"])
    description: str = Field(..., examples=["a small glowing slime monster"])


class AssetGenerateRequest(BaseModel):
    projectName: str
    gameType: str
    style: str
    theme: str
    description: str
    targetModel: TargetModel = "mock_seed"
    promptMode: PromptMode = "normal"
    assets: list[AssetGenerateItem]


class AssetRecord(BaseModel):
    id: str
    generationId: str
    projectName: str = ""
    assetName: str
    assetType: str
    style: str
    theme: str
    finalPrompt: str
    promptVersion: str
    localPath: str
    cloudUrl: str | None = None
    qualityScore: int | None = None
    provider: str
    providerMetadata: dict[str, str | int | bool]
    parentAssetId: str | None = None


class AssetGenerateResponse(BaseModel):
    generationId: str
    provider: str
    promptProvider: str
    fallback: bool
    assets: list[AssetRecord]


class SecondaryGenerationRequest(BaseModel):
    action: str = Field(..., examples=["move"])
    customPrompt: str | None = Field(default=None, examples=["make it more dynamic, add motion blur"])


class BatchRegenerateRequest(BaseModel):
    assetId: str = Field(..., examples=["asset_abc123"])
    actions: list[str] = Field(..., examples=[["move", "attack"]])
    customPrompt: str | None = Field(default=None, examples=["add fire effects"])
