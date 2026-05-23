from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):
    generationId: str = Field(..., examples=["gen_demo_001"])
    assetName: str = Field(..., examples=["bamboo_slime"])
    assetType: str = Field(..., examples=["enemy"])
    style: str = Field(..., examples=["pixel_art"])
    theme: str = Field(..., examples=["cyber bamboo forest"])
    finalPrompt: str
    promptVersion: str = "prompt-v1"


class GeneratedImage(BaseModel):
    assetName: str
    assetType: str
    localPath: str
    provider: str
    metadata: dict[str, str | int | bool]
