from abc import ABC, abstractmethod

from app.models.asset_models import GeneratedImage, ImageGenerationRequest


class ImageProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate(self, request: ImageGenerationRequest) -> GeneratedImage:
        raise NotImplementedError
