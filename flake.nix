{
  description = "Cerebro - Knowledge Extraction & RAG Framework";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      poetry2nix,
      sops-nix,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true; # For CUDA if needed
        };

        # GitLab Duo Configuration
        gitlabDuoConfig = {
          enabled = true;
          apiKey = builtins.getEnv "GITLAB_DUO_API_KEY";
          endpoint = "https://gitlab.com/api/v4";
          features = {
            codeCompletion = true;
            codeReview = true;
            securityScanning = true;
            documentationGeneration = true;
          };
          models = {
            codeGeneration = "claude-3-5-sonnet";
            codeReview = "claude-3-5-sonnet";
            security = "claude-3-5-sonnet";
          };
          rateLimit = {
            requestsPerMinute = 60;
            tokensPerMinute = 90000;
          };
          cache = {
            enabled = true;
            ttl = 3600; # 1 hour
          };
          logging = {
            level = "info";
            format = "json";
          };
        };

        corePythonPackages =
          ps: with ps; [
            # Core CLI & Utils
            pydantic
            typer
            rich
            tqdm
            python-dotenv
            pyyaml
            click
            chromadb
            psycopg
            sentence-transformers
            textual

            # Web Framework
            fastapi
            uvicorn

            # ML/AI: torch + transformers installed via Poetry (torch-bin quebrou no nixpkgs-unstable 2.10.0)
            # sentence-transformers também via Poetry

            # Code Analysis
            tree-sitter
            gitpython
            beautifulsoup4
            markdown
            pygments

            # Development tools
            pytest
            pytest-cov
            pytest-asyncio
            black
            isort
            ruff
            mypy
            types-pyyaml
            types-requests

            # Extra utils
            requests
            aiohttp
          ];

        # Runtime images and dev shells use the subset of Google Cloud SDKs
        # available in nixpkgs directly. The remaining vendor-specific pieces
        # still come from Poetry's optional `gcp` group in the dedicated shell.
        gcpPythonPackages =
          ps: with ps; [
            google-auth
            google-auth-httplib2
            google-auth-oauthlib
            google-api-core
            google-api-python-client
            googleapis-common-protos
            google-cloud-core
            google-cloud-artifact-registry
            google-cloud-bigquery
            google-cloud-bigquery-storage
            google-cloud-logging
            google-cloud-monitoring
            google-cloud-pubsub
            google-cloud-resource-manager
            google-cloud-run
            google-cloud-secret-manager
            google-cloud-storage
            google-crc32c
            google-resumable-media
          ];

        p2nix = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };

        mkPoetryApp =
          groups:
          p2nix.mkPoetryApplication {
            projectDir = self;
            python = pkgs.python313;
            inherit groups;
            checkGroups = [ ];
          };

        coreApp = mkPoetryApp [ "main" ];
        azureApp = mkPoetryApp [
          "main"
          "azure"
        ];
        gcpApp = mkPoetryApp [
          "main"
          "gcp"
        ];

        appSource = pkgs.runCommand "cerebro-app-source" { } ''
          mkdir -p "$out"
          cp -r ${self}/src "$out/src"
          cp ${self}/pyproject.toml "$out/pyproject.toml"
        '';

        mkApiEntrypoint =
          {
            pythonEnv,
            provider,
          }:
          pkgs.writeShellApplication {
            name = "cerebro-api";
            runtimeInputs = [ pythonEnv ];
            text = ''
              export CEREBRO_LLM_PROVIDER="''${CEREBRO_LLM_PROVIDER:-${provider}}"
              export CEREBRO_DATA_DIR="''${CEREBRO_DATA_DIR:-/workspace/data/intelligence}"
              export CEREBRO_VECTOR_DB="''${CEREBRO_VECTOR_DB:-/workspace/data/vector_db}"
              export PYTHONPATH="${appSource}/src:''${PYTHONPATH:-}"
              exec ${pythonEnv}/bin/uvicorn cerebro.api.server:app --host 0.0.0.0 --port "''${PORT:-8000}" "$@"
            '';
          };

        mkDockerImage =
          {
            name,
            pythonEnv,
            provider,
          }:
          let
            entrypoint = mkApiEntrypoint {
              inherit pythonEnv provider;
            };
          in
          pkgs.dockerTools.buildLayeredImage {
            inherit name;
            tag = "latest";
            contents = [
              pythonEnv
              entrypoint
              appSource
              pkgs.bash
              pkgs.coreutils
              pkgs.cacert
              pkgs.git
            ];
            extraCommands = ''
              mkdir -p workspace/data/intelligence
              mkdir -p workspace/data/vector_db
            '';
            config = {
              Cmd = [ (pkgs.lib.getExe entrypoint) ];
              WorkingDir = "/workspace";
              Env = [
                "PYTHONUNBUFFERED=1"
                "CEREBRO_JSON_LOGS=1"
                "CEREBRO_DATA_DIR=/workspace/data/intelligence"
                "CEREBRO_VECTOR_DB=/workspace/data/vector_db"
              ];
              ExposedPorts = {
                "8000/tcp" = { };
              };
            };
          };

        corePythonEnv = pkgs.python313.withPackages corePythonPackages;
        azurePythonEnv = pkgs.python313.withPackages (
          ps:
          (corePythonPackages ps)
          ++ [
            ps.langchain-openai
          ]
        );
        gcpPythonEnv = pkgs.python313.withPackages (ps: (corePythonPackages ps) ++ (gcpPythonPackages ps));

        commonBuildInputs = [
          pkgs.poetry
          pkgs.uv # Fast Python package installer
          pkgs.just
          pkgs.git
          pkgs.sops
          pkgs.age
          pkgs.gitleaks
          pkgs.syft
          pkgs.pip-audit
          pkgs.nodejs_20
          pkgs.gum  # Charmbracelet UI styling for premium terminal DX
          pkgs.stdenv.cc.cc.lib
          pkgs.zlib
          # pkgs.llama-cpp  # Removido: puxa CUDA pesado, instalar separado se necessário
        ];

        baseShellHook = ''
          export PYTHONPATH="$PWD/src:$PYTHONPATH"

          # Add cerebro script to PATH
          export PATH="$PWD:$PATH"

          # System libraries for compiled extensions
          export LD_LIBRARY_PATH="${
            pkgs.lib.makeLibraryPath [
              pkgs.stdenv.cc.cc.lib
              pkgs.zlib
              pkgs.stdenv.cc.libc
            ]
          }:$LD_LIBRARY_PATH"

          # Create necessary directories
          mkdir -p ./data/analyzed ./data/vector_db ./data/reports ./config/gitlab-duo

          # GitLab Duo Configuration
          export GITLAB_DUO_ENABLED=true
          export GITLAB_DUO_ENDPOINT="https://gitlab.com/api/v4"
          export GITLAB_DUO_FEATURES_CODE_COMPLETION=true
          export GITLAB_DUO_FEATURES_CODE_REVIEW=true
          export GITLAB_DUO_FEATURES_SECURITY_SCANNING=true
          export GITLAB_DUO_FEATURES_DOCUMENTATION=true
          export GITLAB_DUO_MODEL_CODE_GENERATION="claude-3-5-sonnet"
          export GITLAB_DUO_MODEL_CODE_REVIEW="claude-3-5-sonnet"
          export GITLAB_DUO_MODEL_SECURITY="claude-3-5-sonnet"
          export GITLAB_DUO_RATE_LIMIT_RPM=60
          export GITLAB_DUO_RATE_LIMIT_TPM=90000
          export GITLAB_DUO_CACHE_ENABLED=true
          export GITLAB_DUO_CACHE_TTL=3600
          export GITLAB_DUO_LOG_LEVEL="info"
          export GITLAB_DUO_LOG_FORMAT="json"

          # Load API key from secure location if available
          if [ -f ~/.config/gitlab-duo/api-key ]; then
            export GITLAB_DUO_API_KEY=$(cat ~/.config/gitlab-duo/api-key)
          fi

          # Project environment variables
          export CEREBRO_DATA_DIR="$PWD/data"
          export CEREBRO_VECTOR_DB="$PWD/data/vector_db"

          # ── Interface shortcuts ─────────────────────────────────────────────
          cdash() { cerebro dashboard "$@"; }   # React GUI → http://localhost:18321
          ctui()  { cerebro tui "$@"; }         # TUI Textual (terminal)

          # ── chelp: referência rápida ────────────────────────────────────────
          chelp() {
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "🧠 CEREBRO — Quick Reference"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "INTERFACES:"
            echo "  cerebro <command>            CLI  (principal — cerebro --help)"
            echo "  cdash                        Dashboard GUI  → http://localhost:18321"
            echo "  ctui                         TUI Textual    (terminal interativo)"
            echo ""
            echo "CEREBRO COMMANDS:"
            echo "  cerebro knowledge analyze <path>   Extrair AST do código"
            echo "  cerebro metrics scan               Métricas zero-token"
            echo "  cerebro rag ingest                 Ingerir no backend RAG configurado"
            echo "  cerebro rag query \"<question>\"    Query RAG com grounded generation"
            echo "  cerebro rag rerank <query>         Rerankar documentos"
            echo "  cerebro strategy optimize          Otimização de carreira/tech"
            echo "  cerebro ops health                 Health check completo"
            echo ""
            echo "OPTIONAL CLOUD:"
            echo "  nix develop .#gcp --command cerebro gcp status"
            echo ""
            echo "JUST TARGETS:"
            echo "  just test          Unit tests"
            echo "  just lint          Ruff linter"
            echo "  just pipeline      CI pipeline completo"
            echo "  just dashboard     Subir Dashboard GUI"
            echo "  just tui           Subir TUI"
            echo ""
            echo "  cerebro --help     Referência completa"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          }

          # ── Shell completion para cerebro ───────────────────────────────────
          if command -v cerebro &>/dev/null; then
            eval "$(cerebro --show-completion zsh 2>/dev/null)" 2>/dev/null || true
          fi

          # ── Sync do ambiente core (apenas na primeira vez) ──────────────────
          if [ -z "''${CI:-}" ] && [ ! -f ".nix-installed-core" ]; then
            gum style --foreground 212 "📥 Syncing Cerebro core dependencies via Poetry..."
            if [ -f "pyproject.toml" ]; then
              poetry install --no-root --only main --no-interaction 2>/dev/null || true
            fi
            touch .nix-installed-core
            gum style --foreground 42 "✅ Cerebro core ready!"
          fi

          # ── Interface Premium Terminal (DX) ───────────────────────────────
          if [ -z "''${CI:-}" ]; then
            clear
            gum style \
              --border double --border-foreground 99 --padding "1 2" \
              --margin "1 1" --align center \
              "$(gum style --foreground 42 --bold '🧠 CEREBRO')" \
              "Enterprise Knowledge Extraction & Distributed RAG Platform" \
              "$(gum style --foreground 240 'Environment: Reproducible Flake')"
            
            # Status Board
            export STATUS_COLOR="42"
            export ART_COLOR="42"
            if [ ! -f "./data/metrics/metrics_snapshot.json" ]; then export STATUS_COLOR="204" ; fi
            if [ ! -f "./data/analyzed/all_artifacts.jsonl" ]; then export ART_COLOR="204" ; fi

            gum style --margin "0 2" "$(gum style --foreground 81 --bold 'Python:') $(python --version 2>&1)"
            gum style --margin "0 2" "$(gum style --foreground 81 --bold 'LLM Core:') ''${CEREBRO_LLM_PROVIDER:-llamacpp}"
            echo ""
            gum style --margin "0 2" "$(gum style --foreground 220 'System State:')"
            gum style --margin "0 4" -- "- Metrics:   $(gum style --foreground $STATUS_COLOR 'Snapshot (cerebro metrics scan)')"
            gum style --margin "0 4" -- "- Artifacts: $(gum style --foreground $ART_COLOR 'Indexed (cerebro knowledge analyze .)')"
            
            echo ""
            gum style --border rounded --border-foreground 81 --padding "1 1" --margin "0 2" "$(gum style --foreground 212 --bold 'Run [ cerebro setup ] to configure models and APIs!')
Or type $(gum style --foreground 42 'chelp') for the quick reference guide."
          else
            echo "CEREBRO dev shell ready (CI mode)"
            echo "Python: $(python --version 2>&1)"
          fi
        '';

        gcpShellHook = ''
          export CEREBRO_GCP_SHELL_ACTIVE=1

          # Optional GCP configuration
          if [ -f ~/.config/gcloud/application_default_credentials.json ]; then
            export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/application_default_credentials.json
          fi

          export GCP_PROJECT_ID="''${GCP_PROJECT_ID:-}"
          export GCP_REGION="''${GCP_REGION:-us-central1}"

          if [ -z "''${CI:-}" ] && [ ! -f ".nix-installed-gcp" ]; then
            echo "☁️  Syncing optional GCP integration dependencies via Poetry..."
            if [ -f "pyproject.toml" ]; then
              poetry install --no-root --with gcp --no-interaction 2>/dev/null || true
            fi
            touch .nix-installed-gcp
            echo "✅ Cerebro optional GCP integration ready!"
          fi

          echo ""
          echo "Optional cloud integration shell active:"
          echo "  cerebro gcp status"
          echo "  cerebro gcp monitor"
          echo "  ./start_embedding_server.sh"
        '';

        azureShellHook = ''
          export CEREBRO_AZURE_SHELL_ACTIVE=1
          export AZURE_LOCATION="''${AZURE_LOCATION:-eastus2}"
          export OPENAI_API_VERSION="''${OPENAI_API_VERSION:-2024-10-21}"

          echo ""
          echo "Optional Azure integration shell active:"
          echo "  cerebro setup"
          echo "  export AZURE_OPENAI_ENDPOINT='https://<resource>.openai.azure.com/'"
          echo "  az account show"
        '';

      in
      {
        # Installable package — enables `nix build` and `nix run`
        packages.default = coreApp;
        packages.azure = azureApp;
        packages.gcp = gcpApp;
        packages.azureDockerImage = mkDockerImage {
          name = "cerebro-azure";
          pythonEnv = azurePythonEnv;
          provider = "azure";
        };
        packages.gcpDockerImage = mkDockerImage {
          name = "cerebro-gcp";
          pythonEnv = gcpPythonEnv;
          provider = "vertex-ai";
        };
        packages.dockerImage = self.packages.${system}.azureDockerImage;

        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [ corePythonEnv ] ++ commonBuildInputs;
          shellHook = baseShellHook;
        };

        devShells.gcp = pkgs.mkShell {
          buildInputs = [
            gcpPythonEnv
            pkgs.google-cloud-sdk
          ]
          ++ commonBuildInputs;
          shellHook = baseShellHook + gcpShellHook;
        };

        devShells.azure = pkgs.mkShell {
          buildInputs = [
            azurePythonEnv
            pkgs.azure-cli
          ]
          ++ commonBuildInputs;
          shellHook = baseShellHook + azureShellHook;
        };

      }
    ) // {
      nixosModules.default = import ./nix/module.nix;
      nixosModules.azure = import ./nix/azure.nix;
      nixosModules.gcp = import ./nix/gcp.nix;
    };
}
