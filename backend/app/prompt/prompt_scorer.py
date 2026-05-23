from app.models.prompt_models import PromptAssetResult, TargetModel


ASSET_USABILITY_TERMS = [
    "clear silhouette",
    "readable",
    "centered composition",
    "simple background",
    "game-ready",
    "small size",
]

COMPOSITION_TERMS = [
    "color",
    "palette",
    "lighting",
    "material",
    "shape",
    "pose",
    "composition",
    "environment",
]

OVERCOMPLEXITY_TERMS = [
    "highly detailed background",
    "cinematic scene",
    "complex background",
    "many tiny details",
    "photorealistic",
    "ultra realistic",
]

DIRECTION_WEIGHTS = {
    "quick_start": -8,
    "production_safe": 2,
    "style_exploration": -3,
    "high_detail": -8,
}


class PromptScorer:
    def score(
        self,
        *,
        target_model: TargetModel,
        asset_type: str,
        prompt: PromptAssetResult,
        tags: dict[str, list[str]],
    ) -> int:
        text = f"{prompt.finalPrompt} {prompt.negativePrompt or ''}".lower()
        score = (
            self._specificity_score(prompt.finalPrompt)
            + self._asset_alignment_score(asset_type, prompt, text)
            + self._model_fit_score(target_model, prompt, text)
            + self._control_score(tags, text)
            + self._negative_score(tags, text)
            + self._direction_adjustment(text)
            - self._penalty_score(text)
        )
        if score >= 96 and not self._has_exceptional_control(text):
            score = 95
        return max(0, min(round(score), 100))

    def _specificity_score(self, final_prompt: str) -> int:
        text = final_prompt.lower()
        word_count = len(text.replace(",", " ").split())
        composition_hits = sum(1 for term in COMPOSITION_TERMS if term in text)

        score = 10
        if word_count >= 45:
            score += 6
        if word_count >= 90:
            score += 5
        if composition_hits >= 3:
            score += 5
        elif composition_hits:
            score += 2
        return min(score, 25)

    def _asset_alignment_score(
        self,
        asset_type: str,
        prompt: PromptAssetResult,
        text: str,
    ) -> int:
        score = 0
        normalized_type = asset_type.replace("_", " ").lower()
        normalized_name = prompt.assetName.replace("_", " ").lower()
        if normalized_type in text:
            score += 8
        if normalized_name in text:
            score += 5
        usability_hits = sum(1 for term in ASSET_USABILITY_TERMS if term in text)
        if usability_hits >= 3:
            score += 5
        elif usability_hits:
            score += 2
        if "sprite" in text or "asset" in text:
            score += 2
        return min(score, 20)

    def _model_fit_score(
        self,
        target_model: TargetModel,
        prompt: PromptAssetResult,
        text: str,
    ) -> int:
        if target_model == "novelai":
            comma_count = prompt.finalPrompt.count(",")
            score = 6
            if comma_count >= 12:
                score += 7
            if prompt.negativePrompt:
                score += 4
            if "game asset" in text or "2d sprite" in text:
                score += 3
            return min(score, 20)

        if target_model == "mock_seed":
            score = 8
            if "mock seed provider" in text:
                score += 5
            if "local seed png" in text or "generated-assets" in text:
                score += 4
            if "prompt metadata" in text:
                score += 3
            return min(score, 20)

        score = 6
        if "create" in text and "subject:" in text:
            score += 5
        if "technical requirements:" in text:
            score += 4
        if "avoid:" in text:
            score += 3
        if "\n" in prompt.finalPrompt:
            score += 2
        return min(score, 20)

    def _control_score(self, tags: dict[str, list[str]], text: str) -> int:
        technical_hits = sum(1 for tag in tags.get("technical", []) if tag.lower() in text)
        theme_hits = sum(1 for tag in tags.get("theme", []) if tag.lower() in text)
        subject_hits = sum(1 for tag in tags.get("subject", []) if tag.lower() in text)

        return min(20, technical_hits * 2 + theme_hits * 2 + subject_hits * 2)

    def _negative_score(self, tags: dict[str, list[str]], text: str) -> int:
        negative_hits = sum(1 for tag in tags.get("negative", []) if tag.lower() in text)
        if negative_hits >= 5:
            return 15
        if negative_hits >= 3:
            return 10
        if negative_hits:
            return 5
        return 0

    def _direction_adjustment(self, text: str) -> int:
        for direction, weight in DIRECTION_WEIGHTS.items():
            if direction.replace("_", " ") in text or direction in text:
                return weight
        if "stable game production" in text:
            return DIRECTION_WEIGHTS["production_safe"]
        if "stronger visual identity" in text:
            return DIRECTION_WEIGHTS["style_exploration"]
        if "richer material detail" in text:
            return DIRECTION_WEIGHTS["high_detail"]
        return 0

    def _penalty_score(self, text: str) -> int:
        penalty = sum(4 for term in OVERCOMPLEXITY_TERMS if term in text)
        if "no complex background" in text and "complex background" in text.replace(
            "no complex background", ""
        ):
            penalty += 5
        if len(text) > 1400:
            penalty += 4
        return penalty

    def _has_exceptional_control(self, text: str) -> bool:
        return all(
            term in text
            for term in [
                "clear silhouette",
                "centered composition",
                "readable at small size",
                "simple background",
                "game-ready asset",
                "no cropped subject",
            ]
        )
