from fastapi.testclient import TestClient

from app.config import llm_runtime_config
from app.main import app
from app.models.config_models import LlmConfigUpdate


def test_llm_config_can_be_updated_without_returning_api_key():
    client = TestClient(app)
    original = llm_runtime_config.public_response()
    original_api_key = llm_runtime_config.api_key

    response = client.put(
        "/api/config/llm",
        json={
            "provider": "openai",
            "baseUrl": "https://example.test/v1/",
            "promptModel": "gpt-5-mini",
            "apiKey": "sk-test-secret",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "provider": "openai",
        "baseUrl": "https://example.test/v1",
        "promptModel": "gpt-5-mini",
        "hasApiKey": True,
    }
    assert "sk-test-secret" not in response.text

    llm_runtime_config.provider = original.provider
    llm_runtime_config.base_url = original.baseUrl
    llm_runtime_config.prompt_model = original.promptModel
    llm_runtime_config.api_key = original_api_key


def test_llm_config_clear_api_key():
    client = TestClient(app)
    original = llm_runtime_config.public_response()
    original_api_key = llm_runtime_config.api_key

    response = client.put(
        "/api/config/llm",
        json={
            "provider": "rule_fallback",
            "baseUrl": "https://api.openai.com/v1",
            "promptModel": "gpt-5-mini",
            "clearApiKey": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "rule_fallback"
    assert response.json()["hasApiKey"] is False

    llm_runtime_config.update(
        LlmConfigUpdate(
            provider=original.provider,
            baseUrl=original.baseUrl,
            promptModel=original.promptModel,
            apiKey=original_api_key,
        )
    )
