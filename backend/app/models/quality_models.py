"""质量检测数据模型：6 个维度的加权百分比评分。"""

from pydantic import BaseModel, Field


class QualitySubCheck(BaseModel):
    """质量维度下的单个检查点。"""

    name: str = Field(..., examples=["png_signature"], description="检查点标识")
    label: str = Field(..., examples=["PNG 文件头有效"], description="检查点中文名称")
    passed: bool = Field(..., description="是否通过")
    message: str = Field(..., description="检查结果说明")
    deductionPct: int = Field(..., examples=[20], description="未通过时在本维度内扣除的百分比")
    weightHint: str = Field(default="", description="该检查点在所属维度内的权重说明")
    optimizationHint: str = Field(default="", description="不通过时给用户的提示词或素材优化建议")


class QualityDimension(BaseModel):
    """单个质量维度，包含维度权重和子检查点列表。"""

    name: str = Field(..., examples=["dimensions"], description="质量维度标识")
    label: str = Field(..., examples=["图片尺寸"], description="展示给用户的维度名称")
    weightPct: int = Field(..., examples=[20], description="该维度在总分中的权重百分比")
    subChecks: list[QualitySubCheck] = Field(default_factory=list, description="该维度下的具体检查点")
    dimensionScore: int = Field(default=100, description="该维度得分，范围 0-100")
    weightedScore: float = Field(default=0.0, description="该维度按权重折算后的得分")
    passed: bool = Field(default=True, description="该维度是否达到可接受标准")
    passedCount: int = Field(default=0, description="通过的检查点数量")
    totalCount: int = Field(default=0, description="检查点总数")


class AssetQualityReport(BaseModel):
    """单个素材的质量报告。"""

    assetId: str
    assetName: str
    assetType: str
    generationId: str
    dimensions: list[QualityDimension] = Field(default_factory=list, description="6 个质量维度")
    totalScore: int = Field(..., description="加权综合得分，范围 0-100")
    maxScore: int = Field(default=100, description="满分，固定为 100")
    grade: str = Field(..., description="综合质量等级")
    overallHint: str = Field(default="", description="综合优化建议")
    promptOptimizationTips: list[str] = Field(default_factory=list, description="可执行的提示词优化建议")


class GenerationQualityReport(BaseModel):
    """单次生成任务的质量汇总报告。"""

    generationId: str
    assets: list[AssetQualityReport] = Field(default_factory=list)
    overallScore: int = Field(default=0, description="所有素材综合得分的平均值")
    maxScore: int = Field(default=100, description="满分，固定为 100")
    assetCount: int = 0
    passCount: int = Field(default=0, description="得分大于等于 60 的素材数量")
    failCount: int = Field(default=0, description="得分低于 60 的素材数量")
    gradeA: int = Field(default=0, description="A 级素材数量")
    gradeB: int = Field(default=0, description="B 级素材数量")
    gradeC: int = Field(default=0, description="C 级素材数量")
    gradeD: int = Field(default=0, description="D 级素材数量")
    gradeF: int = Field(default=0, description="F 级素材数量")
