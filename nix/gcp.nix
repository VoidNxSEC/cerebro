{ config, lib, ... }:

with lib;

let
  cfg = config.services.cerebro.gcp;
in
{
  options.services.cerebro.gcp = {
    enable = mkEnableOption "Google Cloud tuned Cerebro runtime settings";

    projectId = mkOption {
      type = types.str;
      default = "";
      description = "Google Cloud project ID.";
    };

    region = mkOption {
      type = types.str;
      default = "us-central1";
      description = "Google Cloud region.";
    };

    dataStoreId = mkOption {
      type = types.str;
      default = "";
      description = "Discovery Engine data store ID.";
    };

    artifactRepository = mkOption {
      type = types.str;
      default = "cerebro";
      description = "Artifact Registry repository name.";
    };

    imageName = mkOption {
      type = types.str;
      default = "cerebro";
      description = "Container image name inside Artifact Registry.";
    };

    imageTag = mkOption {
      type = types.str;
      default = "latest";
      description = "Container image tag.";
    };

    cloudRunService = mkOption {
      type = types.str;
      default = "cerebro";
      description = "Cloud Run service name for the deployed container.";
    };
  };

  config = mkIf cfg.enable {
    services.cerebro.enable = mkDefault true;
    services.cerebro.provider = mkDefault "vertex-ai";

    systemd.services.cerebro-api.environment = {
      CEREBRO_LLM_PROVIDER = "vertex-ai";
      GCP_PROJECT_ID = cfg.projectId;
      GCP_REGION = cfg.region;
      DATA_STORE_ID = cfg.dataStoreId;
      GCP_ARTIFACT_REGISTRY_REPOSITORY = cfg.artifactRepository;
      GCP_IMAGE_NAME = cfg.imageName;
      GCP_IMAGE_TAG = cfg.imageTag;
      GCP_CLOUD_RUN_SERVICE = cfg.cloudRunService;
    };
  };
}
