from fastapi import APIRouter

from app.models.prompt_models import PromptCompileRequest, PromptCompileResponse
from app.prompt.prompt_compiler import PromptCompiler

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/compile", response_model=PromptCompileResponse)
def compile_prompts(request: PromptCompileRequest) -> PromptCompileResponse:
    return PromptCompiler().compile(request)
