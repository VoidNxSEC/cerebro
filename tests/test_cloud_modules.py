from cerebro.modules.azure import AzureDeploymentConfig
from cerebro.modules.gcp import GcpDeploymentConfig


def test_azure_deployment_config_from_env(monkeypatch):
    monkeypatch.setenv("AZURE_ACR_NAME", "cerebroacr")
    monkeypatch.setenv("AZURE_ACR_LOGIN_SERVER", "cerebroacr.azurecr.io")
    monkeypatch.setenv("AZURE_ACR_REPOSITORY", "cerebro")
    monkeypatch.setenv("AZURE_IMAGE_TAG", "sha123")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("OPENAI_API_VERSION", "2024-10-21")
    monkeypatch.setenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")

    config = AzureDeploymentConfig.from_env()

    assert config.image_ref == "cerebroacr.azurecr.io/cerebro:sha123"
    assert config.missing_registry_fields() == ()
    assert config.missing_runtime_fields() == ()
    assert config.runtime_env()["CEREBRO_LLM_PROVIDER"] == "azure"


def test_azure_deployment_config_reports_missing_fields(monkeypatch):
    monkeypatch.delenv("AZURE_ACR_NAME", raising=False)
    monkeypatch.delenv("AZURE_ACR_LOGIN_SERVER", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("OPENAI_API_VERSION", raising=False)

    config = AzureDeploymentConfig.from_env()

    assert "AZURE_ACR_NAME" in config.missing_registry_fields()
    assert "AZURE_ACR_LOGIN_SERVER" in config.missing_registry_fields()
    assert "AZURE_OPENAI_ENDPOINT" in config.missing_runtime_fields()
    assert "OPENAI_API_VERSION" in config.missing_runtime_fields()


def test_gcp_deployment_config_from_env(monkeypatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "cerebro-prod")
    monkeypatch.setenv("GCP_REGION", "us-central1")
    monkeypatch.setenv("GCP_ARTIFACT_REGISTRY_REPOSITORY", "cerebro")
    monkeypatch.setenv("GCP_IMAGE_NAME", "cerebro")
    monkeypatch.setenv("GCP_IMAGE_TAG", "sha456")
    monkeypatch.setenv("DATA_STORE_ID", "discovery-engine")

    config = GcpDeploymentConfig.from_env()

    assert (
        config.image_ref
        == "us-central1-docker.pkg.dev/cerebro-prod/cerebro/cerebro:sha456"
    )
    assert config.missing_registry_fields() == ()
    assert config.missing_runtime_fields() == ()
    assert config.runtime_env()["CEREBRO_LLM_PROVIDER"] == "vertex-ai"


def test_gcp_deployment_config_reports_missing_fields(monkeypatch):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("DATA_STORE_ID", raising=False)

    config = GcpDeploymentConfig.from_env()

    assert "GCP_PROJECT_ID" in config.missing_registry_fields()
    assert "GCP_PROJECT_ID" in config.missing_runtime_fields()
    assert "DATA_STORE_ID" in config.missing_runtime_fields()
