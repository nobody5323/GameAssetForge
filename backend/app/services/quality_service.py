import re
import struct
from pathlib import Path

from app.models.asset_models import AssetRecord
from app.models.quality_models import AssetQualityReport, GenerationQualityReport, QualityCheck
from app.repositories.asset_repository import AssetRepository

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class QualityService:
    def __init__(self, repository: AssetRepository | None = None) -> None:
        self._repository = repository or AssetRepository()

    def inspect_asset(self, asset_id: str) -> AssetQualityReport:
        asset = self._find_asset(asset_id)
        checks = [
            self._check_file_format(asset),
            self._check_image_dimensions(asset),
            self._check_naming_convention(asset),
            self._check_category_directory(asset),
            self._check_prompt_record(asset),
            self._check_manifest_readiness(asset),
            self._check_cloud_readiness(asset),
        ]
        total = sum(check.score for check in checks)
        maximum = sum(check.maxScore for check in checks)
        return AssetQualityReport(
            assetId=asset.id,
            assetName=asset.assetName,
            assetType=asset.assetType,
            generationId=asset.generationId,
            checks=checks,
            totalScore=total,
            maxScore=maximum,
        )

    def inspect_generation(self, generation_id: str) -> GenerationQualityReport:
        all_assets = self._repository.list_assets()
        gen_assets = [a for a in all_assets if a.generationId == generation_id]
        if not gen_assets:
            return GenerationQualityReport(
                generationId=generation_id,
                assets=[],
                overallScore=0,
                maxScore=100,
                assetCount=0,
                passCount=0,
                failCount=0,
            )

        reports = [self.inspect_asset(a.id) for a in gen_assets]
        overall = (
            sum(r.totalScore for r in reports) // len(reports) if reports else 0
        )
        pass_count = sum(1 for r in reports if r.totalScore >= 60)
        fail_count = len(reports) - pass_count
        return GenerationQualityReport(
            generationId=generation_id,
            assets=reports,
            overallScore=overall,
            maxScore=100,
            assetCount=len(reports),
            passCount=pass_count,
            failCount=fail_count,
        )

    # ── individual checks ──────────────────────────────────────────

    def _check_file_format(self, asset: AssetRecord) -> QualityCheck:
        max_score = 15
        file_path = BACKEND_ROOT / asset.localPath
        if not file_path.exists():
            return QualityCheck(
                name="file_format",
                label="文件格式",
                passed=False,
                message=f"文件不存在：{asset.localPath}",
                score=0,
                maxScore=max_score,
            )
        try:
            header = file_path.read_bytes()[:8]
        except OSError as exc:
            return QualityCheck(
                name="file_format",
                label="文件格式",
                passed=False,
                message=f"无法读取文件：{exc}",
                score=0,
                maxScore=max_score,
            )
        if header == PNG_SIGNATURE:
            return QualityCheck(
                name="file_format",
                label="文件格式",
                passed=True,
                message="文件为合法 PNG 格式",
                score=max_score,
                maxScore=max_score,
            )
        return QualityCheck(
            name="file_format",
            label="文件格式",
            passed=False,
            message="文件不是有效的 PNG（签名不匹配）",
            score=0,
            maxScore=max_score,
        )

    def _check_image_dimensions(self, asset: AssetRecord) -> QualityCheck:
        max_score = 15
        file_path = BACKEND_ROOT / asset.localPath
        if not file_path.exists():
            return QualityCheck(
                name="image_dimensions",
                label="图片尺寸",
                passed=False,
                message="文件不存在，无法读取尺寸",
                score=0,
                maxScore=max_score,
            )
        try:
            width, height = _read_png_dimensions(file_path)
        except (OSError, ValueError, struct.error) as exc:
            return QualityCheck(
                name="image_dimensions",
                label="图片尺寸",
                passed=False,
                message=f"无法解析图片尺寸：{exc}",
                score=0,
                maxScore=max_score,
            )

        if width is None or height is None:
            return QualityCheck(
                name="image_dimensions",
                label="图片尺寸",
                passed=False,
                message="无法从 IHDR 读取尺寸信息",
                score=0,
                maxScore=max_score,
            )

        min_dim, max_dim = 16, 4096
        if min_dim <= width <= max_dim and min_dim <= height <= max_dim:
            return QualityCheck(
                name="image_dimensions",
                label="图片尺寸",
                passed=True,
                message=f"尺寸 {width}x{height}，在合理范围内 ({min_dim}–{max_dim})",
                score=max_score,
                maxScore=max_score,
            )

        deduction = 5 if width > max_dim or height > max_dim else 5
        return QualityCheck(
            name="image_dimensions",
            label="图片尺寸",
            passed=False,
            message=f"尺寸 {width}x{height} 超出合理范围 ({min_dim}–{max_dim})",
            score=max(0, max_score - deduction),
            maxScore=max_score,
        )

    def _check_naming_convention(self, asset: AssetRecord) -> QualityCheck:
        max_score = 10
        name = asset.assetName
        if not name:
            return QualityCheck(
                name="naming_convention",
                label="命名规范",
                passed=False,
                message="素材名称为空",
                score=0,
                maxScore=max_score,
            )

        issues = []
        if " " in name:
            issues.append("名称中包含空格")
        if re.search(r"[A-Z]", name):
            issues.append("名称中包含大写字母")
        if re.search(r"[^a-z0-9_]", name):
            issues.append("名称中包含特殊字符")

        if not issues:
            return QualityCheck(
                name="naming_convention",
                label="命名规范",
                passed=True,
                message=f"命名 '{name}' 符合 snake_case 规范",
                score=max_score,
                maxScore=max_score,
            )

        return QualityCheck(
            name="naming_convention",
            label="命名规范",
            passed=False,
            message="；".join(issues),
            score=max(0, max_score - len(issues) * 3),
            maxScore=max_score,
        )

    def _check_category_directory(self, asset: AssetRecord) -> QualityCheck:
        max_score = 15
        path = asset.localPath
        expected_segment = f"/{asset.assetType}/"
        if expected_segment in path:
            return QualityCheck(
                name="category_directory",
                label="分类目录",
                passed=True,
                message=f"路径包含正确的类型目录 '{asset.assetType}'",
                score=max_score,
                maxScore=max_score,
            )
        return QualityCheck(
            name="category_directory",
            label="分类目录",
            passed=False,
            message=f"路径中未找到类型目录 '{asset.assetType}'，当前路径：{path}",
            score=0,
            maxScore=max_score,
        )

    def _check_prompt_record(self, asset: AssetRecord) -> QualityCheck:
        max_score = 15
        prompt = asset.finalPrompt
        if not prompt:
            return QualityCheck(
                name="prompt_record",
                label="Prompt 记录",
                passed=False,
                message="finalPrompt 为空",
                score=0,
                maxScore=max_score,
            )
        if len(prompt) < 20:
            return QualityCheck(
                name="prompt_record",
                label="Prompt 记录",
                passed=False,
                message=f"finalPrompt 过短（{len(prompt)} 字符），应 >= 20 字符",
                score=5,
                maxScore=max_score,
            )
        return QualityCheck(
            name="prompt_record",
            label="Prompt 记录",
            passed=True,
            message=f"finalPrompt 记录完整（{len(prompt)} 字符）",
            score=max_score,
            maxScore=max_score,
        )

    def _check_manifest_readiness(self, asset: AssetRecord) -> QualityCheck:
        max_score = 15
        required_fields = {
            "id": asset.id,
            "assetName": asset.assetName,
            "assetType": asset.assetType,
            "localPath": asset.localPath,
        }
        missing = [k for k, v in required_fields.items() if not v]
        if not missing:
            return QualityCheck(
                name="manifest_readiness",
                label="Manifest 就绪",
                passed=True,
                message="所有必填字段已填充，可用于导出 manifest",
                score=max_score,
                maxScore=max_score,
            )
        return QualityCheck(
            name="manifest_readiness",
            label="Manifest 就绪",
            passed=False,
            message=f"缺少必填字段：{', '.join(missing)}",
            score=max(0, max_score - len(missing) * 5),
            maxScore=max_score,
        )

    def _check_cloud_readiness(self, asset: AssetRecord) -> QualityCheck:
        max_score = 15
        if asset.cloudUrl:
            return QualityCheck(
                name="cloud_readiness",
                label="云端就绪",
                passed=True,
                message=f"云端 URL 已配置：{asset.cloudUrl}",
                score=max_score,
                maxScore=max_score,
            )
        return QualityCheck(
            name="cloud_readiness",
            label="云端就绪",
            passed=False,
            message="cloudUrl 未设置（PR12 将接入云端上传）",
            score=0,
            maxScore=15,
        )

    # ── helpers ─────────────────────────────────────────────────────

    def _find_asset(self, asset_id: str) -> AssetRecord:
        all_assets = self._repository.list_assets()
        for asset in all_assets:
            if asset.id == asset_id:
                return asset
        raise ValueError(f"未找到素材：{asset_id}")


def _read_png_dimensions(path: Path) -> tuple[int | None, int | None]:
    """从 PNG IHDR chunk 读取宽高，不依赖 Pillow。"""
    data = path.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("不是有效的 PNG 文件")
    # IHDR 总是第一个 chunk，位于签名后 8 字节
    # chunk: 4-byte length, 4-byte type, data, 4-byte CRC
    pos = 8
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        if chunk_type == b"IHDR":
            ihdr = data[pos + 8 : pos + 8 + length]
            width, height = struct.unpack(">II", ihdr[:8])
            return width, height
        pos += 12 + length
    return None, None
