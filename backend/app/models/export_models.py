"""导出相关数据模型 — Manifest、ExportRequest、ExportResponse。"""

from datetime import datetime

from pydantic import BaseModel, Field


class ManifestAsset(BaseModel):
    """manifest.json 中单个素材条目。"""

    id: str = Field(..., description="素材唯一标识")
    assetName: str = Field(..., description="素材名称")
    assetType: str = Field(..., description="素材类型")
    style: str = Field(..., description="视觉风格")
    theme: str = Field(..., description="主题")
    finalPrompt: str = Field(..., description="最终提示词")
    localPath: str = Field(..., description="素材在 zip 内的相对路径")
    provider: str = Field(..., description="生成 provider")
    qualityScore: int | None = Field(default=None, description="质量评分（如有）")


class Manifest(BaseModel):
    """导出包的 manifest 元数据清单。"""

    generationId: str = Field(..., description="所属 generation ID")
    projectName: str = Field(default="unknown", description="项目名称")
    exportedAt: str = Field(..., description="导出时间 ISO 8601")
    assetCount: int = Field(..., description="素材总数")
    assets: list[ManifestAsset] = Field(default_factory=list, description="素材条目列表")


class ExportResponse(BaseModel):
    """导出结果响应。"""

    generationId: str
    zipFileName: str
    assetCount: int
    manifestSize: int = Field(..., description="manifest.json 字节数")
    totalSize: int = Field(..., description="zip 文件总字节数")


class ExportSelectedRequest(BaseModel):
    """按素材 ID 列表导出。"""

    assetIds: list[str] = Field(..., min_length=1, examples=[["asset_abc123", "asset_def456"]])
