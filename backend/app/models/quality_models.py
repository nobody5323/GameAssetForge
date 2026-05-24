from pydantic import BaseModel, Field


class QualityCheck(BaseModel):
    name: str = Field(..., examples=["file_format"])
    label: str = Field(..., examples=["文件格式"])
    passed: bool
    message: str = Field(..., examples=["文件为合法 PNG 格式"])
    score: int = Field(..., examples=[15])
    maxScore: int = Field(..., examples=[15])


class AssetQualityReport(BaseModel):
    assetId: str
    assetName: str
    assetType: str
    generationId: str
    checks: list[QualityCheck]
    totalScore: int
    maxScore: int


class GenerationQualityReport(BaseModel):
    generationId: str
    assets: list[AssetQualityReport]
    overallScore: int
    maxScore: int
    assetCount: int
    passCount: int
    failCount: int
