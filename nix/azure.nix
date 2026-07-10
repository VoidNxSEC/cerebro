{ config, lib, ... }:

with lib;

let
  cfg = config.services.cerebro.azure;
in
{
  options.services.cerebro.azure = {
    enable = mkEnableOption "Azure-tuned Cerebro runtime settings";

    location = mkOption {
      type = types.str;
      default = "eastus2";
      description = "Azure region/location used for OpenAI and container resources.";
    };

    resourceGroup = mkOption {
      type = types.str;
      default = "";
      description = "Azure Resource Group that owns the Cerebro deployment assets.";
    };

    endpoint = mkOption {
      type = types.str;
      default = "";
      description = "Azure OpenAI endpoint URL.";
    };

    chatDeployment = mkOption {
      type = types.str;
      default = "gpt-4o";
      description = "Azure OpenAI chat deployment name.";
    };

    embedDeployment = mkOption {
      type = types.str;
      default = "text-embedding-3-small";
      description = "Azure OpenAI embeddings deployment name.";
    };

    apiVersion = mkOption {
      type = types.str;
      default = "2024-10-21";
      description = "Azure OpenAI API version.";
    };

    acrLoginServer = mkOption {
      type = types.str;
      default = "";
      description = "Azure Container Registry login server.";
    };

    acrName = mkOption {
      type = types.str;
      default = "";
      description = "Azure Container Registry resource name.";
    };

    imageName = mkOption {
      type = types.str;
      default = "cerebro";
      description = "Container repository name inside ACR.";
    };

    imageTag = mkOption {
      type = types.str;
      default = "latest";
      description = "Container image tag.";
    };

    containerAppName = mkOption {
      type = types.str;
      default = "cerebro";
      description = "Azure Container Apps service name for the deployed container.";
    };

    searchServiceName = mkOption {
      type = types.str;
      default = "";
      description = "Azure AI Search service name used for retrieval-oriented features.";
    };

    searchIndexName = mkOption {
      type = types.str;
      default = "";
      description = "Azure AI Search index name used by Cerebro.";
    };
  };

  config = mkIf cfg.enable {
    services.cerebro.enable = mkDefault true;
    services.cerebro.provider = mkDefault "azure";

    systemd.services.cerebro-api.environment = {
      CEREBRO_LLM_PROVIDER = "azure";
      AZURE_LOCATION = cfg.location;
      AZURE_RESOURCE_GROUP = cfg.resourceGroup;
      AZURE_OPENAI_ENDPOINT = cfg.endpoint;
      AZURE_OPENAI_CHAT_DEPLOYMENT = cfg.chatDeployment;
      AZURE_OPENAI_EMBED_DEPLOYMENT = cfg.embedDeployment;
      OPENAI_API_VERSION = cfg.apiVersion;
      AZURE_ACR_NAME = cfg.acrName;
      AZURE_ACR_LOGIN_SERVER = cfg.acrLoginServer;
      AZURE_ACR_REPOSITORY = cfg.imageName;
      AZURE_IMAGE_TAG = cfg.imageTag;
      AZURE_CONTAINER_APP_NAME = cfg.containerAppName;
      AZURE_SEARCH_SERVICE_NAME = cfg.searchServiceName;
      AZURE_SEARCH_INDEX_NAME = cfg.searchIndexName;
    };
  };
}
