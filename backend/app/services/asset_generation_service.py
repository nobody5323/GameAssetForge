from uuid import uuid4

from app.models.asset_models import (
    AssetGenerateResponse,
    AssetGenerateRequest,
    AssetRecord,
    ImageGenerationRequest,
)
from app.models.prompt_models import PromptCompileRequest
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
