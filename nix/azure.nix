{ config, lib, ... }:

with lib;

let
  cfg = config.services.cerebro.azure;
in
{
  options.services.cerebro.azure = {
    enable = mkEnableOption "Azure-tuned Cerebro runtime settings";

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
  };

  config = mkIf cfg.enable {
    services.cerebro.enable = mkDefault true;
    services.cerebro.provider = mkDefault "azure";

    systemd.services.cerebro-api.environment = {
      CEREBRO_LLM_PROVIDER = "azure";
      AZURE_OPENAI_ENDPOINT = cfg.endpoint;
      AZURE_OPENAI_CHAT_DEPLOYMENT = cfg.chatDeployment;
      AZURE_OPENAI_EMBED_DEPLOYMENT = cfg.embedDeployment;
      OPENAI_API_VERSION = cfg.apiVersion;
      AZURE_ACR_LOGIN_SERVER = cfg.acrLoginServer;
      AZURE_ACR_REPOSITORY = cfg.imageName;
      AZURE_IMAGE_TAG = cfg.imageTag;
    };
  };
}
