#!/usr/bin/env python3
"""
Auto-generator de queries para maximizar consumo de créditos com valor.
Gera 10k+ queries técnicas baseadas em templates.
"""

import itertools
import random
from pathlib import Path

# TEMPLATES DE QUERIES
TEMPLATES = {
    "howto": [
        "Como configurar {tech} no {os}?",
        "Como implementar {pattern} em {lang}?",
        "Como otimizar {component} em {framework}?",
        "Como fazer debug de {error} em {context}?",
        "Como integrar {techA} com {techB}?",
    ],
    "best_practices": [
        "Melhor prática para {concept} em {lang}?",
        "Padrão recomendado para {pattern} com {tech}?",
        "Arquitetura ideal para {scenario}?",
        "Code review checklist para {lang}?",
    ],
    "comparison": [
        "{techA} vs {techB}: qual escolher?",
        "Diferença entre {conceptA} e {conceptB}",
        "Quando usar {techA} ao invés de {techB}?",
        "Vantagens de {tech} sobre alternativas",
    ],
    "troubleshooting": [
        "Debug de {error} em {framework}",
        "Resolver {problem} no {context}",
        "Fix para {issue} em {tech}",
        "Troubleshooting de {symptom}",
    ],
    "advanced": [
        "Performance tuning de {service}",
        "Segurança em {component}",
        "Scaling {tech} para produção",
        "Monitoring de {service} com {tool}",
    ],
}

# VOCABULARY
TECH = [
    "Docker", "Kubernetes", "Terraform", "Ansible", "Nix", "NixOS",
    "PostgreSQL", "Redis", "MongoDB", "Elasticsearch", "Kafka",
    "Prometheus", "Grafana", "Vault", "Consul", "Nomad",
    "nginx", "traefik", "caddy", "HAProxy",
]

OS = ["NixOS", "Ubuntu", "Arch", "Debian", "Alpine", "Fedora"]

LANGUAGES = [
    "Python", "Rust", "Go", "JavaScript", "TypeScript", "Nix",
    "Bash", "C", "C++", "Java", "Kotlin", "Elixir",
]

FRAMEWORKS = [
    "Django", "FastAPI", "Flask", "Axum", "Actix", "Rocket",
    "React", "Vue", "Svelte", "Next.js", "Express", "NestJS",
]

PATTERNS = [
    "dependency injection", "middleware", "singleton", "factory",
    "repository pattern", "CQRS", "event sourcing", "saga pattern",
    "circuit breaker", "retry pattern", "bulkhead",
]

CONCEPTS = [
    "caching", "logging", "testing", "monitoring", "tracing",
    "authentication", "authorization", "encryption", "compression",
    "rate limiting", "load balancing", "service discovery",
]

ERRORS = [
    "segfault", "timeout", "OOM", "deadlock", "race condition",
    "connection refused", "broken pipe", "permission denied",
    "null pointer", "stack overflow",
]

SERVICES = [
    "API Gateway", "Auth Service", "Payment Gateway", "Email Service",
    "CDN", "Database", "Message Queue", "Cache Layer", "Search Engine",
]

PROBLEMS = [
    "memory leak", "high latency", "low throughput", "connection pool exhaustion",
    "CPU spike", "disk full", "network congestion",
]

# QUERIES ESPECÍFICAS DE NIXOS (alto valor)
NIXOS_QUERIES = [
    "Como configurar {package} no NixOS 24.11?",
    "Flake.nix exemplo para {service}",
    "Home-manager configuração para {tool}",
    "NixOS module para {service}",
    "Overlays no Nix para {package}",
    "Debug de rebuild loop no NixOS",
    "Nix desenvolver ambiente Python com {framework}",
    "NixOS container com {tech}",
    "Systemd service no NixOS para {daemon}",
]

NIXOS_PACKAGES = [
    "nvidia drivers", "docker", "podman", "postgresql", "redis",
    "vscode", "neovim", "tmux", "alacritty", "zsh", "fish",
]

# QUERIES DE CARREIRA (alto valor)
CAREER_QUERIES = [
    "System design: {scenario}",
    "Algoritmo {algorithm} explicação com exemplo",
    "LeetCode {difficulty}: {problem_type}",
    "Behavioral interview: {situation}",
    "Como demonstrar expertise em {tech} no portfolio",
    "Projeto open source {tech} para iniciantes",
]

ALGORITHMS = [
    "binary search", "quicksort", "mergesort", "DFS", "BFS",
    "dijkstra", "A*", "dynamic programming", "sliding window",
    "two pointers", "backtracking",
]

SCENARIOS = [
    "URL shortener", "rate limiter", "chat system", "file storage",
    "notification service", "recommendation engine", "search autocomplete",
]


def generate_from_template(template: str, vocab: dict, count: int) -> list[str]:
    """Gera queries a partir de template e vocabulário."""
    queries = []

    # Identificar placeholders no template
    import re
    placeholders = re.findall(r'\{(\w+)\}', template)

    # Gerar combinações
    if not placeholders:
        return [template] * min(count, 1)

    # Pegar valores do vocabulário
    vocab_lists = [vocab.get(ph, [ph]) for ph in placeholders]

    # Gerar combinações
    for combination in itertools.product(*vocab_lists):
        if len(queries) >= count:
            break
        query = template
        for placeholder, value in zip(placeholders, combination):
            query = query.replace(f"{{{placeholder}}}", value)
        queries.append(query)

    return queries[:count]


def generate_queries(total: int = 10000, seed: int = 42) -> list[str]:
    """Gera queries diversificadas."""
    random.seed(seed)
    queries = []

    vocab = {
        "tech": TECH,
        "techA": TECH,
        "techB": TECH,
        "os": OS,
        "lang": LANGUAGES,
        "framework": FRAMEWORKS,
        "pattern": PATTERNS,
        "concept": CONCEPTS,
        "conceptA": CONCEPTS,
        "conceptB": CONCEPTS,
        "error": ERRORS,
        "context": FRAMEWORKS + TECH,
        "component": SERVICES,
        "service": SERVICES,
        "problem": PROBLEMS,
        "tool": TECH,
        "scenario": SCENARIOS,
        "algorithm": ALGORITHMS,
    }

    # Distribuir queries por categoria
    per_category = total // (len(TEMPLATES) + 2)  # +2 para NixOS e Career

    # Templates gerais
    for category, templates in TEMPLATES.items():
        for template in templates:
            batch = generate_from_template(template, vocab, per_category // len(templates))
            queries.extend(batch)

    # NixOS específico (20% do total - alto valor)
    nixos_vocab = {**vocab, "package": NIXOS_PACKAGES, "service": TECH}
    for template in NIXOS_QUERIES:
        batch = generate_from_template(template, nixos_vocab, (total // 5) // len(NIXOS_QUERIES))
        queries.extend(batch)

    # Career queries (10% do total - alto valor)
    career_vocab = {
        **vocab,
        "algorithm": ALGORITHMS,
        "scenario": SCENARIOS,
        "difficulty": ["Easy", "Medium", "Hard"],
        "problem_type": ["array", "tree", "graph", "dp", "greedy"],
        "situation": ["conflict resolution", "failed project", "tight deadline"],
    }
    for template in CAREER_QUERIES:
        batch = generate_from_template(template, career_vocab, (total // 10) // len(CAREER_QUERIES))
        queries.extend(batch)

    # Shuffle e limitar
    random.shuffle(queries)
    queries = queries[:total]

    return queries


def save_queries(queries: list[str], output: Path):
    """Salva queries em arquivo."""
    output.write_text("\n".join(queries))
    print(f"✅ Generated {len(queries)} queries")
    print(f"💾 Saved to: {output}")
    print(f"💰 Estimated cost: ${len(queries) * 0.004:.2f} USD (~R$ {len(queries) * 0.004 * 5.5:.2f})")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate queries for credit burning")
    parser.add_argument("--count", type=int, default=10000, help="Number of queries")
    parser.add_argument("--output", type=str, default="queries.txt", help="Output file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    queries = generate_queries(total=args.count, seed=args.seed)
    save_queries(queries, Path(args.output))

    # Stats
    print(f"\n📊 Query Statistics:")
    print(f"   Total: {len(queries)}")
    print(f"   Unique: {len(set(queries))}")
    print(f"   Avg length: {sum(len(q) for q in queries) / len(queries):.1f} chars")

    # Samples
    print(f"\n🎯 Sample queries:")
    for i, q in enumerate(random.sample(queries, min(10, len(queries))), 1):
        print(f"   {i}. {q}")


if __name__ == "__main__":
    main()
