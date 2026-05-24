"""导出路由 — POST /api/exports/{generation_id} 返回 zip 文件。"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])
export_service = ExportService()


@router.post("/{generation_id}")
def export_generation(generation_id: str) -> Response:
    """为指定 generation 生成 zip 包并以文件下载形式返回。"""
    try:
        export_response, zip_bytes = export_service.export_generation(generation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{export_response.zipFileName}"',
            "X-Generation-Id": export_response.generationId,
            "X-Asset-Count": str(export_response.assetCount),
            "X-Manifest-Size": str(export_response.manifestSize),
            "X-Total-Size": str(export_response.totalSize),
        },
    )


@router.get("")
def list_exportable_generations() -> list[str]:
    """列出所有可导出（有过素材记录的）generation ID。"""
    return export_service.list_exportable_generations()
