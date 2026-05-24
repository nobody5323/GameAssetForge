from fastapi import APIRouter, Query

from app.models.asset_models import AssetGenerateRequest, AssetGenerateResponse, AssetRecord
from app.repositories.asset_repository import AssetRepository
from app.services.asset_generation_service import AssetGenerationService


router = APIRouter(prefix="/assets", tags=["assets"])
asset_generation_service = AssetGenerationService()
asset_repository = AssetRepository()


@router.post("/generate", response_model=AssetGenerateResponse)
def generate_assets(request: AssetGenerateRequest) -> AssetGenerateResponse:
    return asset_generation_service.generate(request)


@router.get("", response_model=list[AssetRecord])
def list_assets(category: str | None = Query(default=None, description="按素材类型过滤，例如 character、enemy、item 等")) -> list[AssetRecord]:
    assets = asset_repository.list_assets()
    if category:
        assets = [asset for asset in assets if asset.assetType == category]
    return assets
