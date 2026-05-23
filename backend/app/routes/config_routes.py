from fastapi import APIRouter

from app.config import llm_runtime_config
from app.models.config_models import LlmConfigResponse, LlmConfigUpdate

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/llm", response_model=LlmConfigResponse)
def get_llm_config() -> LlmConfigResponse:
    return llm_runtime_config.public_response()


@router.put("/llm", response_model=LlmConfigResponse)
def update_llm_config(payload: LlmConfigUpdate) -> LlmConfigResponse:
    llm_runtime_config.update(payload)
    return llm_runtime_config.public_response()
