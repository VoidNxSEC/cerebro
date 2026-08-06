"""
Metrics Profiles — Repository Taxonomy & Profile-Weighted Health Rubric

Separates four concepts that the collector used to collapse into one number:

  A. Measurement    what physically exists in the repo (LoC buckets)
  B. Classification what *kind* of project this is        -> Archetype
  C. Position       what tier of the stack it sits in     -> StackLayer
  D. Evaluation     is it healthy *for what it is*        -> profile-weighted score

The old rubric applied a single freshness-and-presence checklist to every repo, which
inverted the ranking: a personal CLI tool with recent commits outscored a tagged
production service, and repos whose whole purpose is security hardening scored lowest
because a regex counted the word "token" in their own source.

Here a dimension may be N/A for an archetype. A docs site is not penalised for having
no unit tests; a knowledge base is not penalised for being mostly prose. Weights are
renormalised over the dimensions that actually apply.

Zero LLM tokens consumed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# ---------------------------------------------------------------------------
# B. Classification — what kind of project is this
# ---------------------------------------------------------------------------


class Archetype(StrEnum):
    SERVICE = "service"
    MCP_SERVER = "mcp-server"
    CLI_TOOL = "cli-tool"
    LIBRARY = "library"
    INFRA_CONFIG = "infra-config"
    KNOWLEDGE_BASE = "knowledge-base"
    FRONTEND = "frontend"
    DOCS_SITE = "docs-site"
    RESEARCH = "research"
    UNKNOWN = "unknown"


class StackLayer(StrEnum):
    BACKBONE = "backbone"
    INFERENCE = "inference"
    RAG = "rag"
    AGENTS_OS = "agents-os"
    SECURITY = "security"
    DEV = "dev"
    FRONTEND = "frontend"
    DOCS = "docs"
    UNKNOWN = "unknown"


# Curated layer map. Mirrors the ecosystem table in ~/master/deploy/CLAUDE.md, which is
# the operator's own classification — inferring it from the filesystem would be guessing
# at something already decided.
LAYER_MAP: dict[str, StackLayer] = {
    "securellm-bridge": StackLayer.BACKBONE,
    "securellm-mcp": StackLayer.BACKBONE,
    "spectre": StackLayer.BACKBONE,
    "neoland": StackLayer.BACKBONE,
    "ml-ops-api": StackLayer.BACKBONE,
    "spooknix": StackLayer.INFERENCE,
    "cerebro": StackLayer.RAG,
    "cerebro-reranker": StackLayer.RAG,
    "ai-agent-os": StackLayer.AGENTS_OS,
    "intelagent": StackLayer.AGENTS_OS,
    "neotron": StackLayer.AGENTS_OS,
    "owasaka": StackLayer.SECURITY,
    "adr-ledger": StackLayer.SECURITY,
    "phantom": StackLayer.SECURITY,
    "sentinel": StackLayer.SECURITY,
    "chainscope": StackLayer.SECURITY,
    "nixos": StackLayer.DEV,
    "arch-analyzer": StackLayer.DEV,
    "spider-nix": StackLayer.DEV,
    "swissknife": StackLayer.DEV,
    "voidnxlabs-workflows": StackLayer.DEV,
    "voidnx-api": StackLayer.FRONTEND,
}

# Archetype overrides for repos whose character is a deliberate decision rather than
# something the filesystem reveals. adr-ledger is mostly Markdown *by design* — the
# corpus is the product, not undocumented code.
ARCHETYPE_MAP: dict[str, Archetype] = {
    "adr-ledger": Archetype.KNOWLEDGE_BASE,
    "securellm-mcp": Archetype.MCP_SERVER,
    "nixos": Archetype.INFRA_CONFIG,
    "voidnxlabs-workflows": Archetype.INFRA_CONFIG,
    "neotron": Archetype.RESEARCH,
    "intelagent": Archetype.RESEARCH,
    "ai-agent-os": Archetype.RESEARCH,
    # sentinel's product *is* its test suite — it validates the rest of the ecosystem
    # end to end, so it is judged as a released, reproducible artifact rather than as
    # a service that happens to have no endpoints.
    "sentinel": Archetype.LIBRARY,
}

_DOCS_SITE_MARKERS = {"mkdocs.yml", "mkdocs.yaml", "docusaurus.config.js", "book.toml", "_config.yml"}
_FRONTEND_DEPS = ("react", "vue", "svelte", "next", "vite", "astro")
_SERVER_DEPS = ("fastapi", "starlette", "flask", "django", "axum", "actix", "express", "hyper", "tokio")
_CLI_DEPS = ("typer", "click", "clap", "argparse", "cobra")


def classify_archetype(
    name: str,
    *,
    deps: list[str],
    loc_authored: int,
    loc_docs: int,
    filenames: set[str],
    has_dockerfile: bool,
    primary_language: str,
    total_commits: int,
    has_ci: bool,
    tags: int,
    endpoints: int = 0,
    modules: int = 0,
    cli_commands: int = 0,
) -> Archetype:
    """Infer project character. Curated overrides win; heuristics fill the rest."""
    if name in ARCHETYPE_MAP:
        return ARCHETYPE_MAP[name]

    dep_blob = " ".join(deps).lower()
    lname = name.lower()

    has_surface = endpoints > 0 or cli_commands > 0

    # Name conventions in this ecosystem are load-bearing and unambiguous.
    if lname.endswith(("-docs", "-wiki")):
        return Archetype.DOCS_SITE
    if lname.endswith("-gui"):
        return Archetype.FRONTEND
    if "mcp" in lname:
        return Archetype.MCP_SERVER

    # Docs tooling is not a docs site. cerebro ships mkdocs.yml alongside a Dockerfile
    # and 47 HTTP endpoints; publishing your documentation does not reclassify the
    # thing being documented.
    if (filenames & _DOCS_SITE_MARKERS) and not has_surface:
        return Archetype.DOCS_SITE
    # Prose dominating authored code, with no service surface, is a docs artifact.
    if loc_docs > loc_authored * 3 and loc_authored < 2_000 and not has_surface:
        return Archetype.DOCS_SITE

    if any(d in dep_blob for d in _FRONTEND_DEPS) and "index.html" in filenames:
        return Archetype.FRONTEND
    if primary_language == "Nix" or (filenames & {"configuration.nix"}) or modules > 20:
        return Archetype.INFRA_CONFIG
    # Dependency manifests are frequently unparseable (Cargo workspaces, uv, pnpm
    # catalogs), so trust what the source demonstrably does before trusting the manifest.
    # Where a repo exposes both, the larger surface decides what it primarily is.
    if cli_commands > endpoints and cli_commands > 0:
        return Archetype.CLI_TOOL
    if endpoints > 0 or has_dockerfile or any(d in dep_blob for d in _SERVER_DEPS):
        return Archetype.SERVICE
    if cli_commands > 0 or any(d in dep_blob for d in _CLI_DEPS):
        return Archetype.CLI_TOOL

    # Low-signal repos are exploratory, not degraded production.
    if total_commits < 30 and not has_ci and tags == 0:
        return Archetype.RESEARCH

    return Archetype.UNKNOWN


def classify_layer(name: str, archetype: Archetype) -> StackLayer:
    if name in LAYER_MAP:
        return LAYER_MAP[name]
    if archetype is Archetype.FRONTEND:
        return StackLayer.FRONTEND
    if archetype is Archetype.DOCS_SITE:
        return StackLayer.DOCS
    if archetype in (Archetype.CLI_TOOL, Archetype.INFRA_CONFIG):
        return StackLayer.DEV
    return StackLayer.UNKNOWN


# ---------------------------------------------------------------------------
# D. Evaluation — ten dimensions, weighted per profile
# ---------------------------------------------------------------------------


class Dimension(StrEnum):
    CENTRALITY = "centrality"
    SUSTAINED_DELIVERY = "sustained_delivery"
    RELEASE_DISCIPLINE = "release_discipline"
    REPRODUCIBILITY = "reproducibility"
    INTERFACE_SURFACE = "interface_surface"
    TEST_DEPTH = "test_depth"
    SECURITY_POSTURE = "security_posture"
    OPERABILITY = "operability"
    ARCHITECTURE_DEPTH = "architecture_depth"
    KNOWLEDGE_ARTIFACTS = "knowledge_artifacts"
    ADOPTION = "adoption"


D = Dimension

# Weight tables per archetype. A dimension absent from a table is N/A for that archetype
# and is excluded from the score rather than counted as zero — the distinction between
# "did badly" and "does not apply" is the whole point of this module.
PROFILE_WEIGHTS: dict[Archetype, dict[Dimension, float]] = {
    Archetype.SERVICE: {
        D.CENTRALITY: 0.13,
        D.SUSTAINED_DELIVERY: 0.09,
        D.RELEASE_DISCIPLINE: 0.08,
        D.REPRODUCIBILITY: 0.10,
        D.INTERFACE_SURFACE: 0.09,
        D.TEST_DEPTH: 0.11,
        D.SECURITY_POSTURE: 0.11,
        D.OPERABILITY: 0.17,  # keeping it running is harder than writing it
        D.ARCHITECTURE_DEPTH: 0.05,
        D.ADOPTION: 0.07,
        # knowledge artifacts: N/A — a service documents itself in ARCHITECTURE.md,
        # which architecture_depth already accounts for
    },
    Archetype.MCP_SERVER: {
        D.CENTRALITY: 0.18,  # an MCP server is definitionally a hub
        D.SUSTAINED_DELIVERY: 0.09,
        D.RELEASE_DISCIPLINE: 0.09,
        D.REPRODUCIBILITY: 0.11,
        D.INTERFACE_SURFACE: 0.14,  # the tool registry *is* the product
        D.TEST_DEPTH: 0.11,
        D.SECURITY_POSTURE: 0.09,
        D.OPERABILITY: 0.08,
        D.ARCHITECTURE_DEPTH: 0.04,
        D.ADOPTION: 0.07,
    },
    Archetype.CLI_TOOL: {
        D.SUSTAINED_DELIVERY: 0.14,
        D.RELEASE_DISCIPLINE: 0.18,  # a CLI is consumed via releases
        D.REPRODUCIBILITY: 0.18,
        D.INTERFACE_SURFACE: 0.13,
        D.TEST_DEPTH: 0.18,
        D.ARCHITECTURE_DEPTH: 0.09,
        D.ADOPTION: 0.10,
        # centrality / operability: N/A — not a networked runtime
    },
    Archetype.LIBRARY: {
        D.CENTRALITY: 0.18,
        D.SUSTAINED_DELIVERY: 0.09,
        D.RELEASE_DISCIPLINE: 0.18,
        D.REPRODUCIBILITY: 0.13,
        D.INTERFACE_SURFACE: 0.09,
        D.TEST_DEPTH: 0.18,
        D.ARCHITECTURE_DEPTH: 0.05,
        D.ADOPTION: 0.10,
    },
    Archetype.INFRA_CONFIG: {
        D.CENTRALITY: 0.12,
        D.SUSTAINED_DELIVERY: 0.14,
        D.REPRODUCIBILITY: 0.24,  # the flake *is* the contract
        D.INTERFACE_SURFACE: 0.12,  # exported modules
        D.SECURITY_POSTURE: 0.14,
        D.OPERABILITY: 0.10,  # a daily-driver config is operated, not just built
        D.ARCHITECTURE_DEPTH: 0.08,
        D.ADOPTION: 0.06,
        # test_depth: N/A — `nix flake check` is the test surface, already scored
        # under reproducibility
    },
    Archetype.KNOWLEDGE_BASE: {
        D.CENTRALITY: 0.19,  # downstream consumers of the corpus
        D.SUSTAINED_DELIVERY: 0.14,
        D.RELEASE_DISCIPLINE: 0.09,
        D.REPRODUCIBILITY: 0.09,
        D.SECURITY_POSTURE: 0.19,  # signing / attestation chain
        D.ARCHITECTURE_DEPTH: 0.09,
        D.KNOWLEDGE_ARTIFACTS: 0.14,
        D.ADOPTION: 0.07,
        # test_depth: N/A — schema validation lives in security_posture
        # a high docs:code ratio is *expected here*, never a penalty
    },
    Archetype.FRONTEND: {
        D.SUSTAINED_DELIVERY: 0.18,
        D.RELEASE_DISCIPLINE: 0.14,
        D.REPRODUCIBILITY: 0.09,  # deliberately light: npm lock is the norm
        D.INTERFACE_SURFACE: 0.14,
        D.TEST_DEPTH: 0.23,
        D.ARCHITECTURE_DEPTH: 0.14,
        D.ADOPTION: 0.08,
    },
    Archetype.DOCS_SITE: {
        D.SUSTAINED_DELIVERY: 0.32,  # freshness is the quality bar for docs
        D.REPRODUCIBILITY: 0.13,
        D.KNOWLEDGE_ARTIFACTS: 0.45,
        D.ADOPTION: 0.10,
        # test_depth / operability / security: N/A
    },
    Archetype.RESEARCH: {
        D.SUSTAINED_DELIVERY: 0.32,
        D.KNOWLEDGE_ARTIFACTS: 0.36,
        D.ARCHITECTURE_DEPTH: 0.22,
        D.ADOPTION: 0.10,
        # everything else N/A — exploratory work is not degraded production and
        # must not be scored as though it were
    },
    Archetype.UNKNOWN: {
        D.SUSTAINED_DELIVERY: 0.22,
        D.REPRODUCIBILITY: 0.18,
        D.TEST_DEPTH: 0.22,
        D.ARCHITECTURE_DEPTH: 0.13,
        D.KNOWLEDGE_ARTIFACTS: 0.13,
        D.ADOPTION: 0.12,
    },
}

# Layers that raise the bar on specific dimensions. A backbone service and a dev tool
# can both be `service`, but only one of them takes the whole platform down with it.
LAYER_EMPHASIS: dict[StackLayer, dict[Dimension, float]] = {
    StackLayer.BACKBONE: {D.OPERABILITY: 1.4, D.CENTRALITY: 1.3, D.TEST_DEPTH: 1.2},
    StackLayer.SECURITY: {D.SECURITY_POSTURE: 1.5, D.TEST_DEPTH: 1.2},
    StackLayer.RAG: {D.TEST_DEPTH: 1.2, D.OPERABILITY: 1.2},
    StackLayer.INFERENCE: {D.OPERABILITY: 1.3},
    StackLayer.AGENTS_OS: {D.ARCHITECTURE_DEPTH: 1.2},
    StackLayer.DEV: {D.RELEASE_DISCIPLINE: 1.2},
}


@dataclass
class HealthResult:
    """Profile-aware score. `score` is only comparable within the same profile."""

    score: float = 0.0
    profile: str = ""
    dimensions: dict[str, float] = field(default_factory=dict)
    na_dimensions: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "profile": self.profile,
            "dimensions": self.dimensions,
            "na_dimensions": self.na_dimensions,
            "weights": self.weights,
        }


def score_repo(
    archetype: Archetype,
    layer: StackLayer,
    dimension_scores: dict[Dimension, float | None],
) -> HealthResult:
    """Weighted mean over applicable dimensions only.

    A dimension is applicable when the archetype's profile assigns it a weight *and*
    the collector produced a value. Weights are renormalised over what remains, so a
    docs site is never dragged down by tests it was never supposed to have.
    """
    base = PROFILE_WEIGHTS.get(archetype, PROFILE_WEIGHTS[Archetype.UNKNOWN])
    emphasis = LAYER_EMPHASIS.get(layer, {})

    applicable: dict[Dimension, float] = {}
    for dim, weight in base.items():
        value = dimension_scores.get(dim)
        if value is None:
            continue
        applicable[dim] = weight * emphasis.get(dim, 1.0)

    # N/A means "this profile does not ask for it" or "no value could be collected".
    # Anything scored must not also appear here, or the report contradicts itself.
    na = sorted(d.value for d in Dimension if d not in applicable)

    if not applicable:
        return HealthResult(profile=f"{archetype}/{layer}", na_dimensions=na)

    total_weight = sum(applicable.values())
    score = sum(
        (dimension_scores[dim] or 0.0) * w for dim, w in applicable.items()
    ) / total_weight

    return HealthResult(
        score=round(score, 1),
        profile=f"{archetype}/{layer}",
        dimensions={d.value: round(dimension_scores[d] or 0.0, 1) for d in applicable},
        na_dimensions=na,
        weights={d.value: round(w / total_weight, 3) for d, w in applicable.items()},
    )
