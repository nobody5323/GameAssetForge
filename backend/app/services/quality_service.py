import re
import struct
from pathlib import Path

from app.models.asset_models import AssetRecord
from app.models.quality_models import (
    AssetQualityReport,
    GenerationQualityReport,
    QualityDimension,
    QualitySubCheck,
)
from app.repositories.asset_repository import AssetRepository

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

FULL_SCORE = 100
PASS_THRESHOLD = 60

DIMENSION_WEIGHTS = {
    "format": 15,
    "dimensions": 20,
    "category_fit": 15,
    "clarity": 20,
    "prompt_alignment": 20,
    "visual_quality": 10,
}

SUPPORTED_ASSET_TYPES = {"character", "enemy", "item", "tileset", "ui", "background"}
ASSET_TYPE_LABELS = {
    "character": "角色",
    "enemy": "敌人",
    "item": "物品",
    "tileset": "地砖",
    "ui": "界面元素",
    "background": "背景",
}
STYLE_LABELS = {
    "pixel_art": "像素风",
    "cartoon": "卡通风",
    "dark_fantasy": "黑暗奇幻",
    "cyberpunk": "赛博朋克",
}
STYLE_KEYWORDS = {
    "pixel_art": ["pixel", "8-bit", "16-bit", "sprite", "retro"],
    "cartoon": ["cartoon", "flat color", "clean outline"],
    "dark_fantasy": ["dark fantasy", "gothic", "moody", "fantasy"],
    "cyberpunk": ["cyberpunk", "neon", "futuristic", "sci-fi"],
}
ASSET_TYPE_HINTS = {
    "character": ["character", "hero", "protagonist", "girl", "boy", "person", "sprite"],
    "enemy": ["enemy", "monster", "slime", "creature", "boss", "sprite"],
    "item": ["item", "icon", "coin", "potion", "weapon", "collectible"],
    "tileset": ["tileset", "tile", "terrain", "ground", "modular", "seam"],
    "ui": ["ui", "button", "panel", "icon", "interface", "hud"],
    "background": ["background", "backdrop", "scene", "environment", "landscape"],
}


class QualityService:
    """按 6 个图片质量维度输出加权评分。"""

    def __init__(self, repository: AssetRepository | None = None) -> None:
        self._repository = repository or AssetRepository()

    def inspect_asset(self, asset_id: str) -> AssetQualityReport:
        asset = self._find_asset(asset_id)
        file_path = BACKEND_ROOT / asset.localPath
        width, height, color_type, png_error = _read_png_info(file_path)

        dimensions = [
            self._check_format(asset, file_path, width, height, png_error),
            self._check_dimensions(asset, width, height),
            self._check_category_fit(asset, width, height),
            self._check_clarity(asset, file_path, width, height, png_error),
            self._check_prompt_alignment(asset),
            self._check_visual_quality(asset, file_path, width, height, color_type, png_error),
        ]
        total = min(FULL_SCORE, round(sum(d.weightedScore for d in dimensions)))
        if dimensions[0].dimensionScore == 0:
            total = 0
        tips = _dedupe(
            sub.optimizationHint
            for dimension in dimensions
            for sub in dimension.subChecks
            if not sub.passed and sub.optimizationHint
        )
        return AssetQualityReport(
            assetId=asset.id,
            assetName=asset.assetName,
            assetType=asset.assetType,
            generationId=asset.generationId,
            dimensions=dimensions,
            totalScore=total,
            maxScore=FULL_SCORE,
            grade=_grade(total),
            overallHint=_overall_hint(dimensions),
            promptOptimizationTips=tips,
        )

    def inspect_generation(self, generation_id: str) -> GenerationQualityReport:
        gen_assets = [a for a in self._repository.list_assets() if a.generationId == generation_id]
        if not gen_assets:
            return GenerationQualityReport(generationId=generation_id, maxScore=FULL_SCORE)

        reports = [self.inspect_asset(asset.id) for asset in gen_assets]
        overall = round(sum(report.totalScore for report in reports) / len(reports))
        pass_count = sum(1 for report in reports if report.totalScore >= PASS_THRESHOLD)
        grade_counts = {grade: sum(1 for report in reports if report.grade == grade) for grade in ["A", "B", "C", "D", "F"]}
        return GenerationQualityReport(
            generationId=generation_id,
            assets=reports,
            overallScore=overall,
            maxScore=FULL_SCORE,
            assetCount=len(reports),
            passCount=pass_count,
            failCount=len(reports) - pass_count,
            gradeA=grade_counts["A"],
            gradeB=grade_counts["B"],
            gradeC=grade_counts["C"],
            gradeD=grade_counts["D"],
            gradeF=grade_counts["F"],
        )

    def _check_format(
        self,
        asset: AssetRecord,
        file_path: Path,
        width: int | None,
        height: int | None,
        png_error: str,
    ) -> QualityDimension:
        exists = file_path.exists()
        data = b""
        read_error = ""
        if exists:
            try:
                data = file_path.read_bytes()
            except OSError as exc:
                read_error = str(exc)

        checks = [
            _subcheck("file_exists", "文件存在", exists, 35, f"文件不存在：{asset.localPath}", "重新生成该素材，并确认 PNG 文件已经成功保存。"),
            _subcheck("png_extension", "文件扩展名为 .png", file_path.suffix.lower() == ".png", 10, "文件扩展名不是 .png。", "在提示词或生成配置中明确要求输出单张 PNG 游戏素材。"),
            _subcheck("file_readable", "文件可以读取", exists and not read_error, 20, f"文件无法读取：{read_error}", "重新生成素材；当前文件可能被占用、损坏或写入不完整。"),
            _subcheck("png_signature", "PNG 文件头有效", bool(data) and data[:8] == PNG_SIGNATURE, 20, "文件头不是有效的 PNG 格式。", "重新生成，并明确要求输出有效 PNG 图片。"),
            _subcheck("png_ihdr", "PNG 尺寸块有效", width is not None and height is not None, 10, png_error or "无法解析 PNG 尺寸块。", "重新生成完整 PNG，避免文件被截断。"),
            _subcheck("file_size", "PNG 文件不是异常小文件", len(data) >= 70, 5, f"PNG 文件过小（{len(data)} 字节）。", "重新生成完整图片文件，避免空文件或截断文件。"),
        ]
        dimension = _dimension("format", "格式与文件有效性", checks)
        if not exists or read_error or not (data and data[:8] == PNG_SIGNATURE) or width is None or height is None:
            dimension.dimensionScore = 0
            dimension.weightedScore = 0
            dimension.passed = False
        return dimension

    def _check_dimensions(self, asset: AssetRecord, width: int | None, height: int | None) -> QualityDimension:
        expected = _expected_size_profile(asset.assetType)
        width = width or 0
        height = height or 0
        min_side = min(width, height)
        max_side = max(width, height)
        type_label = _asset_type_label(asset.assetType)
        checks = [
            _subcheck("size_readable", "宽高信息可以解析", width > 0 and height > 0, 30, "无法读取图片宽高。", "重新生成完整 PNG，并确保图片包含有效尺寸信息。"),
            _subcheck("minimum_side", "最短边满足素材要求", min_side >= expected["min_side"], 20, f"{width}x{height} 低于{type_label}素材建议的最短边 {expected['min_side']}px。", f"在提示词中加入“{expected['prompt_size']}”和“主体完整入画”。"),
            _subcheck("production_side", "最短边达到生产建议", min_side >= expected["preferred_side"], 10, f"{width}x{height} 低于生产建议的 {expected['preferred_side']}px。", f"正式素材建议使用 {expected['prompt_size']} 或更高分辨率。"),
            _subcheck("maximum_side", "最长边没有过大", max_side <= expected["max_side"], 10, f"{width}x{height} 超过建议最长边 {expected['max_side']}px。", "使用更小画布，降低导入游戏引擎后的资源成本。"),
            _subcheck("power_of_two", "宽高为 2 的幂", _is_power_of_two(width) and _is_power_of_two(height), 10, "宽或高不是 2 的幂。", "指定 256x256、512x512、1024x1024 等贴图友好尺寸。"),
            _subcheck("grid_aligned", "宽高对齐 16px 网格", width % 16 == 0 and height % 16 == 0 and width > 0, 10, "宽或高不是 16 的倍数。", "加入“16px 网格对齐”或“适合 tile-map 使用”。"),
            _subcheck("aspect_ratio", "宽高比例符合素材类型", _aspect_ratio(width, height) <= 2.5 or asset.assetType == "background", 10, "素材画面过宽或过高。", "要求主体居中、方形画布或受控构图，避免主体被拉成长条。"),
        ]
        return _dimension("dimensions", "图片尺寸", checks, detail=f"实际尺寸：{width}x{height}")

    def _check_category_fit(self, asset: AssetRecord, width: int | None, height: int | None) -> QualityDimension:
        normalized_type = asset.assetType.lower()
        path_parts = {part.lower() for part in Path(asset.localPath).parts}
        prompt = _normalized_text(asset.finalPrompt)
        hints = ASSET_TYPE_HINTS.get(normalized_type, [normalized_type])
        name_issues = _asset_name_issues(asset.assetName)
        ratio = _aspect_ratio(width or 1, height or 1)
        type_label = _asset_type_label(asset.assetType)
        checks = [
            _subcheck("supported_type", "素材类型在支持范围内", normalized_type in SUPPORTED_ASSET_TYPES, 15, f"不支持的素材类型：{asset.assetType}。", "请使用角色、敌人、物品、地砖、界面元素或背景等支持类型。"),
            _subcheck("type_directory", "保存路径包含素材类型目录", normalized_type in path_parts, 15, f"保存路径中没有包含{type_label}类型目录。", "建议按“生成批次/素材类型/素材名.png”保存。"),
            _subcheck("category_prompt", "提示词包含分类关键词", any(hint in prompt for hint in hints), 20, "提示词缺少该分类的关键描述。", f"在提示词中补充“{type_label}素材”的用途、主体和画面要求。"),
            _subcheck("snake_case_name", "素材名称符合 snake_case", not name_issues, 20, "素材名称不符合 snake_case：" + "、".join(name_issues), "素材名只使用小写字母、数字和下划线。"),
            _subcheck("orientation", "画布方向符合素材分类", _category_orientation_ok(normalized_type, width, height), 15, "画布方向与素材分类不匹配。", "背景图建议横向宽画布；地砖、图标、UI 元素建议方形或受控构图。"),
            _subcheck("single_subject_ratio", "单体素材避免极端比例", normalized_type not in {"character", "enemy", "item", "ui"} or ratio <= 2.0, 15, "单体素材的宽高比例不自然。", "加入“单个主体居中”“方形画布”“透明背景”等约束。"),
        ]
        return _dimension("category_fit", "素材分类匹配", checks)

    def _check_clarity(
        self,
        asset: AssetRecord,
        file_path: Path,
        width: int | None,
        height: int | None,
        png_error: str,
    ) -> QualityDimension:
        width = width or 0
        height = height or 0
        solid = False if png_error else _is_solid_color_png(file_path)
        checks = [
            _subcheck("not_placeholder", "图片不是纯色占位图", not solid and not png_error, 35, "图片接近纯色占位图，或无法读取像素内容。", "补充清晰主体、轮廓、材质、颜色变化和局部细节。"),
            _subcheck("short_side_128", "最短边至少 128px", min(width, height) >= 128, 15, "最短边过小，实际使用时容易模糊。", "请求输出 256x256 或 512x512 尺寸。"),
            _subcheck("short_side_256", "生产素材最短边至少 256px", min(width, height) >= 256, 15, "最短边低于生产建议的 256px。", "正式素材建议使用 256x256 或更高分辨率。"),
            _subcheck("clear_edges_prompt", "提示词要求清晰边缘或轮廓", _has_any(asset.finalPrompt, ["clear silhouette", "clean edges", "crisp edges", "outline", "清晰轮廓", "干净边缘"]), 10, "提示词没有要求清晰边缘或可读轮廓。", "加入“清晰轮廓”“干净边缘”“锐利描边”等约束。"),
            _subcheck("readable_scale_prompt", "提示词要求小尺寸可读性", _has_any(asset.finalPrompt, ["readable", "small size", "thumbnail", "game-ready", "小尺寸", "可读"]), 10, "提示词没有说明游戏内小尺寸可读性。", "加入“小尺寸仍然可读”“适合游戏内使用”等要求。"),
            _subcheck("detail_prompt", "提示词要求视觉细节", _has_any(asset.finalPrompt, ["detail", "material", "texture", "lighting", "palette", "color", "细节", "材质", "光照"]), 15, "提示词缺少细节、材质或颜色控制。", "描述材质、色板、光照和关键细节。"),
        ]
        return _dimension("clarity", "清晰度与细节", checks)

    def _check_prompt_alignment(self, asset: AssetRecord) -> QualityDimension:
        prompt = _normalized_text(asset.finalPrompt)
        name_tokens = _name_tokens(asset.assetName)
        style_terms = STYLE_KEYWORDS.get(asset.style, [asset.style.replace("_", " ")])
        visual_terms = ["style", "composition", "background", "silhouette", "color", "material", "lighting"]
        type_label = _asset_type_label(asset.assetType)
        style_label = _style_label(asset.style)
        checks = [
            _subcheck("prompt_present", "提示词存在", bool(prompt), 25, "finalPrompt 为空。", "写完整提示词，包含主体、风格、构图和限制条件。"),
            _subcheck("prompt_length", "提示词描述足够充分", len(prompt) >= 50, 20, "提示词过短。", "补充主体外观、姿态、材质、背景、用途和避免项。"),
            _subcheck("type_mentioned", "提示词提到素材类型", asset.assetType.lower() in prompt, 15, f"提示词没有提到素材类型：{type_label}。", f"在提示词中加入“{type_label}素材”的明确描述。"),
            _subcheck("name_keywords", "提示词覆盖素材名称关键词", not name_tokens or any(token in prompt for token in name_tokens), 10, f"提示词没有覆盖素材名关键词：{asset.assetName}。", "把素材名称里的核心词加入主体描述。"),
            _subcheck("style_reflected", "提示词体现所选风格", not asset.style or any(term in prompt for term in style_terms), 10, f"提示词没有体现风格：{style_label}。", f"加入与“{style_label}”一致的线条、色彩、渲染方式和细节要求。"),
            _subcheck("theme_reflected", "提示词体现所选主题", not asset.theme or _has_theme_overlap(asset.theme, prompt), 10, f"提示词没有体现主题：{asset.theme}。", "加入主题环境、颜色、氛围或世界观关键词。"),
            _subcheck("visual_controls", "提示词包含视觉控制词", sum(1 for term in visual_terms if term in prompt) >= 2, 10, "提示词缺少构图、材质或光照等视觉控制。", "补充构图、背景、材质、光照、清晰轮廓等视觉控制。"),
        ]
        return _dimension("prompt_alignment", "提示词符合度", checks)

    def _check_visual_quality(
        self,
        asset: AssetRecord,
        file_path: Path,
        width: int | None,
        height: int | None,
        color_type: int | None,
        png_error: str,
    ) -> QualityDimension:
        solid = False if png_error else _is_solid_color_png(file_path)
        checks = [
            _subcheck("real_provider", "由真实图片模型生成", asset.provider != "mock" and asset.providerMetadata.get("mock") is not True, 25, "当前素材使用模拟生成器。", "切换到真实图片生成模型后重新生成。"),
            _subcheck("delivery_url", "素材访问地址可用", bool(asset.cloudUrl), 10, "云端访问地址未设置。", "上传生成素材，并检查云端预览地址是否可访问。"),
            _subcheck("color_type", "PNG 色彩类型为 RGB 或 RGBA", color_type in {2, 6}, 10, f"PNG 色彩类型 {color_type} 不是常见的 RGB/RGBA。", "请求标准 RGB/RGBA PNG 输出。"),
            _subcheck("large_variation", "大图具有可见变化", not (width and height and min(width, height) >= 256 and solid) and not png_error, 25, "大尺寸图片仍然接近纯色，或无法读取像素内容。", "要求清晰主体、材质、阴影、边缘细节和颜色变化。"),
            _subcheck("stable_prompt", "提示词足够支撑稳定生成", len(asset.finalPrompt or "") >= 100, 15, "提示词偏短，生成稳定性不足。", "增加可见属性和限制条件，减少随机跑偏。"),
            _subcheck("provider_metadata", "元数据标识模型或供应商", bool(asset.provider and asset.providerMetadata), 15, "缺少模型或供应商元数据。", "保留供应商和模型元数据，方便追踪生成质量。"),
        ]
        return _dimension("visual_quality", "具体质量等级", checks)

    def _find_asset(self, asset_id: str) -> AssetRecord:
        asset = self._repository.find_asset(asset_id)
        if asset is not None:
            return asset
        raise ValueError(f"未找到素材：{asset_id}")


def _subcheck(
    name: str,
    label: str,
    passed: bool,
    deduction_pct: int,
    fail_message: str,
    optimization_hint: str,
    pass_message: str = "通过",
) -> QualitySubCheck:
    return QualitySubCheck(
        name=name,
        label=label,
        passed=passed,
        message=pass_message if passed else fail_message,
        deductionPct=0 if passed else deduction_pct,
        weightHint=f"未通过扣本维度 {deduction_pct}%",
        optimizationHint="" if passed else optimization_hint,
    )


def _dimension(name: str, label: str, subchecks: list[QualitySubCheck], detail: str | None = None) -> QualityDimension:
    deduction = min(100, sum(sub.deductionPct for sub in subchecks))
    score = max(0, 100 - deduction)
    weight = DIMENSION_WEIGHTS[name]
    if detail:
        subchecks = [
            *subchecks,
            QualitySubCheck(
                name="dimension_detail",
                label="维度补充信息",
                passed=True,
                message=detail,
                deductionPct=0,
                weightHint="不参与扣分",
                optimizationHint="",
            ),
        ]
    return QualityDimension(
        name=name,
        label=label,
        weightPct=weight,
        subChecks=subchecks,
        dimensionScore=score,
        weightedScore=round(score * weight / 100, 2),
        passed=score >= 70,
        passedCount=sum(1 for sub in subchecks if sub.passed),
        totalCount=len(subchecks),
    )


def _read_png_info(path: Path) -> tuple[int | None, int | None, int | None, str]:
    if not path.exists():
        return None, None, None, "文件不存在"
    try:
        return (*_read_png_ihdr(path), "")
    except (OSError, ValueError, struct.error) as exc:
        return None, None, None, str(exc)


def _expected_size_profile(asset_type: str) -> dict[str, int | str]:
    if asset_type == "background":
        return {"min_side": 256, "preferred_side": 576, "max_side": 4096, "prompt_size": "横向 1024x576 或 1536x864 背景图"}
    if asset_type == "tileset":
        return {"min_side": 256, "preferred_side": 512, "max_side": 2048, "prompt_size": "方形 512x512 地砖图集"}
    if asset_type == "ui":
        return {"min_side": 128, "preferred_side": 256, "max_side": 2048, "prompt_size": "256x256 或 512x512 UI 图集元素"}
    return {"min_side": 128, "preferred_side": 256, "max_side": 2048, "prompt_size": "256x256 或 512x512 独立素材"}


def _asset_type_label(asset_type: str) -> str:
    return ASSET_TYPE_LABELS.get(asset_type.lower(), asset_type)


def _style_label(style: str | None) -> str:
    if not style:
        return "未选择风格"
    return STYLE_LABELS.get(style, style.replace("_", " "))


def _read_png_dimensions(path: Path) -> tuple[int | None, int | None]:
    width, height, _ = _read_png_ihdr(path)
    return width, height


def _read_png_ihdr(path: Path) -> tuple[int | None, int | None, int]:
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
            color_type = ihdr[9]
            return width, height, color_type
        pos += 12 + length
    return None, None, 2


def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _is_solid_color_png(path: Path) -> bool:
    try:
        data = path.read_bytes()
        if data[:8] != PNG_SIGNATURE:
            return False

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
        width, height, color_type = _read_png_ihdr(path)
        if width is None or height is None:
            return False

        bytes_per_pixel = 3 if color_type == 2 else 4
        row_size = 1 + width * bytes_per_pixel
        sample_rows = [0, height // 2, height - 1] if height >= 3 else [0]
        sample_cols = [0, width // 2, width - 1] if width >= 3 else [0]
        first_color = None
        for row_idx in sample_rows:
            start = row_idx * row_size
            if start + row_size > len(raw):
                continue
            row_data = raw[start + 1 : start + row_size]
            for col in sample_cols:
                offset = col * bytes_per_pixel
                if offset + 3 > len(row_data):
                    continue
                color = tuple(row_data[offset : offset + 3])
                if first_color is None:
                    first_color = color
                elif color != first_color:
                    return False
        return first_color is not None
    except Exception:
        return False


def _normalized_text(value: str | None) -> str:
    return (value or "").replace("_", " ").lower()


def _name_tokens(name: str) -> list[str]:
    return [token for token in re.split(r"[^a-zA-Z0-9]+", name.lower()) if len(token) >= 3]


def _asset_name_issues(name: str) -> list[str]:
    issues = []
    if not name:
        return ["名称为空"]
    if " " in name:
        issues.append("包含空格")
    if re.search(r"[A-Z]", name):
        issues.append("包含大写字母")
    if re.search(r"[^a-z0-9_]", name):
        issues.append("包含特殊字符")
    if re.match(r"^\d", name):
        issues.append("以数字开头")
    if len(name) > 40:
        issues.append("名称过长")
    return issues


def _has_theme_overlap(theme: str, prompt: str) -> bool:
    tokens = [token for token in re.split(r"[^a-zA-Z0-9]+", theme.lower()) if len(token) >= 3]
    return bool(tokens) and any(token in prompt for token in tokens)


def _has_any(value: str | None, terms: list[str]) -> bool:
    text = _normalized_text(value)
    return any(term in text for term in terms)


def _category_orientation_ok(asset_type: str, width: int | None, height: int | None) -> bool:
    if not width or not height:
        return False
    if asset_type == "background":
        return width > height
    if asset_type == "tileset":
        return width == height
    return True


def _aspect_ratio(width: int, height: int) -> float:
    small = max(1, min(width, height))
    return max(width, height) / small


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _overall_hint(dimensions: list[QualityDimension]) -> str:
    weak = [dimension.label for dimension in dimensions if dimension.dimensionScore < 70]
    if not weak:
        return "整体质量较好，可以进入素材库复用或导出。"
    return "需要优先优化：" + "、".join(weak[:3]) + "。"


def _dedupe(values) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
