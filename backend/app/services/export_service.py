"""导出服务 — 生成 manifest.json 并打包 zip。"""

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app.models.asset_models import AssetRecord
from app.models.export_models import ExportResponse, Manifest, ManifestAsset
from app.repositories.asset_repository import AssetRepository
from app.services.quality_service import QualityService

BACKEND_ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = BACKEND_ROOT / "runtime" / "exports"


class ExportService:
    """导出服务 —— 为指定 generation 生成 manifest + zip 包。"""

    def __init__(
        self,
        repository: AssetRepository | None = None,
        quality_service: QualityService | None = None,
    ) -> None:
        self._repository = repository or AssetRepository()
        self._quality_service = quality_service or QualityService(self._repository)

    def export_generation(self, generation_id: str) -> tuple[ExportResponse, bytes]:
        """为指定 generation 生成 zip 包，返回 ExportResponse 和 zip 字节流。"""
        all_assets = self._repository.list_assets()
        gen_assets = [a for a in all_assets if a.generationId == generation_id]
        if not gen_assets:
            raise ValueError(f"未找到 generation：{generation_id}")

        # 收集项目名（从素材记录的 projectName 字段获取）
        project_name = gen_assets[0].projectName or self._infer_project_name(
            generation_id, gen_assets[0]
        )

        # 运行质量检查
        quality_map: dict[str, int] = {}
        for asset in gen_assets:
            try:
                report = self._quality_service.inspect_asset(asset.id)
                quality_map[asset.id] = report.totalScore
            except Exception:
                quality_map[asset.id] = 0

        now_iso = datetime.now(timezone.utc).isoformat()

        # 构建 manifest
        manifest_assets: list[ManifestAsset] = []
        for asset in gen_assets:
            zip_path = f"{asset.assetType}/{Path(asset.localPath).name}"
            manifest_assets.append(
                ManifestAsset(
                    id=asset.id,
                    assetName=asset.assetName,
                    assetType=asset.assetType,
                    style=asset.style,
                    theme=asset.theme,
                    finalPrompt=asset.finalPrompt,
                    localPath=zip_path,
                    provider=asset.provider,
                    qualityScore=quality_map.get(asset.id),
                )
            )

        manifest = Manifest(
            generationId=generation_id,
            projectName=project_name,
            exportedAt=now_iso,
            assetCount=len(manifest_assets),
            assets=manifest_assets,
        )

        manifest_json = json.dumps(
            manifest.model_dump(), ensure_ascii=False, indent=2
        ).encode("utf-8")

        # 构建 zip（在内存中）
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 写入 manifest.json
            zf.writestr("manifest.json", manifest_json)

            # 写入每个 PNG 素材
            for asset in gen_assets:
                file_path = BACKEND_ROOT / asset.localPath
                zip_path = f"{asset.assetType}/{Path(asset.localPath).name}"
                if file_path.exists():
                    zf.write(file_path, zip_path)

        zip_bytes = zip_buffer.getvalue()
        zip_file_name = f"{generation_id}.zip"

        # 同时保存到磁盘（方便静态文件访问）
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        (EXPORT_DIR / zip_file_name).write_bytes(zip_bytes)
        (EXPORT_DIR / f"{generation_id}.manifest.json").write_text(
            json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        response = ExportResponse(
            generationId=generation_id,
            zipFileName=zip_file_name,
            assetCount=len(gen_assets),
            manifestSize=len(manifest_json),
            totalSize=len(zip_bytes),
        )

        return response, zip_bytes

    def list_exportable_generations(self) -> list[str]:
        """返回所有可导出的 generation ID 列表。"""
        all_assets = self._repository.list_assets()
        gen_ids: list[str] = []
        seen: set[str] = set()
        for asset in all_assets:
            if asset.generationId and asset.generationId not in seen:
                seen.add(asset.generationId)
                gen_ids.append(asset.generationId)
        return gen_ids

    @staticmethod
    def _infer_project_name(generation_id: str, sample_asset: AssetRecord) -> str:
        """从素材路径推断项目名称。"""
        local_path = sample_asset.localPath
        parts = Path(local_path).parts
        # 路径格式：runtime/storage/generated-assets/gen_xxx/type/name.png
        for i, part in enumerate(parts):
            if part == "generated-assets" and i + 1 < len(parts):
                return parts[i + 1]
        return generation_id
