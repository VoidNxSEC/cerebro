#!/usr/bin/env python3
"""
PERSONAL MOAT BUILDER - Analisa seu perfil e gera queries para skills únicos

Estratégia: Você tem 70% em várias skills. Queries para chegar a 95% nas certas = moat.

ROI: Expertise única = zero competição = premium pricing
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter
from datetime import datetime

class PersonalMoatBuilder:
    """Constrói knowledge moat único baseado em seu perfil atual."""

    def __init__(self):
        # High-value skill combinations (niches inexplorados)
        self.POWER_COMBOS = [
            ("Rust", "Distributed Systems", "Observability"),
            ("NixOS", "Kubernetes", "Security"),
            ("Go", "EBPF", "Networking"),
            ("Python", "ML Ops", "Cost Optimization"),
            ("TypeScript", "WebAssembly", "Performance"),
            ("Zig", "Embedded", "Real-time"),
        ]

        # Emerging but underserved (baixa supply, alta demand futura)
        self.EMERGING_NICHES = [
            "WASM outside browser",
            "Edge computing patterns",
            "eBPF for observability",
            "Nix for reproducible builds",
            "Rust for systems programming",
            "Platform engineering",
            "Developer experience (DevEx)",
            "AI infrastructure (não ML models)",
        ]

    def analyze_github_profile(self, username: str = None) -> Dict:
        """Analisa repos do GitHub para extrair skills atuais."""

        print(f"🔍 Analyzing GitHub profile...")

        # For now, analyze local repos (can extend to API later)
        local_repos = Path.home() / "dev"
        if not local_repos.exists():
            local_repos = Path(".")

        skills = Counter()
        projects = []

        # Scan for language files
        for path in local_repos.rglob("*"):
            if path.is_file():
                ext = path.suffix.lower()
                lang_map = {
                    ".rs": "Rust",
                    ".go": "Go",
                    ".py": "Python",
                    ".ts": "TypeScript",
                    ".nix": "Nix",
                    ".c": "C",
                    ".cpp": "C++",
                    ".zig": "Zig",
                }
                if ext in lang_map:
                    skills[lang_map[ext]] += 1

        # Check for tech stacks in configs
        for config_file in ["Dockerfile", "docker-compose.yml", "flake.nix", "Cargo.toml", "go.mod"]:
            if list(local_repos.rglob(config_file)):
                if config_file == "Dockerfile":
                    skills["Docker"] += 10
                elif config_file == "flake.nix":
                    skills["NixOS"] += 10
                elif config_file == "Cargo.toml":
                    skills["Rust"] += 10

        return {
            "primary_languages": [lang for lang, _ in skills.most_common(5)],
            "tech_stack": dict(skills),
            "project_count": len(list(local_repos.glob("*/"))),
        }

    def identify_skill_gaps(self, current_skills: List[str]) -> Dict[str, List[str]]:
        """Identifica gaps para chegar a moat."""

        gaps = {
            "near_expert": [],  # 70% → 95% (pequeno gap)
            "power_combo": [],  # Combinar 2 skills fortes em 1 nicho
            "emerging": [],     # 0% → 70% em tech emergente
        }

        # Near expert: Se você usa, mas não é expert
        for skill in current_skills:
            gaps["near_expert"].append({
                "skill": skill,
                "current_level": "Intermediate/Advanced",
                "target_level": "Expert/Recognized",
                "gap_size": "Small (6-12 months)",
            })

        # Power combos: Combine skills que você tem
        for combo in self.POWER_COMBOS:
            if any(skill in current_skills for skill in combo):
                gaps["power_combo"].append({
                    "combo": " + ".join(combo),
                    "your_skills": [s for s in combo if s in current_skills],
                    "missing": [s for s in combo if s not in current_skills],
                })

        # Emerging: Tech que vai explodir
        for niche in self.EMERGING_NICHES:
            gaps["emerging"].append({
                "niche": niche,
                "opportunity": "High demand, low supply",
                "timeline": "12-24 months to expertise",
            })

        return gaps

    def generate_moat_queries(self, gaps: Dict) -> List[str]:
        """Gera queries ultra-específicas para construir moat."""

        queries = []

        # Near expert queries (deep dives)
        for item in gaps["near_expert"]:
            skill = item["skill"]
            queries.extend([
                f"{skill}: advanced patterns que separam intermediate de expert",
                f"{skill}: production pitfalls que só aparecem em scale",
                f"{skill}: arquitetura interna e design decisions profundas",
                f"Como se tornar recognized expert em {skill}: estratégias concretas",
                f"{skill}: edge cases e corner cases de produção com solutions",
            ])

        # Power combo queries (niche expertise)
        for combo in gaps["power_combo"]:
            combo_name = combo["combo"]
            queries.extend([
                f"{combo_name}: arquitetura completa para produção",
                f"{combo_name}: casos de uso que justificam essa stack",
                f"{combo_name}: trade-offs vs alternativas mainstream",
                f"Como se posicionar como expert em {combo_name}",
                f"{combo_name}: projects para portfolio que demonstram expertise",
            ])

        # Emerging tech queries (early mover advantage)
        for item in gaps["emerging"]:
            niche = item["niche"]
            queries.extend([
                f"{niche}: estado atual em 2025 e roadmap",
                f"{niche}: primeiros passos para production readiness",
                f"{niche}: onde está sendo usado em produção hoje",
                f"{niche}: skills transferable e learning path",
                f"Por que {niche} vai ser importante nos próximos 2 anos",
            ])

        # Meta queries (strategy)
        queries.extend([
            "Como construir personal moat em tech: framework concreto",
            "Niche expertise vs generalist: quando cada path faz sentido",
            "Como se tornar go-to person para tech específica",
            "Personal branding para technical expertise: o que funciona",
            "From capable to expert: deliberate practice em software",
        ])

        return queries

    def generate_project_ideas(self, gaps: Dict) -> List[Dict]:
        """Gera project ideas para demonstrar expertise."""

        projects = []

        # Projects para each power combo
        for combo in gaps["power_combo"][:3]:
            combo_skills = combo["combo"]
            projects.append({
                "name": f"Production-grade {combo_skills} implementation",
                "goal": "Demonstrate deep expertise in niche",
                "deliverables": [
                    "Open source project with 100+ stars",
                    "Blog series explaining decisions",
                    "Talk at local meetup/conference",
                ],
                "timeline": "3-6 months",
                "roi": "Positioning as expert in niche",
            })

        # Projects para emerging tech
        for item in gaps["emerging"][:2]:
            niche = item["niche"]
            projects.append({
                "name": f"{niche}: early implementation and case study",
                "goal": "Be among first to demonstrate production use",
                "deliverables": [
                    "Working prototype with real use case",
                    "Performance benchmarks vs alternatives",
                    "Lessons learned blog post",
                ],
                "timeline": "2-4 months",
                "roi": "Early mover advantage when tech goes mainstream",
            })

        return projects

    def export_moat_strategy(self, profile: Dict, gaps: Dict, queries: List[str], projects: List[Dict]) -> str:
        """Export complete moat-building strategy."""

        strategy = []
        strategy.append("# PERSONAL MOAT BUILDING STRATEGY\n")
        strategy.append(f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n")

        strategy.append("## Current Profile\n")
        strategy.append(f"**Primary Languages:** {', '.join(profile['primary_languages'])}\n")
        strategy.append(f"**Projects:** {profile['project_count']}\n\n")

        strategy.append("## Strategy: 3-Path Approach\n\n")

        strategy.append("### Path 1: Near Expert → Recognized Expert (6-12 months)\n")
        for item in gaps["near_expert"]:
            strategy.append(f"- **{item['skill']}:** {item['current_level']} → {item['target_level']}\n")
        strategy.append("\n")

        strategy.append("### Path 2: Power Combos (Niche Expertise) (12 months)\n")
        for combo in gaps["power_combo"][:3]:
            strategy.append(f"- **{combo['combo']}**\n")
            strategy.append(f"  - You have: {', '.join(combo['your_skills'])}\n")
            if combo['missing']:
                strategy.append(f"  - Need: {', '.join(combo['missing'])}\n")
        strategy.append("\n")

        strategy.append("### Path 3: Emerging Tech (Early Mover) (12-24 months)\n")
        for item in gaps["emerging"][:3]:
            strategy.append(f"- **{item['niche']}:** {item['opportunity']}\n")
        strategy.append("\n")

        strategy.append("## Recommended Projects\n\n")
        for i, project in enumerate(projects, 1):
            strategy.append(f"### Project {i}: {project['name']}\n")
            strategy.append(f"**Goal:** {project['goal']}\n")
            strategy.append(f"**Timeline:** {project['timeline']}\n")
            strategy.append(f"**ROI:** {project['roi']}\n")
            strategy.append("**Deliverables:**\n")
            for deliverable in project['deliverables']:
                strategy.append(f"- {deliverable}\n")
            strategy.append("\n")

        strategy.append(f"## Query Plan ({len(queries)} queries)\n\n")
        strategy.append("These queries will build the knowledge foundation for your moat.\n\n")

        return "".join(strategy)

    def run(self, output_file: str = "queries_personal_moat.txt", github_username: str = None):
        """Build complete moat strategy."""

        print("🏰 PERSONAL MOAT BUILDER - Constructing your unique expertise...\n")

        # Analyze current profile
        profile = self.analyze_github_profile(github_username)
        print(f"📊 Current Profile:")
        print(f"   Primary skills: {', '.join(profile['primary_languages'])}")
        print(f"   Projects: {profile['project_count']}\n")

        # Identify gaps
        print("🎯 Identifying skill gaps...")
        gaps = self.identify_skill_gaps(profile['primary_languages'])
        print(f"   Near expert opportunities: {len(gaps['near_expert'])}")
        print(f"   Power combos: {len(gaps['power_combo'])}")
        print(f"   Emerging niches: {len(gaps['emerging'])}\n")

        # Generate queries
        print("💡 Generating moat-building queries...")
        queries = self.generate_moat_queries(gaps)
        print(f"   Created {len(queries)} queries\n")

        # Generate project ideas
        print("🚀 Generating project ideas...")
        projects = self.generate_project_ideas(gaps)
        print(f"   Designed {len(projects)} portfolio projects\n")

        # Export
        output = Path(output_file)
        output.write_text("\n".join(queries))

        strategy = self.export_moat_strategy(profile, gaps, queries, projects)
        strategy_file = output.with_name("moat_building_strategy.md")
        strategy_file.write_text(strategy)

        # Metadata
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "current_skills": profile['primary_languages'],
            "moat_paths": {
                "near_expert": len(gaps['near_expert']),
                "power_combos": len(gaps['power_combo']),
                "emerging_tech": len(gaps['emerging']),
            },
            "query_count": len(queries),
            "project_count": len(projects),
            "estimated_timeline": "12-24 months to established moat",
            "estimated_roi": "Niche expertise = R$ 200k-500k salary premium",
        }

        metadata_file = output.with_suffix(".json")
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # Stats
        print("✅ Moat strategy complete!")
        print(f"\n📄 Files generated:")
        print(f"   Strategy: {strategy_file}")
        print(f"   Queries: {output_file}")
        print(f"   Metadata: {metadata_file}")

        print(f"\n💰 ROI Projection:")
        print(f"   Investment: {len(queries)} queries × R$ 0.02 = R$ {len(queries) * 0.022:.2f}")
        print(f"   Timeline: 12-24 months to established moat")
        print(f"   Return: Niche expertise → R$ 200k-500k salary premium")
        print(f"   Multiple: {200000 / (len(queries) * 0.022):.0f}x")

        return queries


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build your personal knowledge moat")
    parser.add_argument("--output", default="queries_personal_moat.txt", help="Output file")
    parser.add_argument("--github", help="GitHub username (optional)")
    parser.add_argument("--execute", action="store_true", help="Auto-execute batch burn")

    args = parser.parse_args()

    builder = PersonalMoatBuilder()
    queries = builder.run(args.output, args.github)

    if args.execute:
        import subprocess
        print("\n🚀 Auto-executing batch burn...")
        subprocess.run([
            "python", "scripts/batch_burn.py",
            "--file", args.output,
            "--workers", "10",
        ])
