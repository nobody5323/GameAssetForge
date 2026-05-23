from app.config import llm_runtime_config
from app.models.prompt_models import PromptCompileRequest, PromptCompileResponse
from app.prompt.tag_extractor import extract_prompt_tags
from app.providers.openai_llm_provider import OpenAiLlmProvider
from app.providers.rule_llm_provider import RuleLlmProvider


class PromptCompiler:
    def __init__(self):
        self.openai_provider = OpenAiLlmProvider()
        self.rule_provider = RuleLlmProvider()

    def compile(self, request: PromptCompileRequest) -> PromptCompileResponse:
        tags = extract_prompt_tags(request)
        threshold = 80 if request.mode == "professional" else 60
        preferred_provider = llm_runtime_config.provider

        if preferred_provider == "openai":
            try:
                candidates = self.openai_provider.compile_prompts(request, tags)
                return PromptCompileResponse(
                    mode=request.mode,
                    targetModel=request.targetModel,
                    provider=self.openai_provider.provider_name,
                    fallback=False,
                    threshold=threshold,
                    candidates=candidates,
                )
            except Exception:
                pass

        candidates = self.rule_provider.compile_prompts(request, tags)
        return PromptCompileResponse(
            mode=request.mode,
            targetModel=request.targetModel,
            provider=self.rule_provider.provider_name,
            fallback=True,
            threshold=threshold,
            candidates=candidates,
        )
