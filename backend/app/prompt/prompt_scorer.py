from app.models.prompt_models import PromptAssetResult, TargetModel


class PromptScorer:
    def score(
        self,
        *,
        target_model: TargetModel,
        asset_type: str,
        prompt: PromptAssetResult,
        tags: dict[str, list[str]],
    ) -> int:
        score = 0
        text = f"{prompt.finalPrompt} {prompt.negativePrompt or ''}".lower()

        if prompt.finalPrompt and len(prompt.finalPrompt) >= 120:
            score += 25
        elif prompt.finalPrompt:
            score += 15

        if asset_type.lower() in text or asset_type.replace("_", " ").lower() in text:
            score += 20

        if target_model == "novelai":
            score += 20 if "," in prompt.finalPrompt and "game asset" in text else 10
        else:
            score += 20 if "create a production-ready" in text and "avoid:" in text else 10

        technical_hits = sum(1 for tag in tags["technical"] if tag.lower() in text)
        score += 20 if technical_hits >= 3 else 10 if technical_hits else 0

        negative_hits = sum(1 for tag in tags["negative"] if tag.lower() in text)
        score += 15 if negative_hits >= 3 else 8 if negative_hits else 0

        return min(score, 100)
