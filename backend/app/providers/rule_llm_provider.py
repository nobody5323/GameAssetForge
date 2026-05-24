from app.models.prompt_models import (
    PromptAssetResult,
    PromptCandidate,
    PromptCompileRequest,
    PromptDirection,
)
from app.prompt.chinese_translator import translate_chinese_text
from app.prompt.model_optimizers import PromptOptimizer
from app.prompt.prompt_scorer import PromptScorer


NORMAL_DIRECTIONS: list[PromptDirection] = ["quick_start"]
PROFESSIONAL_DIRECTIONS: list[PromptDirection] = [
    "production_safe",
    "style_exploration",
    "high_detail",
]


class RuleLlmProvider:
    provider_name = "rule_fallback"

    def __init__(self):
        self.optimizer = PromptOptimizer()
        self.scorer = PromptScorer()

    def compile_prompts(
        self,
        request: PromptCompileRequest,
        tags: dict[str, list[str]],
    ) -> list[PromptCandidate]:
        directions = (
            PROFESSIONAL_DIRECTIONS if request.mode == "professional" else NORMAL_DIRECTIONS
        )
        threshold = 80 if request.mode == "professional" else 60
        project_context = ", ".join(
            filter(
                None,
                (
                    translate_chinese_text(request.projectName),
                    translate_chinese_text(request.gameType),
                    translate_chinese_text(request.theme),
                    translate_chinese_text(request.description),
                ),
            )
        )

        candidates: list[PromptCandidate] = []
        for index, direction in enumerate(directions, start=1):
            assets = []
            scores = []
            for asset in request.assets:
                final_prompt, negative_prompt = self.optimizer.optimize(
                    target_model=request.targetModel,
                    asset=asset,
                    tags=tags,
                    direction=direction,
                    project_context=project_context,
                )
                asset_result = PromptAssetResult(
                    assetName=asset.name,
                    assetType=asset.type,
                    finalPrompt=final_prompt,
                    negativePrompt=negative_prompt,
                )
                assets.append(asset_result)
                scores.append(
                    self.scorer.score(
                        target_model=request.targetModel,
                        asset_type=asset.type,
                        prompt=asset_result,
                        tags=tags,
                    )
                )

            score = round(sum(scores) / len(scores)) if scores else 0
            warnings = []
            if score < threshold:
                warnings.append(
                    f"Score {score} is below the {threshold} threshold for {request.mode} mode."
                )

            candidates.append(
                PromptCandidate(
                    id=f"candidate_{index}",
                    direction=direction,
                    score=score,
                    tags=tags,
                    assets=assets,
                    warnings=warnings,
                )
            )
        return candidates
