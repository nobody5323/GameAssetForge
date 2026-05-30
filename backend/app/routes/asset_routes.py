from fastapi import APIRouter, HTTPException, Query

from app.models.asset_models import AssetGenerateRequest, AssetGenerateResponse, AssetRecord, BatchRegenerateRequest, SecondaryGenerationRequest
from app.repositories.asset_repository import AssetRepository
from app.services.asset_generation_service import AssetGenerationService


router = APIRouter(prefix="/assets", tags=["assets"])
asset_generation_service = AssetGenerationService()
asset_repository = AssetRepository()


@router.post("/generate", response_model=AssetGenerateResponse)
def generate_assets(request: AssetGenerateRequest) -> AssetGenerateResponse:
    try:
        return asset_generation_service.generate(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Asset generation failed: {exc}")


@router.get("", response_model=list[AssetRecord])
def list_assets(category: str | None = Query(default=None, description="按素材类型过滤，例如 character、enemy、item 等")) -> list[AssetRecord]:
    assets = asset_repository.list_assets()
    if category:
        assets = [asset for asset in assets if asset.assetType == category]
    return assets


@router.post("/{asset_id}/regenerate", response_model=AssetRecord)
def regenerate_asset(asset_id: str, request: SecondaryGenerationRequest) -> AssetRecord:
    original = asset_repository.find_asset(asset_id)
    if original is None:
        raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")

    try:
        return asset_generation_service.regenerate_asset(original, request.action, request.customPrompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {exc}")


@router.post("/regenerate-batch", response_model=list[AssetRecord])
def regenerate_batch(request: BatchRegenerateRequest) -> list[AssetRecord]:
    original = asset_repository.find_asset(request.assetId)
    if original is None:
        raise HTTPException(status_code=404, detail=f"Asset not found: {request.assetId}")

    results: list[AssetRecord] = []
    errors: list[str] = []
    for action in request.actions:
        try:
            result = asset_generation_service.regenerate_asset(original, action, request.customPrompt)
            results.append(result)
        except ValueError as exc:
            errors.append(f"{original.assetName}/{action}: {exc}")
        except RuntimeError as exc:
            errors.append(f"{original.assetName}/{action}: {exc}")
        except Exception as exc:
            errors.append(f"{original.assetName}/{action}: {exc}")

    if not results and errors:
        raise HTTPException(status_code=502, detail="; ".join(errors))

    return results
