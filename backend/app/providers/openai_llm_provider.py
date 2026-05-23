import os

from app.models.prompt_models import PromptCandidate, PromptCompileRequest
from app.providers.rule_llm_provider import RuleLlmProvider


class OpenAiLlmProvider:
    provider_name = "openai"

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_PROMPT_MODEL", "gpt-5-mini")
        self.rule_provider = RuleLlmProvider()

    def is_available(self) -> bool:
        return bool(self.api_key)

    def compile_prompts(
        self,
        request: PromptCompileRequest,
        tags: dict[str, list[str]],
    ) -> list[PromptCandidate]:
        # PR5 keeps a production-safe provider boundary but avoids depending on
        # live credentials during tests. Real API wiring can replace this method
        # without changing the route or response contract.
        if not self.is_available():
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return self.rule_provider.compile_prompts(request, tags)
