from fastapi import APIRouter

from app.config import cloud_runtime_config, image_runtime_config, llm_runtime_config
from app.models.config_models import (
    CloudConfigResponse,
    CloudConfigUpdate,
    ImageConfigResponse,
    ImageConfigUpdate,
    LlmConfigResponse,
    LlmConfigUpdate,
)

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/llm", response_model=LlmConfigResponse)
def get_llm_config() -> LlmConfigResponse:
    return llm_runtime_config.public_response()


@router.put("/llm", response_model=LlmConfigResponse)
def update_llm_config(payload: LlmConfigUpdate) -> LlmConfigResponse:
    llm_runtime_config.update(payload)
    return llm_runtime_config.public_response()


@router.get("/image", response_model=ImageConfigResponse)
def get_image_config() -> ImageConfigResponse:
    return image_runtime_config.public_response()


@router.put("/image", response_model=ImageConfigResponse)
def update_image_config(payload: ImageConfigUpdate) -> ImageConfigResponse:
    image_runtime_config.update(payload)
    return image_runtime_config.public_response()


@router.get("/cloud", response_model=CloudConfigResponse)
def get_cloud_config() -> CloudConfigResponse:
    return cloud_runtime_config.public_response()


@router.put("/cloud", response_model=CloudConfigResponse)
def update_cloud_config(payload: CloudConfigUpdate) -> CloudConfigResponse:
    cloud_runtime_config.update(payload)
    return cloud_runtime_config.public_response()
