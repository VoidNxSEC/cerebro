{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.services.cerebro;
in
{
  options.services.cerebro = {
    enable = mkEnableOption "Cerebro RAG Engine & Dashboard";

    provider = mkOption {
      type = types.enum [ "llamacpp" "azure" "vertex-ai" ];
      default = "azure";
      description = "The primary LLM provider to bind to Cerebro.";
    };

    secretsFile = mkOption {
      type = types.path;
      description = "Path to the sops-encrypted secrets file containing AZURE_OPENAI_API_KEY, ELASTICSEARCH_PASSWORD, etc.";
    };
  };

  config = mkIf cfg.enable {
    # Assuming sops-nix is evaluated alongside this module on the host system.
    sops.secrets."cerebro/env" = {
      sopsFile = cfg.secretsFile;
      format = "dotenv";
      # The service runner will need access to this
      owner = config.systemd.services.cerebro-api.serviceConfig.User or "root";
    };

    systemd.services.cerebro-api = {
      description = "Cerebro Logic & RAG API";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      
      serviceConfig = {
        # Dynamically inject the plaintext environments safely at runtime:
        EnvironmentFile = [ config.sops.secrets."cerebro/env".path ];
        Environment = [
          "CEREBRO_LLM_PROVIDER=${cfg.provider}"
        ];
        
        ExecStart = "${pkgs.poetry}/bin/poetry run uvicorn cerebro.launcher:app --host 127.0.0.1 --port 8000";
        Restart = "always";
        User = "cerebro";
        DynamicUser = true;
      };
    };
  };
}
