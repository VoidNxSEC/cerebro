# nix/cerebro.nix
#
# Standalone buildPythonPackage derivation for upstream nixpkgs submission.
# Does NOT use poetry2nix — follows the nixpkgs convention directly.
#
# Usage (in a nixpkgs overlay or pkgs/development/python-modules/):
#   cerebro-cli = pkgs.python313Packages.callPackage ./nix/cerebro.nix {};
#
# Large or CUDA-dependent packages (torch, dspy-ai, accelerate, bitsandbytes)
# are intentionally excluded and must be provided via separate overlay entries.
# Optional provider SDKs (anthropic, groq, google-generativeai) are also
# excluded; users install them via `poetry install --with <group>`.

{
  lib,
  buildPythonPackage,
  pythonOlder,
  poetry-core,
  # Core runtime dependencies (all available in nixpkgs):
  fastapi,
  uvicorn,
  chromadb,
  sentence-transformers,
  transformers,
  typer,
  rich,
  tqdm,
  python-dotenv,
  pyyaml,
  click,
  textual,
  tree-sitter,
  gitpython,
  beautifulsoup4,
  markdown,
  pygments,
  pydantic,
  langchain,
  langchain-chroma,
  langchain-community,
  langchain-text-splitters,
  websockets,
  aiofiles,
  nats-py,
}:

buildPythonPackage rec {
  pname = "cerebro-cli";
  version = "1.0.0b1";
  pyproject = true;

  disabled = pythonOlder "3.13";

  src = ../.;

  build-system = [ poetry-core ];

  dependencies = [
    fastapi
    uvicorn
    chromadb
    sentence-transformers
    transformers
    typer
    rich
    tqdm
    python-dotenv
    pyyaml
    click
    textual
    tree-sitter
    gitpython
    beautifulsoup4
    markdown
    pygments
    pydantic
    langchain
    langchain-chroma
    langchain-community
    langchain-text-splitters
    websockets
    aiofiles
    nats-py
  ];

  pythonImportsCheck = [ "cerebro" ];

  meta = {
    description = "Cerebro — Enterprise Knowledge Extraction Platform";
    homepage = "https://github.com/VoidNxSEC/cerebro";
    license = lib.licenses.mit;
    mainProgram = "cerebro";
    maintainers = [ marcosfpina ];
  };
}
