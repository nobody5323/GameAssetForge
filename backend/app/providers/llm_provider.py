from abc import ABC, abstractmethod

from app.models.prompt_models import PromptCandidate, PromptCompileRequest


class LlmProvider(ABC):
    provider_name: str

    @abstractmethod
    def compile_prompts(
        self,
        request: PromptCompileRequest,
        tags: dict[str, list[str]],
    ) -> list[PromptCandidate]:
        raise NotImplementedError
