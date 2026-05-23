from fastapi import APIRouter

from app.models.asset_models import AssetGenerateRequest, AssetGenerateResponse
from app.services.asset_generation_service import AssetGenerationService


router = APIRouter(prefix="/assets", tags=["assets"])
asset_generation_service = AssetGenerationService()


@router.post("/generate", response_model=AssetGenerateResponse)
def generate_assets(request: AssetGenerateRequest) -> AssetGenerateResponse:
    return asset_generation_service.generate(request)
