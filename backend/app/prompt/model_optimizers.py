from app.models.prompt_models import PromptAssetRequest, PromptDirection, TargetModel
from app.prompt.chinese_translator import sanitize_prompt, translate_chinese_text


DIRECTION_NOTES: dict[PromptDirection, str] = {
    "quick_start": "Create a concise first-pass prompt for fast iteration with the core subject, style, theme, and basic usability constraints.",
    "production_safe": "Prioritize stable game production use, clear silhouette, centered composition, simple background, and simple readable shapes.",
    "style_exploration": "Push a stronger visual identity, distinctive color palette, stylized lighting, memorable shape language, and bolder mood.",
    "high_detail": "Add richer material detail, layered lighting, ornate surface texture, and showcase polish while keeping the asset readable and game-ready.",
}


def _subject_anchor(asset_type: str) -> str:
    """Danbooru subject anchor tag — essential for NovelAI character prompting."""
    return {
        "character": "1girl, solo",
        "enemy": "monster, solo",
        "item": "item, solo, simple background",
        "tileset": "scenery, no humans",
        "ui": "ui, simple background",
        "background": "scenery, no humans",
    }.get(asset_type, "solo")


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
        if target_model == "mock_seed":
            return self._mock_seed_prompt(asset, tags, direction, project_context)
        if target_model == "novelai":
            return self._novelai_prompt(asset, tags, direction, project_context)
        return self._gpt_image_prompt(asset, tags, direction, project_context)

    def _mock_seed_prompt(
        self,
        asset: PromptAssetRequest,
        tags: dict[str, list[str]],
        direction: PromptDirection,
        project_context: str,
    ) -> tuple[str, None]:
        prompt = "\n".join(
            [
                "Mock Seed Prompt Profile",
                "Provider: local Mock Seed Provider",
                "External model call: disabled",
                f"Project context: {project_context}",
                f"Seed selection: choose backend/runtime/storage/mock-assets/{asset.type}.png, or create it if missing.",
                f"Copy target: backend/runtime/storage/generated-assets/{{generationId}}/{asset.type}/{asset.name}.png",
                f"Asset name: {asset.name}",
                f"Asset type: {asset.type}",
                f"Asset description: {asset.description}",
                f"Direction profile: {direction}",
                f"Metadata style tags: {', '.join(tags['style'])}",
                f"Metadata theme tags: {', '.join(tags['theme'])}",
                "Metadata to attach: provider=mock, mock=true, promptHash, promptVersion, sourcePath, width=64, height=64.",
                "Generation behavior: copy the matching local seed PNG into generated-assets and return the localPath.",
            ]
        )
        return prompt, None

    def _gpt_image_prompt(
        self,
        asset: PromptAssetRequest,
        tags: dict[str, list[str]],
        direction: PromptDirection,
        project_context: str,
    ) -> tuple[str, None]:
        if direction == "quick_start":
            prompt = "\n".join(
                [
                    "Create a simple 2D game asset concept.",
                    f"Project context: {project_context}",
                    f"Asset type: {translate_chinese_text(asset.type)}",
                    f"Subject: {translate_chinese_text(asset.description)}",
                    f"Style: {', '.join(tags['style'])}",
                    f"Theme: {', '.join(tags['theme'])}",
                    "Technical requirements: clear silhouette, centered composition, game-ready asset",
                    "Avoid: no text, no watermark, no blurry edges",
                ]
            )
            return sanitize_prompt(prompt), None

        prompt = "\n".join(
            [
                "Create a production-ready 2D game asset.",
                f"Project context: {project_context}",
                f"Asset type: {translate_chinese_text(asset.type)}",
                f"Subject: {translate_chinese_text(asset.description)}",
                f"Direction: {DIRECTION_NOTES[direction]}",
                f"Direction profile: {direction}",
                f"Style tags: {', '.join(tags['style'])}",
                f"Theme tags: {', '.join(tags['theme'])}",
                f"Environment and mood: {', '.join(tags['environment'] + tags['mood'])}",
                f"Technical requirements: {', '.join(tags['technical'])}",
                f"Avoid: {', '.join(tags['negative'])}",
            ]
        )
        return sanitize_prompt(prompt), None

    def _novelai_prompt(
        self,
        asset: PromptAssetRequest,
        tags: dict[str, list[str]],
        direction: PromptDirection,
        project_context: str,
    ) -> tuple[str, str]:
        subject_anchor = _subject_anchor(asset.type)
        appearance = [
            translate_chinese_text(asset.name.replace("_", " ")),
            translate_chinese_text(asset.description),
        ]

        if direction == "quick_start":
            positive_tags = [
                "masterpiece",
                "best quality",
                subject_anchor,
                *filter(None, appearance),
                *tags["style"],
                *tags["theme"],
            ]
            negative_prompt = ", ".join([
                "lowres", "bad anatomy", "bad hands", "worst quality",
                "low quality", "normal quality", "jpeg artifacts",
                "signature", "watermark", "blurry",
            ])
            return sanitize_prompt(", ".join(filter(None, positive_tags))), negative_prompt

        # Professional: full Danbooru tag structure
        # quality → subject → appearance → style → theme → setting → mood
        positive_tags = [
            "masterpiece",
            "best quality",
            "amazing quality",
            "very aesthetic",
            "absurdres",
            "rating:general",
            subject_anchor,
            *filter(None, appearance),
            *tags["style"],
            *tags["theme"],
            *tags["environment"],
            *tags["mood"],
        ]
        negative_prompt = ", ".join([
            "lowres", "bad anatomy", "bad hands", "text", "error",
            "missing fingers", "extra digit", "fewer digits", "cropped",
            "worst quality", "low quality", "normal quality", "jpeg artifacts",
            "signature", "watermark", "username", "blurry",
        ])
        return sanitize_prompt(", ".join(filter(None, positive_tags))), negative_prompt
