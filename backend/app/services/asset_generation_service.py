from uuid import uuid4

from app.models.asset_models import (
    AssetGenerateResponse,
    AssetGenerateRequest,
    AssetRecord,
    ImageGenerationRequest,
)
from app.models.prompt_models import PromptCompileRequest
from app.presets.secondary_presets import build_action_prompt, get_presets_for_type
from app.prompt.prompt_compiler import PromptCompiler
from app.providers.gpt_image_provider import GptImageProvider
from app.providers.image_provider import ImageProvider
from app.providers.mock_image_provider import MockImageProvider
from app.repositories.asset_repository import AssetRepository

PROMPT_VERSION = "prompt-v1"


class AssetGenerationService:
    def __init__(self):
        self.prompt_compiler = PromptCompiler()
        self.mock_provider = MockImageProvider()
        self.gpt_provider = GptImageProvider()
        self.asset_repository = AssetRepository()

    def _select_provider(self, target_model: str) -> ImageProvider:
        """Select an image provider based on the target model.

        Falls back to MockImageProvider when the requested real provider
        has no credentials configured.
        """
        if target_model == "gpt_image":
            if self.gpt_provider.is_available():
                return self.gpt_provider
            return self.mock_provider
        return self.mock_provider

    def generate(self, request: AssetGenerateRequest) -> AssetGenerateResponse:
        generation_id = f"gen_{uuid4().hex[:12]}"
        image_provider = self._select_provider(request.targetModel)

        prompt_response = self.prompt_compiler.compile(
            PromptCompileRequest(
                mode=request.promptMode,
                targetModel=request.targetModel,
                projectName=request.projectName,
                gameType=request.gameType,
                style=request.style,
                theme=request.theme,
                description=request.description,
                assets=[
                    {
                        "type": asset.type,
                        "name": asset.name,
                        "description": asset.description,
                    }
                    for asset in request.assets
                ],
            )
        )
        selected_candidate = prompt_response.candidates[0]
        records: list[AssetRecord] = []
        errors: list[str] = []

        for prompt_asset in selected_candidate.assets:
            try:
                generated = image_provider.generate(
                    ImageGenerationRequest(
                        generationId=generation_id,
                        assetName=prompt_asset.assetName,
                        assetType=prompt_asset.assetType,
                        style=request.style,
                        theme=request.theme,
                        finalPrompt=prompt_asset.finalPrompt,
                        negativePrompt=prompt_asset.negativePrompt,
                        promptVersion=PROMPT_VERSION,
                    )
                )
                records.append(
                    AssetRecord(
                        id=f"asset_{uuid4().hex[:12]}",
                        generationId=generation_id,
                        projectName=request.projectName,
                        assetName=prompt_asset.assetName,
                        assetType=prompt_asset.assetType,
                        style=request.style,
                        theme=request.theme,
                        finalPrompt=prompt_asset.finalPrompt,
                        promptVersion=PROMPT_VERSION,
                        localPath=generated.localPath,
                        provider=generated.provider,
                        providerMetadata=generated.metadata,
                    )
                )
            except Exception as exc:
                msg = f"{prompt_asset.assetType}/{prompt_asset.assetName}: {exc}"
                errors.append(msg)

        if not records and errors:
            # All assets failed — raise the first error
            raise RuntimeError(errors[0])

        self.asset_repository.save_generation(generation_id, records)
        return AssetGenerateResponse(
            generationId=generation_id,
            provider=image_provider.provider_name,
            promptProvider=prompt_response.provider,
            fallback=prompt_response.fallback,
            assets=records,
            errors=errors,
        )

    def regenerate_asset(
        self,
        original_asset: AssetRecord,
        action: str,
        custom_prompt: str | None = None,
    ) -> AssetRecord:
        presets = get_presets_for_type(original_asset.assetType)
        if not presets:
            raise ValueError(f"Asset type '{original_asset.assetType}' does not support secondary generation")

        action_prompt = build_action_prompt(original_asset.assetType, action)
        if not action_prompt:
            raise ValueError(f"Unknown action '{action}' for asset type '{original_asset.assetType}'")

        # 用原图的 finalPrompt 精确复现角色，不依赖参考图（micuapi.ai 不支持图片输入）
        prompt_parts = [
            f"Generate EXACTLY this character: {original_asset.finalPrompt}",
            f"Now show this SAME character in a new pose: {action_prompt}.",
            f"CRITICAL: This must be the IDENTICAL character from the description above. "
            "Same appearance, same hair, same eyes, same outfit, same art style, same color scheme. "
            "ONLY the pose/action changes.",
        ]
        if custom_prompt:
            prompt_parts.append(f"Additional requirements: {custom_prompt}")
        prompt_parts.append(
            "Maintain visual consistency with the original asset's style and art direction. "
            "Game-ready 2D asset, clear silhouette, centered composition. No text, no watermark."
        )
        final_prompt = " ".join(prompt_parts)

        regen_id = f"regen_{uuid4().hex[:12]}"
        image_request = ImageGenerationRequest(
            generationId=regen_id,
            assetName=f"{original_asset.assetName}_{action}",
            assetType=original_asset.assetType,
            style=original_asset.style,
            theme=original_asset.theme,
            finalPrompt=final_prompt,
            negativePrompt=None,
            promptVersion=PROMPT_VERSION,
            # micuapi.ai 不支持 image_url，不传参考图，靠原 finalPrompt 文本复现
        )
        image_provider = self._select_provider("gpt_image")
        fallback_reason = ""

        try:
            generated = image_provider.generate(image_request)
        except Exception as exc:
            if image_provider is self.mock_provider:
                raise
            fallback_reason = str(exc)
            generated = self.mock_provider.generate(image_request)
            generated.metadata.update({
                "fallbackFrom": image_provider.provider_name,
                "fallbackReason": fallback_reason[:500],
            })

        new_asset = AssetRecord(
            id=f"asset_{uuid4().hex[:12]}",
            generationId=regen_id,
            projectName=original_asset.projectName,
            assetName=f"{original_asset.assetName}_{action}",
            assetType=original_asset.assetType,
            style=original_asset.style,
            theme=original_asset.theme,
            finalPrompt=final_prompt,
            promptVersion=PROMPT_VERSION,
            localPath=generated.localPath,
            provider=generated.provider,
            providerMetadata=generated.metadata,
            parentAssetId=original_asset.id,
        )

        self.asset_repository.save_generation(regen_id, [new_asset])
        return new_asset
