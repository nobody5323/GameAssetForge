"""云端上传路由。"""

from fastapi import APIRouter, HTTPException

from app.models.asset_models import AssetRecord
from app.services.cloud_service import CloudService

router = APIRouter(prefix="/cloud", tags=["cloud"])
cloud_service = CloudService()


@router.post("/upload/{asset_id}", response_model=AssetRecord)
def upload_asset(asset_id: str) -> AssetRecord:
    """上传单个素材到云端（模拟），返回更新后的素材记录（含 cloudUrl）。"""
    try:
        return cloud_service.upload_asset(asset_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/upload-generation/{generation_id}", response_model=list[AssetRecord])
def upload_generation(generation_id: str) -> list[AssetRecord]:
    """上传整个 generation 的所有素材到云端。"""
    try:
        return cloud_service.upload_generation(generation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
