"""Azure-specific deployment metadata helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AzureDeploymentConfig:
    """Configuration required to publish and run Cerebro in Azure."""

    location: str = "eastus2"
    acr_name: str | None = None
    acr_login_server: str | None = None
    acr_repository: str = "cerebro"
    image_tag: str = "latest"
    resource_group: str | None = None
    container_app_name: str | None = None
    search_service_name: str | None = None
    search_index_name: str | None = None
    openai_endpoint: str | None = None
    openai_api_version: str | None = None
    openai_chat_deployment: str = "gpt-4o"
    openai_embed_deployment: str = "text-embedding-3-small"

    @classmethod
    def from_env(cls) -> AzureDeploymentConfig:
        """Create a config snapshot from the current process environment."""

        return cls(
            location=os.getenv("AZURE_LOCATION", "eastus2").strip(),
            acr_name=os.getenv("AZURE_ACR_NAME"),
            acr_login_server=os.getenv("AZURE_ACR_LOGIN_SERVER"),
            acr_repository=os.getenv("AZURE_ACR_REPOSITORY", "cerebro").strip(),
            image_tag=os.getenv("AZURE_IMAGE_TAG", "latest").strip(),
            resource_group=os.getenv("AZURE_RESOURCE_GROUP"),
            container_app_name=os.getenv("AZURE_CONTAINER_APP_NAME"),
            search_service_name=os.getenv("AZURE_SEARCH_SERVICE_NAME"),
            search_index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_version=os.getenv("OPENAI_API_VERSION"),
            openai_chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o").strip(),
            openai_embed_deployment=os.getenv(
                "AZURE_OPENAI_EMBED_DEPLOYMENT",
                "text-embedding-3-small",
            ).strip(),
        )

    @property
    def image_ref(self) -> str | None:
        """Return the full ACR image reference when enough fields are present."""

        if not self.acr_login_server or not self.acr_repository:
            return None
        return f"{self.acr_login_server}/{self.acr_repository}:{self.image_tag}"

    def missing_registry_fields(self) -> tuple[str, ...]:
        """Return the environment-backed fields required to publish to ACR."""

        missing: list[str] = []
        if not self.acr_name:
            missing.append("AZURE_ACR_NAME")
        if not self.acr_login_server:
            missing.append("AZURE_ACR_LOGIN_SERVER")
        if not self.acr_repository:
            missing.append("AZURE_ACR_REPOSITORY")
        return tuple(missing)

    def missing_runtime_fields(self) -> tuple[str, ...]:
        """Return the non-secret runtime fields expected by the Azure provider."""

        missing: list[str] = []
        if not self.openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not self.openai_api_version:
            missing.append("OPENAI_API_VERSION")
        if not self.openai_chat_deployment:
            missing.append("AZURE_OPENAI_CHAT_DEPLOYMENT")
        if not self.openai_embed_deployment:
            missing.append("AZURE_OPENAI_EMBED_DEPLOYMENT")
        return tuple(missing)

    def required_secret_env_names(self) -> tuple[str, ...]:
        """Return secret env names that must be supplied out-of-band."""

        return ("AZURE_OPENAI_API_KEY",)

    def runtime_env(self) -> dict[str, str]:
        """Return the non-secret runtime environment for an Azure deployment."""

        env = {
            "CEREBRO_LLM_PROVIDER": "azure",
            "AZURE_LOCATION": self.location,
            "AZURE_OPENAI_CHAT_DEPLOYMENT": self.openai_chat_deployment,
            "AZURE_OPENAI_EMBED_DEPLOYMENT": self.openai_embed_deployment,
        }
        if self.resource_group:
            env["AZURE_RESOURCE_GROUP"] = self.resource_group
        if self.container_app_name:
            env["AZURE_CONTAINER_APP_NAME"] = self.container_app_name
        if self.search_service_name:
            env["AZURE_SEARCH_SERVICE_NAME"] = self.search_service_name
        if self.search_index_name:
            env["AZURE_SEARCH_INDEX_NAME"] = self.search_index_name
        if self.openai_endpoint:
            env["AZURE_OPENAI_ENDPOINT"] = self.openai_endpoint
        if self.openai_api_version:
            env["OPENAI_API_VERSION"] = self.openai_api_version
        return env
