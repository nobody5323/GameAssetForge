from app.models.prompt_models import PromptAssetRequest, PromptDirection, TargetModel


DIRECTION_NOTES: dict[PromptDirection, str] = {
    "production_safe": "Prioritize stable game production use, clear silhouette, and simple readable shapes.",
    "style_exploration": "Push a stronger visual identity, distinctive color language, and memorable style.",
    "high_detail": "Add richer material detail while keeping the asset readable and game-ready.",
}


class PromptOptimizer:
    def optimize(
        self,
        *,
        target_model: TargetModel,
        asset: PromptAssetRequest,
        tags: dict[str, list[str]],
        direction: PromptDirection,
        project_context: str,
    ) -> tuple[str, str | None]:
        if target_model == "novelai":
            return self._novelai_prompt(asset, tags, direction, project_context)
        return self._gpt_image_prompt(asset, tags, direction, project_context)

    def _gpt_image_prompt(
        self,
        asset: PromptAssetRequest,
        tags: dict[str, list[str]],
        direction: PromptDirection,
        project_context: str,
    ) -> tuple[str, None]:
        prompt = "\n".join(
            [
                "Create a production-ready 2D game asset.",
                f"Project context: {project_context}",
                f"Asset type: {asset.type}",
                f"Subject: {asset.description}",
                f"Direction: {DIRECTION_NOTES[direction]}",
                f"Style tags: {', '.join(tags['style'])}",
                f"Theme tags: {', '.join(tags['theme'])}",
                f"Environment and mood: {', '.join(tags['environment'] + tags['mood'])}",
                f"Technical requirements: {', '.join(tags['technical'])}",
                f"Avoid: {', '.join(tags['negative'])}",
            ]
        )
        return prompt, None

    def _novelai_prompt(
        self,
        asset: PromptAssetRequest,
        tags: dict[str, list[str]],
        direction: PromptDirection,
        project_context: str,
    ) -> tuple[str, str]:
        positive_tags = [
            "best quality",
            "game asset",
            "2d sprite",
            asset.type.replace("_", " "),
            asset.name.replace("_", " "),
            asset.description,
            DIRECTION_NOTES[direction],
            project_context,
            *tags["style"],
            *tags["theme"],
            *tags["environment"],
            *tags["mood"],
            *tags["technical"],
        ]
        negative_prompt = ", ".join(tags["negative"] + ["low quality", "bad anatomy"])
        return ", ".join(filter(None, positive_tags)), negative_prompt
