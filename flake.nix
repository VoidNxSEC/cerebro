{
  description = "PHANTOM Cerebro - Knowledge Extraction & RAG Framework";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
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

        # Python environment with project dependencies from nixpkgs
        # Note: Some deps (langchain-*, google-cloud-*) need Poetry for now
        pythonEnv = pkgs.python313.withPackages (
          ps: with ps; [
            # Core CLI & Utils
            pydantic
            typer
            rich
            tqdm
            python-dotenv
            pyyaml
            click

            # Google Cloud (basic)
            google-auth
            google-api-core
            google-cloud-core

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
          ]
        );

      in
      {
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.poetry
            pkgs.uv # Fast Python package installer
            pkgs.google-cloud-sdk
            pkgs.just
            pkgs.git
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
            # pkgs.llama-cpp  # Removido: puxa CUDA pesado, instalar separado se necessário
          ];

          shellHook = ''
            export PYTHONPATH="$PWD/src:$PYTHONPATH"

            # Python path for development
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

            # GCP configuration
            if [ -f ~/.config/gcloud/application_default_credentials.json ]; then
              export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/application_default_credentials.json
            fi
# Project environment variables
export CEREBRO_DATA_DIR="$PWD/data"
export CEREBRO_VECTOR_DB="$PWD/data/vector_db"
export GCP_PROJECT_ID="gen-lang-client-0530325234"
export GCP_REGION="us-central1"

# Aliases for common cerebro commands
alias cscan='cerebro metrics scan'
alias canalyze='cerebro knowledge analyze'
alias cingest='cerebro rag ingest'
alias cquery='cerebro rag query'
alias crerank='cerebro rag rerank'

            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "🧠 PHANTOM CEREBRO - Development Environment (Nix-managed)"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Python: $(python --version)"
            echo "Nix:    Fully declarative, reproducible dependencies ⚡"

            # Hybrid approach: Nix for base deps, Poetry for unavailable ones
            if [ ! -f ".nix-installed" ]; then
              echo "📥 Installing cerebro (Nix base + Poetry fallback)..."

              # Install missing deps via Poetry first (langchain, chromadb, google-cloud-*)
              if [ -f "pyproject.toml" ]; then
                echo "⚡ Installing missing deps via Poetry..."
                poetry install --no-root --only main --no-interaction 2>/dev/null || true
              fi

              # Install project in dev mode (creates cerebro/phantom scripts)
              echo "📦 Installing cerebro scripts..."
              pip install -e . --no-build-isolation 2>/dev/null

              touch .nix-installed
              echo "✅ Cerebro ready!"
            fi

            echo ""
            echo "Available commands:"
            echo "  cerebro ops health           - Verify GCP, Quotas and Environment"
            echo "  cerebro knowledge analyze .  - Extract AST from current repo"
            echo "  cerebro rag ingest           - Index artifacts to ChromaDB"
            echo "  cerebro rag query \"...\"      - Query the Knowledge Base"
            echo "  cerebro rag rerank           - Rerank retrieved documents with cross‑encoder"
            echo "  just pipeline                - Run full validation (test + lint)"
            echo "  pytest tests/                - Run unit tests"
            echo ""
            echo "Current status:"
            if [[ -f "./data/metrics/metrics_snapshot.json" ]]; then
              echo "  📊 Metrics snapshot present"
            else
              echo "  📊 No metrics snapshot (run 'cscan')"
            fi
            if [[ -f "./data/analyzed/all_artifacts.jsonl" ]]; then
              echo "  🧠 Artifacts ready"
            else
              echo "  🧠 No artifacts (run 'canalyze')"
            fi
            echo ""
            echo "Data directories:"
            echo "  ./data/analyzed     - Analyzed artifacts"
            echo "  ./data/vector_db    - Vector database"
            echo "  ./data/reports      - Analysis reports"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          '';
        };

      }
    );
}
