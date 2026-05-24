import re
import struct
from pathlib import Path

from app.models.asset_models import AssetRecord
from app.models.quality_models import AssetQualityReport, GenerationQualityReport, QualityCheck
from app.repositories.asset_repository import AssetRepository

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# ── 扣分制常量 ─────────────────────────────────────────────────────
# 满分 100，每项检查返回扣分数（0 = 无扣分）
# 设计参考：T2I-CompBench（属性绑定/对象关系）、GenEval（对象存在/颜色/位置）、
# Intel CGVQM（游戏画面实时质量度量）

FULL_SCORE = 100
PASS_THRESHOLD = 60


class QualityService:
    """质量检查服务 — 扣分制。

    满分 100，逐项检查并扣分。扣分越少质量越高。
    参考图像质量评估研究设计差异化扣分维度。
    """

    def __init__(self, repository: AssetRepository | None = None) -> None:
        self._repository = repository or AssetRepository()

    def inspect_asset(self, asset_id: str) -> AssetQualityReport:
        asset = self._find_asset(asset_id)

        # 致命检查：非 PNG 直接归零
        fatal = self._check_png_fatal(asset)
        if fatal is not None:
            return AssetQualityReport(
                assetId=asset.id,
                assetName=asset.assetName,
                assetType=asset.assetType,
                generationId=asset.generationId,
                checks=[fatal],
                totalScore=0,
                maxScore=FULL_SCORE,
            )

        checks = [
            self._check_dimensions(asset),
            self._check_naming(asset),
            self._check_directory(asset),
            self._check_prompt_quality(asset),
            self._check_metadata(asset),
            self._check_delivery(asset),
        ]

        total_deduction = sum(c.score for c in checks)
        final = max(0, FULL_SCORE - total_deduction)

        return AssetQualityReport(
            assetId=asset.id,
            assetName=asset.assetName,
            assetType=asset.assetType,
            generationId=asset.generationId,
            checks=checks,
            totalScore=final,
            maxScore=FULL_SCORE,
        )

    def inspect_generation(self, generation_id: str) -> GenerationQualityReport:
        all_assets = self._repository.list_assets()
        gen_assets = [a for a in all_assets if a.generationId == generation_id]
        if not gen_assets:
            return GenerationQualityReport(
                generationId=generation_id,
                assets=[],
                overallScore=0,
                maxScore=FULL_SCORE,
                assetCount=0,
                passCount=0,
                failCount=0,
            )

        reports = [self.inspect_asset(a.id) for a in gen_assets]
        overall = (
            sum(r.totalScore for r in reports) // len(reports) if reports else 0
        )
        pass_count = sum(1 for r in reports if r.totalScore >= PASS_THRESHOLD)
        fail_count = len(reports) - pass_count

        return GenerationQualityReport(
            generationId=generation_id,
            assets=reports,
            overallScore=overall,
            maxScore=FULL_SCORE,
            assetCount=len(reports),
            passCount=pass_count,
            failCount=fail_count,
        )

    # ── 致命检查：PNG 合规 ──────────────────────────────────────────

    def _check_png_fatal(self, asset: AssetRecord) -> QualityCheck | None:
        """PNG 致命检查——不是有效 PNG 则直接 0 分，不再检查其他项。"""
        max_deduction = FULL_SCORE
        file_path = BACKEND_ROOT / asset.localPath

        if not file_path.exists():
            return QualityCheck(
                name="png_fatal",
                label="PNG 合规（致命）",
                passed=False,
                message=f"文件不存在：{asset.localPath}",
                score=max_deduction,
                maxScore=max_deduction,
            )

        try:
            data = file_path.read_bytes()
        except OSError as exc:
            return QualityCheck(
                name="png_fatal",
                label="PNG 合规（致命）",
                passed=False,
                message=f"无法读取文件：{exc}",
                score=max_deduction,
                maxScore=max_deduction,
            )

        if data[:8] != PNG_SIGNATURE:
            return QualityCheck(
                name="png_fatal",
                label="PNG 合规（致命）",
                passed=False,
                message="文件不是有效的 PNG（签名不匹配），无法继续检查",
                score=max_deduction,
                maxScore=max_deduction,
            )

        # 极小文件可能损坏（< 70 bytes 连最小 PNG header 都凑不齐）
        if len(data) < 70:
            return QualityCheck(
                name="png_fatal",
                label="PNG 合规（致命）",
                passed=False,
                message=f"PNG 文件极小（{len(data)} bytes），可能已损坏",
                score=max_deduction,
                maxScore=max_deduction,
            )

        return None  # 通过致命检查

    # ── 尺寸规格检查（最多扣 30）──────────────────────────────────
    # 参考 Intel CGVQM 对分辨率敏感度的研究，以及游戏资产对
    # GPU 纹理友好尺寸（2 的幂、16 对齐）的要求。

    def _check_dimensions(self, asset: AssetRecord) -> QualityCheck:
        max_deduction = 30
        file_path = BACKEND_ROOT / asset.localPath

        try:
            width, height = _read_png_dimensions(file_path)
        except (OSError, ValueError, struct.error) as exc:
            return QualityCheck(
                name="dimensions",
                label="尺寸规格",
                passed=False,
                message=f"无法解析图片尺寸：{exc}",
                score=max_deduction,
                maxScore=max_deduction,
            )

        if width is None or height is None:
            return QualityCheck(
                name="dimensions",
                label="尺寸规格",
                passed=False,
                message="无法从 IHDR chunk 读取尺寸信息",
                score=max_deduction,
                maxScore=max_deduction,
            )

        deductions = []
        detail_parts = []
        min_side = min(width, height)
        max_side = max(width, height)

        # 尺寸分级扣分（游戏资产建议 ≥256px）
        if min_side < 64:
            deductions.append(30)
            detail_parts.append(f"尺寸 {width}x{height} 过小（<64px），不满足游戏资产最低要求")
        elif min_side < 128:
            deductions.append(25)
            detail_parts.append(f"尺寸 {width}x{height} 偏小（<128px），建议 ≥256px")
        elif min_side < 256:
            deductions.append(18)
            detail_parts.append(f"尺寸 {width}x{height} 略小（<256px），生产建议 ≥256px")

        # 过大扣分
        if max_side > 4096:
            deductions.append(20)
            detail_parts.append(f"尺寸超过 4096px，浪费显存和存储")

        # GPU 纹理友好度：2 的幂
        if not (_is_power_of_two(width) and _is_power_of_two(height)):
            deductions.append(10)
            detail_parts.append("非 2 的幂次方尺寸，GPU 纹理采样效率降低")

        # Tile-map 对齐：16 的倍数
        if width % 16 != 0 or height % 16 != 0:
            deductions.append(5)
            detail_parts.append("尺寸不是 16 的倍数，tile-map 拼接可能不对齐")

        # Mock 纯色图检测
        if _is_solid_color_png(file_path):
            deductions.append(15)
            detail_parts.append("检测为纯色填充图（mock 占位素材），非真实生成结果")

        total = min(sum(deductions), max_deduction)

        if total == 0:
            return QualityCheck(
                name="dimensions",
                label="尺寸规格",
                passed=True,
                message=f"尺寸 {width}x{height}，符合生产规范",
                score=0,
                maxScore=max_deduction,
            )

        return QualityCheck(
            name="dimensions",
            label="尺寸规格",
            passed=False,
            message="；".join(detail_parts),
            score=total,
            maxScore=max_deduction,
        )

    # ── 命名规范检查（最多扣 20）──────────────────────────────────

    def _check_naming(self, asset: AssetRecord) -> QualityCheck:
        max_deduction = 20
        name = asset.assetName
        deductions = []
        issues = []

        if not name:
            return QualityCheck(
                name="naming",
                label="命名规范",
                passed=False,
                message="素材名称为空",
                score=max_deduction,
                maxScore=max_deduction,
            )

        if " " in name:
            deductions.append(8)
            issues.append("含空格")

        if re.search(r"[A-Z]", name):
            deductions.append(5)
            issues.append("含大写字母")

        if re.search(r"[^a-z0-9_]", name):
            deductions.append(10)
            issues.append("含特殊字符（仅允许 a-z、0-9、_）")

        if re.match(r"^\d", name):
            deductions.append(3)
            issues.append("以数字开头")

        if len(name) > 40:
            deductions.append(3)
            issues.append(f"名称过长（{len(name)} 字符，建议 ≤40）")

        total = min(sum(deductions), max_deduction)
        if total == 0:
            return QualityCheck(
                name="naming",
                label="命名规范",
                passed=True,
                message=f"'{name}' 符合 snake_case 规范",
                score=0,
                maxScore=max_deduction,
            )

        return QualityCheck(
            name="naming",
            label="命名规范",
            passed=False,
            message="；".join(issues),
            score=total,
            maxScore=max_deduction,
        )

    # ── 目录分类检查（最多扣 20）──────────────────────────────────

    def _check_directory(self, asset: AssetRecord) -> QualityCheck:
        max_deduction = 20
        path = asset.localPath
        deductions = []
        issues = []

        expected_segment = f"/{asset.assetType}/"
        if expected_segment not in path:
            deductions.append(20)
            issues.append(f"路径缺少类型目录 '{asset.assetType}'")

        # 检查路径深度
        parts = Path(path).parts
        if len(parts) < 4:
            deductions.append(10)
            issues.append(f"路径层级过浅（{len(parts)} 层），建议 generation/type/name 结构")

        total = min(sum(deductions), max_deduction)
        if total == 0:
            return QualityCheck(
                name="directory",
                label="目录分类",
                passed=True,
                message=f"路径结构正确：{path}",
                score=0,
                maxScore=max_deduction,
            )

        return QualityCheck(
            name="directory",
            label="目录分类",
            passed=False,
            message="；".join(issues),
            score=total,
            maxScore=max_deduction,
        )

    # ── Prompt 质量检查（最多扣 25）───────────────────────────────
    # 参考 T2I-CompBench 属性绑定评估、GenEval 对象/颜色对齐

    def _check_prompt_quality(self, asset: AssetRecord) -> QualityCheck:
        max_deduction = 25
        prompt = asset.finalPrompt or ""
        deductions = []
        issues = []

        if not prompt:
            return QualityCheck(
                name="prompt_quality",
                label="Prompt 质量",
                passed=False,
                message="finalPrompt 为空，无任何提示词记录",
                score=max_deduction,
                maxScore=max_deduction,
            )

        char_count = len(prompt)
        if char_count < 20:
            deductions.append(25)
            issues.append(f"提示词极短（{char_count} 字符），无法描述素材特征")
        elif char_count < 50:
            deductions.append(15)
            issues.append(f"提示词偏短（{char_count} 字符），可能缺少细节描述")
        elif char_count < 100:
            deductions.append(8)
            issues.append(f"提示词略短（{char_count} 字符），建议补充风格和构图描述")

        prompt_lower = prompt.lower()
        style_keywords = ["pixel", "style", "art", "game", "sprite", "2d", "cartoon",
                          "cyberpunk", "fantasy", "dark", "retro", "anime"]
        has_style = any(kw in prompt_lower for kw in style_keywords)
        if not has_style:
            deductions.append(8)
            issues.append("缺少风格关键词（如 pixel_art、game sprite 等）")

        if asset.assetName.lower() not in prompt_lower:
            deductions.append(5)
            issues.append(f"提示词中未提及素材名称 '{asset.assetName}'")

        total = min(sum(deductions), max_deduction)
        if total == 0:
            return QualityCheck(
                name="prompt_quality",
                label="Prompt 质量",
                passed=True,
                message=f"提示词完整（{char_count} 字符），包含风格和主体描述",
                score=0,
                maxScore=max_deduction,
            )

        return QualityCheck(
            name="prompt_quality",
            label="Prompt 质量",
            passed=False,
            message="；".join(issues),
            score=total,
            maxScore=max_deduction,
        )

    # ── 元数据完整检查（最多扣 15）────────────────────────────────

    def _check_metadata(self, asset: AssetRecord) -> QualityCheck:
        max_deduction = 15
        deductions = []
        issues = []

        if not asset.id:
            deductions.append(8)
            issues.append("缺少素材 ID")
        if not asset.generationId:
            deductions.append(5)
            issues.append("缺少 generationId")
        if not asset.provider:
            deductions.append(5)
            issues.append("缺少 provider 信息")
        if not asset.promptVersion:
            deductions.append(5)
            issues.append("缺少 promptVersion")

        total = min(sum(deductions), max_deduction)
        if total == 0:
            return QualityCheck(
                name="metadata",
                label="元数据完整",
                passed=True,
                message="所有元数据字段已填充",
                score=0,
                maxScore=max_deduction,
            )

        return QualityCheck(
            name="metadata",
            label="元数据完整",
            passed=False,
            message="；".join(issues),
            score=total,
            maxScore=max_deduction,
        )

    # ── 交付就绪检查（最多扣 20）──────────────────────────────────

    def _check_delivery(self, asset: AssetRecord) -> QualityCheck:
        max_deduction = 20
        deductions = []
        issues = []

        if not asset.cloudUrl:
            deductions.append(15)
            issues.append("cloudUrl 未设置（PR12 接入云端上传后生效）")

        if asset.provider == "mock":
            deductions.append(10)
            issues.append("使用 mock provider，非真实生成结果")

        manifest_fields = {
            "id": asset.id,
            "assetName": asset.assetName,
            "assetType": asset.assetType,
            "localPath": asset.localPath,
        }
        missing_manifest = [k for k, v in manifest_fields.items() if not v]
        if missing_manifest:
            deductions.append(8)
            issues.append(f"manifest 缺少字段：{', '.join(missing_manifest)}")

        total = min(sum(deductions), max_deduction)
        if total == 0:
            return QualityCheck(
                name="delivery",
                label="交付就绪",
                passed=True,
                message="素材已满足交付条件（含云端 URL、真实 provider）",
                score=0,
                maxScore=max_deduction,
            )

        return QualityCheck(
            name="delivery",
            label="交付就绪",
            passed=False,
            message="；".join(issues),
            score=total,
            maxScore=max_deduction,
        )

    # ── helpers ─────────────────────────────────────────────────────

    def _find_asset(self, asset_id: str) -> AssetRecord:
        all_assets = self._repository.list_assets()
        for asset in all_assets:
            if asset.id == asset_id:
                return asset
        raise ValueError(f"未找到素材：{asset_id}")


# ── 纯标准库 PNG 工具 ──────────────────────────────────────────────


def _read_png_dimensions(path: Path) -> tuple[int | None, int | None]:
    """从 PNG IHDR chunk 读取宽高，不依赖 Pillow。"""
    width, height, _ = _read_png_ihdr(path)
    return width, height


def _read_png_ihdr(path: Path) -> tuple[int | None, int | None, int]:
    """从 PNG IHDR chunk 读取 width, height, color_type。"""
    data = path.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("不是有效的 PNG 文件")
    pos = 8
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        if chunk_type == b"IHDR":
            ihdr = data[pos + 8 : pos + 8 + length]
            width, height = struct.unpack(">II", ihdr[:8])
            color_type = ihdr[9]  # byte 9 of IHDR = color type
            return width, height, color_type
        pos += 12 + length
    return None, None, 2  # default to RGB


def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _is_solid_color_png(path: Path) -> bool:
    """采样检测 PNG 是否为纯色填充图（mock 特征）。

    在图像的不同区域采样多个像素，如果全部一致则判定为纯色图。
    """
    try:
        data = path.read_bytes()
        if data[:8] != PNG_SIGNATURE:
            return False

        # 收集所有 IDAT chunk 数据
        idat_parts = []
        pos = 8
        while pos + 12 <= len(data):
            length = struct.unpack(">I", data[pos : pos + 4])[0]
            chunk_type = data[pos + 4 : pos + 8]
            if chunk_type == b"IDAT":
                idat_parts.append(data[pos + 8 : pos + 8 + length])
            pos += 12 + length

        if not idat_parts:
            return False

        import zlib
        raw = zlib.decompress(b"".join(idat_parts))

        # 读取 IHDR 获取宽度和颜色类型
        width, height, color_type = _read_png_ihdr(path)
        if width is None or height is None:
            return False

        bytes_per_pixel = 3 if color_type == 2 else 4  # RGB or RGBA
        row_size = 1 + width * bytes_per_pixel

        # 在图像的上、中、下三个区域各采一行，每行在左、中、右各采一个像素
        sample_rows = [0, height // 2, height - 1] if height >= 3 else [0]
        sample_cols = [0, width // 2, width - 1] if width >= 3 else [0]

        first_color = None
        for row_idx in sample_rows:
            if row_idx < 0 or row_idx >= height:
                continue
            start = row_idx * row_size
            if start + row_size > len(raw):
                continue
            row_data = raw[start + 1 : start + row_size]
            for col in sample_cols:
                offset = col * bytes_per_pixel
                if offset + 3 > len(row_data):
                    continue
                color = tuple(row_data[offset : offset + 3])  # RGB only
                if first_color is None:
                    first_color = color
                elif color != first_color:
                    return False

        return first_color is not None
    except Exception:
        return False
