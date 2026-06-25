#!/usr/bin/env python3
"""
TREND PREDICTOR - Identifica tech emergente ANTES de virar mainstream
Analisa GitHub trending, HN, e Reddit para gerar queries sobre futuro.

ROI: Early mover advantage = ser expert quando tech explode
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import subprocess

class TrendPredictor:
    def __init__(self):
        self.github_trending_url = "https://api.github.com/search/repositories"
        self.hn_algolia_url = "http://hn.algolia.com/api/v1/search"

    def get_github_emerging(self, days: int = 7) -> List[Dict]:
        """Repos que estão crescendo RÁPIDO mas ainda pequenos (early signal)."""

        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Estratégia: 100-1000 stars (não muito pequeno, não mainstream)
        # Criado nos últimos 3 meses
        # Stars/day > 10 (momentum)

        params = {
            "q": f"created:>{since} stars:100..1000",
            "sort": "stars",
            "order": "desc",
            "per_page": 50,
        }

        response = requests.get(self.github_trending_url, params=params)
        repos = response.json().get("items", [])

        # Filter por momentum (stars/day)
        trending = []
        for repo in repos:
            created = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
            days_old = (datetime.now(created.tzinfo) - created).days
            if days_old > 0:
                stars_per_day = repo["stargazers_count"] / days_old
                if stars_per_day > 5:  # High momentum
                    trending.append({
                        "name": repo["full_name"],
                        "description": repo["description"],
                        "language": repo["language"],
                        "stars": repo["stargazers_count"],
                        "stars_per_day": round(stars_per_day, 2),
                        "topics": repo.get("topics", []),
                        "url": repo["html_url"],
                    })

        return sorted(trending, key=lambda x: x["stars_per_day"], reverse=True)

    def get_hn_emerging_topics(self, days: int = 7) -> List[Dict]:
        """HN posts sobre tech nova com alto engajamento."""

        since = int((datetime.now() - timedelta(days=days)).timestamp())

        # Buscar posts com tech keywords
        tech_keywords = [
            "new language", "new framework", "alternative to",
            "faster than", "replaces", "next generation",
            "rust", "zig", "gleam", "mojo", "bun",
            "webassembly", "wasm", "wasi", "ebpf",
        ]

        topics = []
        for keyword in tech_keywords[:5]:  # Limit to avoid rate limit
            params = {
                "query": keyword,
                "tags": "story",
                "numericFilters": f"created_at_i>{since},points>50",
            }

            response = requests.get(self.hn_algolia_url, params=params)
            hits = response.json().get("hits", [])

            for hit in hits[:10]:  # Top 10 per keyword
                topics.append({
                    "title": hit["title"],
                    "url": hit["url"],
                    "points": hit["points"],
                    "comments": hit["num_comments"],
                    "author": hit["author"],
                })

        # Dedupe e sort por engajamento
        seen = set()
        unique = []
        for topic in topics:
            if topic["title"] not in seen:
                seen.add(topic["title"])
                unique.append(topic)

        return sorted(unique, key=lambda x: x["points"] + x["comments"], reverse=True)

    def extract_tech_from_trends(self, github_trends: List[Dict], hn_trends: List[Dict]) -> List[str]:
        """Extrai nomes de tech/frameworks/languages dos trends."""

        techs = set()

        # De GitHub
        for repo in github_trends:
            if repo["language"]:
                techs.add(repo["language"])
            for topic in repo["topics"]:
                if len(topic) > 2:  # Skip single char tags
                    techs.add(topic)
            # Parse repo name (e.g., "oven-sh/bun" -> "bun")
            name = repo["name"].split("/")[-1]
            if len(name) > 2:
                techs.add(name)

        # De HN (basic extraction from titles)
        tech_indicators = ["rust", "zig", "gleam", "mojo", "bun", "deno", "wasm", "ebpf", "llvm"]
        for trend in hn_trends:
            title_lower = trend["title"].lower()
            for indicator in tech_indicators:
                if indicator in title_lower:
                    techs.add(indicator)

        return sorted(list(techs))

    def generate_early_adopter_queries(self, techs: List[str], github_trends: List[Dict]) -> List[str]:
        """Gera queries para se tornar early expert."""

        queries = []

        for tech in techs[:15]:  # Top 15 emerging techs
            queries.extend([
                # Understanding
                f"{tech}: overview técnico, use cases, e por que está ganhando tração em 2025",
                f"{tech} vs alternativas estabelecidas: trade-offs honestos e quando escolher",

                # Practical
                f"{tech}: getting started guide para production, não tutorial básico",
                f"{tech}: arquitetura interna e decisões de design que importam",

                # Future-looking
                f"{tech}: limitações atuais e roadmap futuro",
                f"Casos de uso de {tech} que vão explodir nos próximos 12 meses",
            ])

        # Deep dives em top 5 GitHub trends
        for repo in github_trends[:5]:
            queries.extend([
                f"{repo['name']}: análise profunda do código fonte e padrões usados",
                f"Como {repo['name']} resolve {repo['description']}: implementação técnica",
                f"Production readiness de {repo['name']}: o que falta e quando adotar",
            ])

        # Meta queries sobre trends
        queries.extend([
            "Tecnologias emergentes 2025: qual tem maior chance de mainstream adoption",
            "Early signals de tech que vai explodir: pattern recognition",
            "Como identificar hype vs real innovation em tech emergente",
            "Framework para avaliar se nova tech vale investimento de tempo",
        ])

        return queries

    def run(self, output_file: str = "queries_trend_prediction.txt"):
        """Pipeline completo."""

        print("🔮 TREND PREDICTOR - Finding future tech...")

        # Fetch data
        print("\n📊 Analyzing GitHub trending...")
        github_trends = self.get_github_emerging(days=30)
        print(f"   Found {len(github_trends)} high-momentum repos")

        print("\n📰 Analyzing Hacker News...")
        hn_trends = self.get_hn_emerging_topics(days=7)
        print(f"   Found {len(hn_trends)} high-engagement discussions")

        # Extract tech
        techs = self.extract_tech_from_trends(github_trends, hn_trends)
        print(f"\n🎯 Identified {len(techs)} emerging technologies:")
        print(f"   {', '.join(techs[:10])}...")

        # Generate queries
        print("\n🔥 Generating early adopter queries...")
        queries = self.generate_early_adopter_queries(techs, github_trends)

        # Save
        output = Path(output_file)
        output.write_text("\n".join(queries))

        # Stats
        print(f"\n✅ Generated {len(queries)} queries")
        print(f"💾 Saved to: {output_file}")
        print(f"💰 Estimated cost: ${len(queries) * 0.004:.2f} USD (~R$ {len(queries) * 0.004 * 5.5:.2f})")

        # Save metadata
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "github_trends": github_trends[:10],
            "hn_trends": hn_trends[:10],
            "emerging_techs": techs,
            "query_count": len(queries),
        }

        metadata_file = output.with_suffix(".json")
        metadata_file.write_text(json.dumps(metadata, indent=2))
        print(f"📊 Metadata: {metadata_file}")

        # Sample
        print(f"\n🎯 Sample queries:")
        for i, q in enumerate(queries[:5], 1):
            print(f"   {i}. {q}")

        return queries


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Predict emerging tech trends and generate queries")
    parser.add_argument("--output", default="queries_trend_prediction.txt", help="Output file")
    parser.add_argument("--execute", action="store_true", help="Auto-execute batch burn after generation")

    args = parser.parse_args()

    predictor = TrendPredictor()
    queries = predictor.run(args.output)

    if args.execute:
        print("\n🚀 Auto-executing batch burn...")
        subprocess.run([
            "python", "scripts/batch_burn.py",
            "--file", args.output,
            "--workers", "10",
        ])
