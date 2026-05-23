from pathlib import Path

from app.models.asset_models import ImageGenerationRequest
from app.providers.mock_image_provider import GENERATED_ASSET_DIR, MOCK_ASSET_DIR, MockImageProvider


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_mock_image_provider_generates_local_asset_path():
    provider = MockImageProvider()

    result = provider.generate(
        ImageGenerationRequest(
            generationId="gen-demo-001",
            assetName="bamboo_slime",
            assetType="enemy",
            style="pixel_art",
            theme="cyber bamboo forest",
            finalPrompt="Create an enemy sprite.",
        )
    )

    generated_path = Path(result.localPath)
    assert result.provider == "mock"
    assert result.assetName == "bamboo_slime"
    assert result.assetType == "enemy"
    assert result.localPath == "runtime/storage/generated-assets/gen_demo_001/enemy/bamboo_slime.png"
    assert result.metadata["mock"] is True
    assert result.metadata["promptHash"]
    assert generated_path.exists()
    assert generated_path.read_bytes().startswith(PNG_SIGNATURE)


def test_mock_image_provider_reuses_seed_asset():
    provider = MockImageProvider()

    first = provider.generate(
        ImageGenerationRequest(
            generationId="gen-demo-002",
            assetName="hero",
            assetType="character",
            style="pixel_art",
            theme="cyber bamboo forest",
            finalPrompt="Create a playable character sprite.",
        )
    )
    second = provider.generate(
        ImageGenerationRequest(
            generationId="gen-demo-003",
            assetName="hero_copy",
            assetType="character",
            style="pixel_art",
            theme="cyber bamboo forest",
            finalPrompt="Create another playable character sprite.",
        )
    )

    assert Path(first.metadata["sourcePath"]).exists()
    assert first.metadata["sourcePath"] == second.metadata["sourcePath"]


def test_mock_image_provider_sanitizes_unknown_asset_type():
    provider = MockImageProvider()

    result = provider.generate(
        ImageGenerationRequest(
            generationId="gen demo 004",
            assetName="Boss Portal!",
            assetType="boss portal",
            style="dark_fantasy",
            theme="ruined gate",
            finalPrompt="Create a portal boss prop.",
        )
    )

    assert result.localPath == "runtime/storage/generated-assets/gen_demo_004/boss_portal/boss_portal.png"
    assert Path(result.localPath).exists()
    assert (MOCK_ASSET_DIR / "boss_portal.png").exists()
    assert GENERATED_ASSET_DIR.joinpath("gen_demo_004", "boss_portal", "boss_portal.png").exists()
