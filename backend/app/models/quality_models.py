from pydantic import BaseModel, Field


class QualityCheck(BaseModel):
    """单项质量检查结果（扣分制：score=扣分, maxScore=该项最多可扣分, passed=True表示无扣分）"""

    name: str = Field(..., examples=["dimensions"], description="检查项标识名")
    label: str = Field(..., examples=["尺寸规格"], description="检查项中文标签")
    passed: bool = Field(..., description="是否通过（扣分为 0 即为通过）")
    message: str = Field(..., examples=["尺寸 64x64 偏小（<128px），建议 ≥256px"], description="检查详情或扣分原因")
    score: int = Field(..., examples=[25], description="该项实际扣分（0 = 无扣分，越大越差）")
    maxScore: int = Field(..., examples=[30], description="该项最多可扣分数")


class AssetQualityReport(BaseModel):
    """单个素材的质量报告"""

    assetId: str
    assetName: str
    assetType: str
    generationId: str
    checks: list[QualityCheck]
    totalScore: int = Field(..., description="最终得分（100 - 总扣分，下限 0）")
    maxScore: int = Field(..., description="满分（固定 100）")


class GenerationQualityReport(BaseModel):
    """整个 generation 的质量汇总报告"""

    generationId: str
    assets: list[AssetQualityReport]
    overallScore: int = Field(..., description="所有素材得分的平均值")
    maxScore: int = Field(..., description="满分（固定 100）")
    assetCount: int
    passCount: int = Field(..., description="得分 ≥ 60 的素材数")
    failCount: int = Field(..., description="得分 < 60 的素材数")
