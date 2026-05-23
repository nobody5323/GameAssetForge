import hashlib
import shutil
from pathlib import Path

from app.models.asset_models import GeneratedImage, ImageGenerationRequest
from app.providers.image_provider import ImageProvider
from app.utils.png_writer import write_solid_png


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
MOCK_ASSET_DIR = BACKEND_ROOT / "runtime" / "storage" / "mock-assets"
GENERATED_ASSET_DIR = BACKEND_ROOT / "runtime" / "storage" / "generated-assets"

ASSET_COLORS = {
    "character": (41, 173, 255),
    "enemy": (255, 0, 77),
    "item": (255, 236, 39),
    "tileset": (0, 228, 54),
    "ui": (255, 119, 168),
    "background": (106, 106, 138),
}


class MockImageProvider(ImageProvider):
    provider_name = "mock"

    def generate(self, request: ImageGenerationRequest) -> GeneratedImage:
        source_path = self._ensure_mock_asset(request.assetType)
        destination_path = self._destination_path(request)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination_path)

        return GeneratedImage(
            assetName=request.assetName,
            assetType=request.assetType,
            localPath=_relative_path(destination_path),
            provider=self.provider_name,
            metadata={
                "provider": self.provider_name,
                "sourcePath": _relative_path(source_path),
                "promptHash": _short_hash(request.finalPrompt),
                "promptVersion": request.promptVersion,
                "mock": True,
                "width": 64,
                "height": 64,
            },
        )

    def _ensure_mock_asset(self, asset_type: str) -> Path:
        normalized_type = _safe_slug(asset_type)
        path = MOCK_ASSET_DIR / f"{normalized_type}.png"
        if not path.exists():
            color = ASSET_COLORS.get(asset_type, _color_from_text(asset_type))
            write_solid_png(path, width=64, height=64, color=color)
        return path

    def _destination_path(self, request: ImageGenerationRequest) -> Path:
        generation_id = _safe_slug(request.generationId)
        asset_type = _safe_slug(request.assetType)
        asset_name = _safe_slug(request.assetName)
        return GENERATED_ASSET_DIR / generation_id / asset_type / f"{asset_name}.png"


def _safe_slug(value: str) -> str:
    slug = "".join(character if character.isalnum() else "_" for character in value.lower())
    return "_".join(part for part in slug.split("_") if part) or "asset"


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _color_from_text(value: str) -> tuple[int, int, int]:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return digest[0], digest[1], digest[2]


def _relative_path(path: Path) -> str:
    return path.relative_to(BACKEND_ROOT).as_posix()
