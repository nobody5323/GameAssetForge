"""云端配置 API 测试 + Qiniu Provider 测试。"""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import create_app
from app.services.cloud_service import CloudService


app = create_app()
client = TestClient(app)


# ── Cloud Config API ──


class TestCloudConfigAPI:
    def test_get_cloud_config_returns_defaults(self):
        # Reset to mock first (previous tests may have persisted qiniu)
        client.put(
            "/api/config/cloud",
            json={"provider": "mock", "clearCredentials": True},
        )
        response = client.get("/api/config/cloud")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "mock"
        assert data["hasCredentials"] is False

    def test_update_cloud_config_switches_to_qiniu(self):
        response = client.put(
            "/api/config/cloud",
            json={
                "provider": "qiniu",
                "accessKey": "test-ak",
                "secretKey": "test-sk",
                "bucket": "test-bucket",
                "domain": "https://cdn.example.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "qiniu"
        assert data["hasCredentials"] is True
        assert data["bucket"] == "test-bucket"
        assert data["domain"] == "https://cdn.example.com"

    def test_clear_credentials(self):
        # First set credentials
        client.put(
            "/api/config/cloud",
            json={
                "provider": "qiniu",
                "accessKey": "test-ak",
                "secretKey": "test-sk",
                "bucket": "test-bucket",
            },
        )
        # Then clear
        response = client.put(
            "/api/config/cloud",
            json={"provider": "mock", "clearCredentials": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hasCredentials"] is False

    def test_secret_key_not_returned(self):
        client.put(
            "/api/config/cloud",
            json={
                "provider": "qiniu",
                "accessKey": "test-ak",
                "secretKey": "test-sk",
                "bucket": "test-bucket",
            },
        )
        response = client.get("/api/config/cloud")
        data = response.json()
        # Secret key should never be returned
        assert "secretKey" not in data
        assert "accessKey" not in data


# ── Qiniu Provider ──


class TestQiniuCloudProvider:
    def test_qiniu_provider_upload_success(self):
        from pathlib import Path
        from app.providers.qiniu_cloud_provider import QiniuCloudProvider

        # Create a temp file
        tmp = Path(__file__).parent / "_test_qiniu_upload.png"
        tmp.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100 + b"IEND\xaeB`\x82")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("app.providers.qiniu_cloud_provider.cloud_runtime_config") as cfg:
            cfg.access_key = "test-ak"
            cfg.secret_key = "test-sk"
            cfg.bucket = "test-bucket"
            cfg.domain = "https://cdn.example.com"

            with patch("app.providers.qiniu_cloud_provider.put_file") as mock_put:
                mock_put.return_value = ({"hash": "abc123"}, mock_response)

                provider = QiniuCloudProvider()
                result = provider.upload(str(tmp), "asset_123", "test_asset")

        tmp.unlink(missing_ok=True)

        assert result.provider == "qiniu"
        assert result.cloud_url.startswith("https://cdn.example.com/")
        assert "asset_123" in result.cloud_url
        assert result.metadata["qiniu_hash"] == "abc123"

    def test_qiniu_provider_missing_file(self):
        from app.providers.qiniu_cloud_provider import QiniuCloudProvider

        provider = QiniuCloudProvider()
        try:
            provider.upload("/nonexistent/path.png", "id", "name")
            raise AssertionError("Expected FileNotFoundError")
        except FileNotFoundError:
            pass

    def test_qiniu_provider_no_credentials_raises(self):
        from app.providers.qiniu_cloud_provider import QiniuCloudProvider

        with patch("app.providers.qiniu_cloud_provider.cloud_runtime_config") as cfg:
            cfg.access_key = ""
            cfg.secret_key = ""
            cfg.bucket = ""

            provider = QiniuCloudProvider()
            try:
                provider.upload(__file__, "id", "name")
                raise AssertionError("Expected RuntimeError")
            except RuntimeError as e:
                assert "凭证" in str(e)


# ── Cloud Service Provider Selection ──


class TestCloudServiceSelection:
    def test_cloud_service_uses_mock_by_default(self):
        with patch("app.services.cloud_service.cloud_runtime_config") as cfg:
            cfg.provider = "mock"
            cfg.is_qiniu_available.return_value = False
            service = CloudService()
            assert service.provider_name == "mock_cloud"

    def test_cloud_service_uses_qiniu_when_configured(self):
        with patch("app.services.cloud_service.cloud_runtime_config") as cfg:
            cfg.provider = "qiniu"
            cfg.is_qiniu_available.return_value = True

            service = CloudService()
            assert service.provider_name == "qiniu"

    def test_cloud_service_falls_back_to_mock_without_credentials(self):
        with patch("app.services.cloud_service.cloud_runtime_config") as cfg:
            cfg.provider = "qiniu"
            cfg.is_qiniu_available.return_value = False

            service = CloudService()
            assert service.provider_name == "mock_cloud"
