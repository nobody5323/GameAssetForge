"""云存储 Provider 抽象接口。"""

from abc import ABC, abstractmethod


class CloudUploadResult:
    """上传结果。"""

    def __init__(self, cloud_url: str, provider: str, metadata: dict | None = None) -> None:
        self.cloud_url = cloud_url
        self.provider = provider
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"CloudUploadResult(provider={self.provider!r}, url={self.cloud_url!r})"


class CloudProvider(ABC):
    """云存储上传抽象接口。"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """返回 provider 标识名。"""
        ...

    @abstractmethod
    def upload(self, file_path: str, asset_id: str, asset_name: str) -> CloudUploadResult:
        """上传文件到云端，返回云端访问 URL。"""
        ...
