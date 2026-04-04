{
  description = "Cerebro - Knowledge Extraction & RAG Framework";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    spider-nix.url = "path:/home/kernelcore/master/spider-nix";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      spider-nix,
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

        # Nixpkgs only covers part of the optional GCP surface used by Cerebro.
        # The remaining vendor-specific Python packages still come from Poetry's
        # optional `gcp` group in the dedicated gcp shell below.
        gcpPythonPackages =
          ps: with ps; [
            google-auth
            google-api-core
            google-cloud-core
            google-cloud-bigquery
            google-cloud-storage
          ];

        corePythonEnv = pkgs.python313.withPackages corePythonPackages;
        gcpPythonEnv = pkgs.python313.withPackages (
          ps: (corePythonPackages ps) ++ (gcpPythonPackages ps)
        );

        commonBuildInputs = [
          pkgs.poetry
          pkgs.uv # Fast Python package installer
          pkgs.just
          pkgs.git
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
          if [ ! -f ".nix-installed-core" ]; then
            echo "📥 Syncing Cerebro core dependencies via Poetry..."
            if [ -f "pyproject.toml" ]; then
              poetry install --no-root --only main --no-interaction 2>/dev/null || true
            fi
            touch .nix-installed-core
            echo "✅ Cerebro core ready!"
          fi

          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo "🧠 CEREBRO — Development Environment (Nix)"
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo "Python: $(python --version 2>&1)"
          echo ""
          echo "Status:"
          if [[ -f "./data/metrics/metrics_snapshot.json" ]]; then
            echo "  📊 Metrics snapshot present"
          else
            echo "  📊 No metrics snapshot  →  cerebro metrics scan"
          fi
          if [[ -f "./data/analyzed/all_artifacts.jsonl" ]]; then
            echo "  🧠 Artifacts ready"
          else
            echo "  🧠 No artifacts         →  cerebro knowledge analyze ."
          fi
          echo ""
          echo "Interfaces:"
          echo "  cerebro <cmd>    → CLI             (cerebro --help)"
          echo "  cdash            → Dashboard GUI   (http://localhost:18321)"
          echo "  ctui             → TUI Textual     (terminal)"
          echo ""
          echo "  chelp            → quick reference"
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        '';

        gcpShellHook = ''
          export CEREBRO_GCP_SHELL_ACTIVE=1

          # Optional GCP configuration
          if [ -f ~/.config/gcloud/application_default_credentials.json ]; then
            export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/application_default_credentials.json
          fi

          export GCP_PROJECT_ID="''${GCP_PROJECT_ID:-}"
          export GCP_REGION="''${GCP_REGION:-us-central1}"

          if [ ! -f ".nix-installed-gcp" ]; then
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

      in
      {
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [ corePythonEnv ] ++ commonBuildInputs;
          shellHook = baseShellHook;
        };

        devShells.gcp = pkgs.mkShell {
          buildInputs = [ gcpPythonEnv pkgs.google-cloud-sdk ] ++ commonBuildInputs;
          shellHook = baseShellHook + gcpShellHook;
        };

      }
    );
}
