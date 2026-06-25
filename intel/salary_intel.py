#!/usr/bin/env python3
"""
SALARY INTEL - Gera queries de negociação baseado em dados REAIS de mercado

ROI: 1 negociação bem feita = R$ 50k-200k/ano a mais
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class SalaryIntelligence:
    """Gera queries ultra-específicas para negotiation usando market data."""

    # Data real de levels.fyi, Glassdoor, Blind (2025)
    SALARY_DATA = {
        "FAANG": {
            "Google": {
                "L3": {"base": "120-140k", "total": "180-220k"},
                "L4": {"base": "160-190k", "total": "240-300k"},
                "L5": {"base": "190-230k", "total": "320-420k"},
                "L6": {"base": "230-280k", "total": "450-600k"},
            },
            "Meta": {
                "E3": {"base": "120-140k", "total": "180-230k"},
                "E4": {"base": "160-195k", "total": "250-320k"},
                "E5": {"base": "200-240k", "total": "350-480k"},
                "E6": {"base": "250-300k", "total": "500-700k"},
            },
            "Amazon": {
                "SDE1": {"base": "110-130k", "total": "150-190k"},
                "SDE2": {"base": "140-170k", "total": "210-280k"},
                "SDE3": {"base": "170-210k", "total": "300-420k"},
                "Principal": {"base": "220-270k", "total": "450-650k"},
            },
        },
        "Unicorns": {
            "Stripe": {"base": "140-220k", "equity": "High", "total": "250-400k"},
            "Databricks": {"base": "150-230k", "equity": "Very High", "total": "300-500k"},
            "Figma": {"base": "140-210k", "equity": "High", "total": "240-380k"},
        },
        "Remote_Brazil": {
            "Senior": {"usd": "80-120k", "brl": "440-660k/ano"},
            "Staff": {"usd": "120-180k", "brl": "660k-1M/ano"},
            "Principal": {"usd": "180-250k", "brl": "1M-1.4M/ano"},
        },
    }

    NEGOTIATION_TACTICS = [
        "anchoring alto",
        "multiple offers como leverage",
        "timing de counteroffer",
        "equity vs cash trade-off",
        "sign-on bonus negotiation",
        "relocation package",
        "remote work premium",
        "level up durante processo",
    ]

    COMMON_MISTAKES = [
        "aceitar primeira offer",
        "não pesquisar comps",
        "revelar current salary",
        "negociar email vs phone",
        "não ter BATNA",
        "focar só em base vs total comp",
    ]

    def generate_negotiation_queries(self) -> List[str]:
        """Queries específicas para cada stage de negotiation."""

        queries = []

        # Stage 1: Preparation
        queries.extend([
            "Salary negotiation preparation checklist: research, BATNA, e script",
            "Como calcular seu market value real: fatores além de YoE",
            "Equity vs cash compensation: framework de decisão 2025",
            "Total compensation package breakdown: o que pedir além de salary",
            "Remote work salary differential: US vs Europe vs LatAm em 2025",
        ])

        # Stage 2: Company-specific intel
        for company_type, companies in self.SALARY_DATA.items():
            if isinstance(companies, dict) and "base" not in companies:
                for company in list(companies.keys())[:3]:
                    queries.append(
                        f"{company} salary negotiation: levels, bands, e leverage points específicos"
                    )

        # Stage 3: Tactics
        for tactic in self.NEGOTIATION_TACTICS:
            queries.append(
                f"Salary negotiation: como usar {tactic} efetivamente com exemplos reais"
            )

        # Stage 4: Avoiding mistakes
        for mistake in self.COMMON_MISTAKES:
            queries.append(
                f"Por que {mistake} é erro em salary negotiation e como evitar"
            )

        # Stage 5: Specific scenarios
        queries.extend([
            "Counteroffer strategy: quando aceitar vs quando recusar com data points",
            "Multiple offers: como usar para maximizar final offer sem queimar bridges",
            "Equity negotiation em startup: vesting, strike price, e valuation analysis",
            "Sign-on bonus negotiation: amounts típicos e como justificar",
            "Level negotiation: evidências para level up durante hiring process",
            "Remote work premium: quanto pedir a mais se for escritório vs full remote",
        ])

        # Stage 6: Market intelligence
        queries.extend([
            "Tech salary trends 2025: qual skill paga mais premium",
            "Compensation bands por level FAANG: L3-L6 breakdown atualizado",
            "Startup vs BigTech comp: quando cada um faz sentido financeiramente",
            "Brazil tech salaries vs international remote: arbitrage opportunities",
            "Recession impact em tech salaries: como negociar em downturn",
        ])

        # Stage 7: Advanced tactics
        queries.extend([
            "Competing offer framework: template de apresentação para maximize leverage",
            "Email vs phone negotiation: quando usar cada e scripts específicos",
            "Timeline manipulation em negotiation: como criar urgency a seu favor",
            "Hiring manager vs recruiter: quem pode dar o quê em negotiation",
            "Final round negotiation: último push tactics que funcionam",
        ])

        return queries

    def generate_career_growth_queries(self) -> List[str]:
        """Queries para growth que leva a higher comp."""

        queries = [
            # Promotion
            "Staff engineer promotion: evidências concretas e timeline típico",
            "Principal engineer path: technical vs management track compensation",
            "Promo packet engineering: o que incluir para maximizar chances",
            "Promotion timing: quando pedir e como justificar with metrics",

            # Skills que pagam
            "Highest paying tech skills 2025: demand vs supply analysis",
            "ML Engineer vs Data Engineer vs SWE: compensation comparison",
            "Distributed systems expertise: salary premium e como demonstrar",
            "Security engineering: certification ROI e salary impact",

            # Market positioning
            "Niche expertise: como criar positioning que comanda premium",
            "Personal branding impact em salary: quantificação real",
            "Open source contributions: correlation com compensation",
            "Speaking/writing: ROI em career growth e offers",

            # Company/industry transitions
            "Finance tech vs FAANG: total comp comparison e trade-offs",
            "Trading firms (Jane Street, HRT): comp structure e hiring",
            "Crypto/Web3 compensation 2025: risk vs reward honest take",
            "Developer tools startups: equity potential vs BigTech stability",
        ]

        return queries

    def generate_scenarios(self, current_salary: int, target: int) -> List[str]:
        """Queries personalizadas baseado em situação específica."""

        gap = target - current_salary
        percent_increase = (gap / current_salary) * 100

        queries = [
            f"Como justificar aumento de {percent_increase:.0f}% em salary negotiation",
            f"Transition de R$ {current_salary/1000:.0f}k para R$ {target/1000:.0f}k: roadmap realista",
            f"Salary negotiation com gap grande ({percent_increase:.0f}%): strategies que funcionam",
        ]

        # Add scenario-specific queries
        if percent_increase > 50:
            queries.append(
                "Large salary jump (>50%): como justificar sem parecer unrealistic"
            )
        if percent_increase > 100:
            queries.append(
                "Doubling salary: quando é possível e path mais rápido"
            )

        return queries

    def run(self, output_file: str = "queries_salary_intel.txt", current_salary: int = None, target_salary: int = None):
        """Generate complete salary intelligence query set."""

        print("💰 SALARY INTEL - Generating negotiation queries...")

        queries = []

        # Core negotiation
        print("\n📊 Negotiation tactics...")
        queries.extend(self.generate_negotiation_queries())

        # Career growth
        print("📈 Career growth paths...")
        queries.extend(self.generate_career_growth_queries())

        # Personalized scenarios
        if current_salary and target_salary:
            print(f"\n🎯 Personalized scenarios (R$ {current_salary:,} → R$ {target_salary:,})...")
            queries.extend(self.generate_scenarios(current_salary, target_salary))

        # Save
        output = Path(output_file)
        output.write_text("\n".join(queries))

        # Metadata
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "query_count": len(queries),
            "categories": {
                "negotiation": len(self.generate_negotiation_queries()),
                "career_growth": len(self.generate_career_growth_queries()),
                "personalized": len(self.generate_scenarios(current_salary or 0, target_salary or 0)) if current_salary and target_salary else 0,
            },
            "estimated_roi": "R$ 50,000 - 200,000 per successful negotiation",
        }

        metadata_file = output.with_suffix(".json")
        metadata_file.write_text(json.dumps(metadata, indent=2))

        # Stats
        print(f"\n✅ Generated {len(queries)} queries")
        print(f"💾 Saved to: {output_file}")
        print(f"💰 Estimated cost: ${len(queries) * 0.004:.2f} USD (~R$ {len(queries) * 0.004 * 5.5:.2f})")
        print(f"🎯 Estimated ROI: R$ 50k-200k (1 successful negotiation)")
        print(f"📊 ROI Multiple: {50000 / (len(queries) * 0.004 * 5.5):.0f}x")

        # Samples
        print(f"\n🎯 Sample queries:")
        for i, q in enumerate(queries[:5], 1):
            print(f"   {i}. {q}")

        return queries


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate salary negotiation intelligence queries")
    parser.add_argument("--output", default="queries_salary_intel.txt", help="Output file")
    parser.add_argument("--current", type=int, help="Current salary (BRL)")
    parser.add_argument("--target", type=int, help="Target salary (BRL)")
    parser.add_argument("--execute", action="store_true", help="Auto-execute batch burn")

    args = parser.parse_args()

    intel = SalaryIntelligence()
    queries = intel.run(args.output, args.current, args.target)

    if args.execute:
        import subprocess
        print("\n🚀 Auto-executing batch burn...")
        subprocess.run([
            "python", "scripts/batch_burn.py",
            "--file", args.output,
            "--workers", "10",
        ])
