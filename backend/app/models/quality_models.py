from pydantic import BaseModel, Field


class QualityCriterion(BaseModel):
    """加权质量维度中的单个具体检查点。"""

    label: str = Field(..., examples=["PNG 文件头有效"])
    passed: bool = Field(..., description="该检查点是否通过")
    deduction: int = Field(..., examples=[10], description="未通过时扣除的分数")
    message: str = Field(..., description="检查点结果说明")
    suggestion: str | None = Field(default=None, description="提示词优化建议")


class QualityCheck(BaseModel):
    """单个加权图片质量维度。"""

    name: str = Field(..., examples=["dimensions"], description="质量维度标识")
    label: str = Field(..., examples=["尺寸规格"], description="展示给用户的维度名称")
    passed: bool = Field(..., description="该维度是否达到可接受标准")
    message: str = Field(..., description="维度结果摘要")
    score: int = Field(..., examples=[86], description="维度得分，范围 0-100")
    maxScore: int = Field(default=100, description="维度满分，固定为 100")
    weight: int = Field(..., examples=[20], description="维度权重百分比")
    weightedScore: int = Field(..., examples=[17], description="按权重折算后的得分")
    grade: str = Field(..., examples=["A"], description="维度质量等级")
    suggestions: list[str] = Field(default_factory=list, description="提示词优化建议")
    criteria: list[QualityCriterion] = Field(
        default_factory=list,
        description="该维度下实际评估的具体检查点",
    )


class AssetQualityReport(BaseModel):
    """单个生成图片素材的质量报告。"""

    assetId: str
    assetName: str
    assetType: str
    generationId: str
    checks: list[QualityCheck]
    totalScore: int = Field(..., description="加权综合得分，范围 0-100")
    maxScore: int = Field(..., description="综合满分，固定为 100")
    qualityGrade: str = Field(..., description="总体质量等级")
    promptOptimizationTips: list[str] = Field(
        default_factory=list,
        description="根据薄弱维度生成的可执行提示词优化建议",
    )


class GenerationQualityReport(BaseModel):
    """单次生成任务的质量汇总。"""

    generationId: str
    assets: list[AssetQualityReport]
    overallScore: int = Field(..., description="素材平均质量得分")
    maxScore: int = Field(..., description="满分，固定为 100")
    assetCount: int
    passCount: int = Field(..., description="得分大于等于 60 的素材数量")
    failCount: int = Field(..., description="得分低于 60 的素材数量")
