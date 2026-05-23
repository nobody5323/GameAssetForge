import json

from app.config import llm_runtime_config
from app.models.prompt_models import PromptCandidate, PromptCompileRequest
from app.prompt.prompt_scorer import PromptScorer
from app.providers.llm_provider import LlmProvider
from app.providers.rule_llm_provider import PROFESSIONAL_DIRECTIONS, NORMAL_DIRECTIONS
import httpx


class OpenAiLlmProvider(LlmProvider):
    provider_name = "openai"

    def __init__(self):
        self.scorer = PromptScorer()

    def is_available(self) -> bool:
        return bool(llm_runtime_config.api_key)

    def compile_prompts(
        self,
        request: PromptCompileRequest,
        tags: dict[str, list[str]],
    ) -> list[PromptCandidate]:
        if not self.is_available():
            raise RuntimeError("OPENAI_API_KEY is not configured")

        candidates = self._request_candidates(request, tags)
        threshold = 80 if request.mode == "professional" else 60
        for candidate in candidates:
            score = self._score_candidate(request, candidate, tags)
            candidate.score = score
            if score < threshold:
                candidate.warnings.append(
                    f"Score {score} is below the {threshold} threshold after LLM generation."
                )
        return candidates

    def _request_candidates(
        self,
        request: PromptCompileRequest,
        tags: dict[str, list[str]],
    ) -> list[PromptCandidate]:
        payload = {
            "model": llm_runtime_config.prompt_model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": self._system_prompt(),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                {
                                    "request": request.model_dump(),
                                    "extractedTags": tags,
                                    "directions": self._directions_for(request),
                                    "threshold": 80
                                    if request.mode == "professional"
                                    else 60,
                                },
                                ensure_ascii=False,
                            ),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_object",
                }
            },
        }

        with httpx.Client(timeout=45) as client:
            response = client.post(
                f"{llm_runtime_config.base_url}/responses",
                headers={
                    "Authorization": f"Bearer {llm_runtime_config.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()

        content = self._extract_text(response.json())
        parsed = json.loads(content)
        return [PromptCandidate(**candidate) for candidate in parsed["candidates"]]

    def _score_candidate(
        self,
        request: PromptCompileRequest,
        candidate: PromptCandidate,
        tags: dict[str, list[str]],
    ) -> int:
        if not candidate.assets:
            return 0
        scores = [
            self.scorer.score(
                target_model=request.targetModel,
                asset_type=asset.assetType,
                prompt=asset,
                tags=tags,
            )
            for asset in candidate.assets
        ]
        return round(sum(scores) / len(scores))

    def _system_prompt(self) -> str:
        return (
            "You are the Prompt Compiler for GameAsset Forge. "
            "Generate image-generation prompts for a complete 2D game asset pack. "
            "Return JSON only. Shape: {\"candidates\":[{\"id\":\"candidate_1\","
            "\"direction\":\"production_safe\",\"score\":0,\"tags\":{\"style\":[],"
            "\"subject\":[],\"theme\":[],\"environment\":[],\"mood\":[],"
            "\"technical\":[],\"negative\":[]},\"assets\":[{\"assetName\":\"\","
            "\"assetType\":\"\",\"finalPrompt\":\"\",\"negativePrompt\":null}],"
            "\"warnings\":[]}]}. Use every requested asset. For targetModel=gpt_image, "
            "write natural English prompts with subject, style, composition, game usability, "
            "technical requirements, and an Avoid sentence. For targetModel=novelai, "
            "write comma-separated tags and put negative tags in negativePrompt. "
            "Professional mode must return production_safe, style_exploration, and high_detail."
        )

    def _directions_for(self, request: PromptCompileRequest) -> list[str]:
        return PROFESSIONAL_DIRECTIONS if request.mode == "professional" else NORMAL_DIRECTIONS

    def _extract_text(self, response_json: dict) -> str:
        if isinstance(response_json.get("output_text"), str):
            return response_json["output_text"]

        texts = []
        for item in response_json.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str):
                    texts.append(text)
        if not texts:
            raise ValueError("OpenAI response did not include text output")
        return "\n".join(texts)
