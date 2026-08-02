"""Google Cloud specific deployment metadata helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GcpDeploymentConfig:
    """Configuration required to publish and run Cerebro in Google Cloud."""

    project_id: str | None = None
    region: str = "us-central1"
    artifact_repository: str = "cerebro"
    image_name: str = "cerebro"
    image_tag: str = "latest"
    cloud_run_service: str | None = None
    data_store_id: str | None = None

    @classmethod
    def from_env(cls) -> GcpDeploymentConfig:
        """Create a config snapshot from the current process environment."""

        return cls(
            project_id=os.getenv("GCP_PROJECT_ID"),
            region=os.getenv("GCP_REGION", "us-central1").strip(),
            artifact_repository=os.getenv(
                "GCP_ARTIFACT_REGISTRY_REPOSITORY",
                "cerebro",
            ).strip(),
            image_name=os.getenv("GCP_IMAGE_NAME", "cerebro").strip(),
            image_tag=os.getenv("GCP_IMAGE_TAG", "latest").strip(),
            cloud_run_service=os.getenv("GCP_CLOUD_RUN_SERVICE"),
            data_store_id=os.getenv("DATA_STORE_ID"),
        )

    @property
    def registry_host(self) -> str:
        """Return the Artifact Registry host for the configured region."""

        return f"{self.region}-docker.pkg.dev"

    @property
    def image_ref(self) -> str | None:
        """Return the full Artifact Registry image reference when possible."""

        if not self.project_id or not self.artifact_repository or not self.image_name:
            return None
        return (
            f"{self.registry_host}/{self.project_id}/"
            f"{self.artifact_repository}/{self.image_name}:{self.image_tag}"
        )

    def missing_registry_fields(self) -> tuple[str, ...]:
        """Return the environment-backed fields required to publish an image."""

        missing: list[str] = []
        if not self.project_id:
            missing.append("GCP_PROJECT_ID")
        if not self.artifact_repository:
            missing.append("GCP_ARTIFACT_REGISTRY_REPOSITORY")
        if not self.image_name:
            missing.append("GCP_IMAGE_NAME")
        return tuple(missing)

    def missing_runtime_fields(self) -> tuple[str, ...]:
        """Return the non-secret runtime fields expected by the GCP provider."""

        missing: list[str] = []
        if not self.project_id:
            missing.append("GCP_PROJECT_ID")
        if not self.data_store_id:
            missing.append("DATA_STORE_ID")
        return tuple(missing)

    def required_secret_env_names(self) -> tuple[str, ...]:
        """Return secret env names that must be supplied out-of-band."""

        return ("GOOGLE_APPLICATION_CREDENTIALS",)

    def runtime_env(self) -> dict[str, str]:
        """Return the non-secret runtime environment for a GCP deployment."""

        env = {
            "CEREBRO_LLM_PROVIDER": "vertex-ai",
            "GCP_REGION": self.region,
        }
        if self.project_id:
            env["GCP_PROJECT_ID"] = self.project_id
        if self.data_store_id:
            env["DATA_STORE_ID"] = self.data_store_id
        return env
