from fastapi import APIRouter, HTTPException

from app.models.quality_models import AssetQualityReport, GenerationQualityReport
from app.services.quality_service import QualityService

router = APIRouter(prefix="/quality", tags=["quality"])
quality_service = QualityService()


@router.post("/inspect/{asset_id}", response_model=AssetQualityReport)
def inspect_asset(asset_id: str) -> AssetQualityReport:
    try:
        return quality_service.inspect_asset(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/report/{generation_id}", response_model=GenerationQualityReport)
def generation_report(generation_id: str) -> GenerationQualityReport:
    return quality_service.inspect_generation(generation_id)
