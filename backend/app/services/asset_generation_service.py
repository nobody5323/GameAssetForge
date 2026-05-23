from uuid import uuid4

from app.models.asset_models import (
    AssetGenerateResponse,
    AssetGenerateRequest,
    AssetRecord,
    ImageGenerationRequest,
)
from app.models.prompt_models import PromptCompileRequest
from app.prompt.prompt_compiler import PromptCompiler
from app.providers.mock_image_provider import MockImageProvider
from app.repositories.asset_repository import AssetRepository

PROMPT_VERSION = "prompt-v1"


class AssetGenerationService:
    def __init__(self):
        self.prompt_compiler = PromptCompiler()
        self.image_provider = MockImageProvider()
        self.asset_repository = AssetRepository()

    def generate(self, request: AssetGenerateRequest) -> AssetGenerateResponse:
        generation_id = f"gen_{uuid4().hex[:12]}"
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

        for prompt_asset in selected_candidate.assets:
            generated = self.image_provider.generate(
                ImageGenerationRequest(
                    generationId=generation_id,
                    assetName=prompt_asset.assetName,
                    assetType=prompt_asset.assetType,
                    style=request.style,
                    theme=request.theme,
                    finalPrompt=prompt_asset.finalPrompt,
                    promptVersion=PROMPT_VERSION,
                )
            )
            records.append(
                AssetRecord(
                    id=f"asset_{uuid4().hex[:12]}",
                    generationId=generation_id,
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

        self.asset_repository.save_generation(generation_id, records)
        return AssetGenerateResponse(
            generationId=generation_id,
            provider=self.image_provider.provider_name,
            promptProvider=prompt_response.provider,
            fallback=prompt_response.fallback,
            assets=records,
        )
