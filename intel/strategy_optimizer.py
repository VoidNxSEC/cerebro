#!/usr/bin/env python3
"""
STRATEGY OPTIMIZER - Meta-script que analisa todos os outros e sugere MELHOR estratégia

ROI: Maximizar R$ 10k → $200k/year value através de execution inteligente
"""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import subprocess

class StrategyOptimizer:
    """Meta-optimizer para maximum ROI da operação toda."""

    SCRIPTS = {
        "trend_predictor": {
            "file": "scripts/trend_predictor.py",
            "roi_multiple": 50,  # Early mover advantage
            "time_to_value": "6-12 months",
            "queries_generated": 150,
            "cost_brl": 3.3,
            "value_proposition": "Early expertise antes de mainstream",
        },
        "salary_intel": {
            "file": "scripts/salary_intel.py",
            "roi_multiple": 2000,  # 1 negotiation = R$ 50k+
            "time_to_value": "Immediate",
            "queries_generated": 80,
            "cost_brl": 1.76,
            "value_proposition": "1 salary bump = R$ 50k-200k/ano",
        },
        "content_gold_miner": {
            "file": "scripts/content_gold_miner.py",
            "roi_multiple": 100,  # Visibility → offers
            "time_to_value": "1-3 months",
            "queries_generated": 0,  # Analyzes existing
            "cost_brl": 0,
            "value_proposition": "Visibilidade → inbound offers",
        },
        "personal_moat_builder": {
            "file": "scripts/personal_moat_builder.py",
            "roi_multiple": 200,  # Niche expertise premium
            "time_to_value": "12-24 months",
            "queries_generated": 100,
            "cost_brl": 2.2,
            "value_proposition": "Expertise única = R$ 200k-500k premium",
        },
        "generate_queries": {
            "file": "scripts/generate_queries.py",
            "roi_multiple": 10,  # Generic queries
            "time_to_value": "1-6 months",
            "queries_generated": 10000,
            "cost_brl": 220,
            "value_proposition": "Volume de conhecimento geral",
        },
    }

    STRATEGIES = {
        "immediate_value": {
            "name": "Immediate Value (30 dias)",
            "goal": "Quick wins, fastest ROI",
            "scripts": ["salary_intel", "content_gold_miner"],
            "total_cost": 1.76,
            "expected_roi": "R$ 50k-200k (1 negotiation OR 5 offers)",
            "execution": "salary_intel → burn → apply to jobs → content_gold_miner → post",
        },
        "long_term_moat": {
            "name": "Long-term Moat (12-24 meses)",
            "goal": "Build unique expertise, maximum differentiation",
            "scripts": ["personal_moat_builder", "trend_predictor"],
            "total_cost": 5.5,
            "expected_roi": "R$ 200k-500k salary premium",
            "execution": "moat_builder → identify niches → trend_predictor → early mover",
        },
        "balanced": {
            "name": "Balanced (6 meses)",
            "goal": "Mix of quick wins + long-term value",
            "scripts": ["salary_intel", "personal_moat_builder", "trend_predictor", "content_gold_miner"],
            "total_cost": 7.26,
            "expected_roi": "R$ 100k-300k combined",
            "execution": "All scripts in sequence, compounding effects",
        },
        "spray_and_pray": {
            "name": "Spray and Pray (Volume)",
            "goal": "Maximum queries, broad knowledge",
            "scripts": ["generate_queries"],
            "total_cost": 220,
            "expected_roi": "R$ 50k-100k general knowledge",
            "execution": "Generate 10k queries → burn all → hope for insights",
        },
    }

    def analyze_current_situation(self) -> Dict:
        """Analisa situação atual para recomendar estratégia."""

        # Check existing batch results
        results_exist = len(list(Path(".").glob("batch_results_*.json"))) > 0

        # Estimate queries already processed
        total_queries = 0
        if results_exist:
            for file in Path(".").glob("batch_results_*.json"):
                try:
                    data = json.loads(file.read_text())
                    total_queries += len(data.get("results", []))
                except:
                    pass

        # Check content already generated
        content_exists = Path("content_output").exists()

        return {
            "results_exist": results_exist,
            "queries_processed": total_queries,
            "content_generated": content_exists,
            "credits_used_estimate": total_queries * 0.022,  # BRL
            "credits_remaining": 10000 - (total_queries * 0.022),
        }

    def recommend_strategy(self, situation: Dict, goal: str = None) -> Dict:
        """Recomenda melhor estratégia baseado em situação e objetivo."""

        recommendations = []

        # If no queries yet → Start with high ROI immediate
        if situation["queries_processed"] < 100:
            recommendations.append({
                "strategy": "immediate_value",
                "reasoning": "Sem queries ainda. Começar com ROI rápido (salary_intel).",
                "priority": 10,
            })

        # If some queries → Mine for content
        if situation["queries_processed"] > 100 and not situation["content_generated"]:
            recommendations.append({
                "strategy": "content_phase",
                "reasoning": "Você tem queries processadas. Minerar para content AGORA.",
                "priority": 9,
                "action": "Run content_gold_miner.py",
            })

        # If lots of credits left → Build moat
        if situation["credits_remaining"] > 5000:
            recommendations.append({
                "strategy": "long_term_moat",
                "reasoning": "Muitos créditos restantes. Investir em moat building.",
                "priority": 7,
            })

        # If low credits → Focused high ROI only
        if situation["credits_remaining"] < 1000:
            recommendations.append({
                "strategy": "focused_finish",
                "reasoning": "Poucos créditos. Focar só em salary_intel e trend_predictor.",
                "priority": 8,
            })

        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"], reverse=True)

        return recommendations[0] if recommendations else {
            "strategy": "balanced",
            "reasoning": "Situação neutra. Balanced approach é safest.",
            "priority": 5,
        }

    def generate_execution_plan(self, strategy_name: str) -> List[Dict]:
        """Gera plano de execução step-by-step."""

        strategy = self.STRATEGIES.get(strategy_name)
        if not strategy:
            strategy = self.STRATEGIES["balanced"]

        plan = []

        for i, script_name in enumerate(strategy["scripts"], 1):
            script_info = self.SCRIPTS[script_name]

            step = {
                "step": i,
                "script": script_name,
                "file": script_info["file"],
                "action": f"Run {script_name}",
                "queries_generated": script_info["queries_generated"],
                "cost_brl": script_info["cost_brl"],
                "expected_value": script_info["value_proposition"],
                "command": self._generate_command(script_name),
            }

            plan.append(step)

        return plan

    def _generate_command(self, script_name: str) -> str:
        """Generate CLI command for script."""

        commands = {
            "trend_predictor": "python scripts/trend_predictor.py --execute",
            "salary_intel": "python scripts/salary_intel.py --current 150000 --target 300000 --execute",
            "content_gold_miner": "python scripts/content_gold_miner.py",
            "personal_moat_builder": "python scripts/personal_moat_builder.py --execute",
            "generate_queries": "python scripts/generate_queries.py --count 10000 && ./speedrun.sh burn queries.txt 20",
        }

        return commands.get(script_name, f"python scripts/{script_name}.py")

    def export_master_plan(self, recommendation: Dict, execution_plan: List[Dict], situation: Dict) -> str:
        """Export master execution plan."""

        plan = []
        plan.append("# 🎯 MASTER EXECUTION PLAN - Strategy Optimizer\n")
        plan.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        plan.append("## 📊 Current Situation\n")
        plan.append(f"- Queries processed: {situation['queries_processed']:,}\n")
        plan.append(f"- Credits used: R$ {situation['credits_used_estimate']:.2f}\n")
        plan.append(f"- Credits remaining: R$ {situation['credits_remaining']:.2f}\n")
        plan.append(f"- Content generated: {'Yes' if situation['content_generated'] else 'No'}\n\n")

        plan.append("## 🎯 Recommended Strategy\n")
        plan.append(f"**Strategy:** {recommendation['strategy']}\n")
        plan.append(f"**Reasoning:** {recommendation['reasoning']}\n")
        plan.append(f"**Priority:** {recommendation['priority']}/10\n\n")

        strategy_info = self.STRATEGIES.get(recommendation['strategy'], self.STRATEGIES['balanced'])
        plan.append(f"**Goal:** {strategy_info['goal']}\n")
        plan.append(f"**Total Cost:** R$ {strategy_info['total_cost']:.2f}\n")
        plan.append(f"**Expected ROI:** {strategy_info['expected_roi']}\n\n")

        plan.append("## 📋 Execution Plan\n\n")
        for step in execution_plan:
            plan.append(f"### Step {step['step']}: {step['action']}\n")
            plan.append(f"**File:** `{step['file']}`\n")
            plan.append(f"**Queries:** {step['queries_generated']:,}\n")
            plan.append(f"**Cost:** R$ {step['cost_brl']:.2f}\n")
            plan.append(f"**Value:** {step['expected_value']}\n")
            plan.append(f"\n**Command:**\n```bash\n{step['command']}\n```\n\n")

        total_cost = sum(step['cost_brl'] for step in execution_plan)
        total_queries = sum(step['queries_generated'] for step in execution_plan)

        plan.append("## 💰 ROI Summary\n")
        plan.append(f"- Total queries: {total_queries:,}\n")
        plan.append(f"- Total cost: R$ {total_cost:.2f}\n")
        plan.append(f"- Expected ROI: {strategy_info['expected_roi']}\n")
        plan.append(f"- ROI Multiple: {self._calculate_roi_multiple(strategy_info['expected_roi'], total_cost)}\n\n")

        plan.append("## ⚡ Quick Start\n")
        plan.append("```bash\n")
        for step in execution_plan:
            plan.append(f"# Step {step['step']}: {step['action']}\n")
            plan.append(f"{step['command']}\n\n")
        plan.append("```\n")

        return "".join(plan)

    def _calculate_roi_multiple(self, roi_string: str, cost: float) -> str:
        """Extract ROI multiple from string."""

        # Parse "R$ 50k-200k" → average 125k
        import re
        numbers = re.findall(r'(\d+)k', roi_string)
        if numbers:
            avg = sum(int(n) for n in numbers) / len(numbers) * 1000
            multiple = avg / cost if cost > 0 else 0
            return f"{multiple:.0f}x"
        return "N/A"

    def run(self, output_file: str = "MASTER_EXECUTION_PLAN.md", goal: str = None):
        """Generate complete optimization strategy."""

        print("🎯 STRATEGY OPTIMIZER - Analyzing best execution path...\n")

        # Analyze
        print("📊 Analyzing current situation...")
        situation = self.analyze_current_situation()
        print(f"   Queries processed: {situation['queries_processed']:,}")
        print(f"   Credits remaining: R$ {situation['credits_remaining']:.2f}\n")

        # Recommend
        print("🤖 Generating recommendation...")
        recommendation = self.recommend_strategy(situation, goal)
        print(f"   Strategy: {recommendation['strategy']}")
        print(f"   Reasoning: {recommendation['reasoning']}\n")

        # Plan
        print("📋 Creating execution plan...")
        execution_plan = self.generate_execution_plan(recommendation['strategy'])
        print(f"   Steps: {len(execution_plan)}\n")

        # Export
        master_plan = self.export_master_plan(recommendation, execution_plan, situation)
        output = Path(output_file)
        output.write_text(master_plan)

        print(f"✅ Master plan generated!")
        print(f"📄 File: {output_file}\n")

        # Summary
        total_cost = sum(step['cost_brl'] for step in execution_plan)
        print(f"💰 Total Investment: R$ {total_cost:.2f}")
        print(f"🎯 Expected ROI: {self.STRATEGIES[recommendation['strategy']]['expected_roi']}")

        print(f"\n🚀 Next action: Open {output_file} and execute Step 1")

        return execution_plan


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Optimize credit burning strategy for maximum ROI")
    parser.add_argument("--output", default="MASTER_EXECUTION_PLAN.md", help="Output file")
    parser.add_argument("--goal", choices=["immediate", "moat", "balanced"], help="Strategic goal")

    args = parser.parse_args()

    optimizer = StrategyOptimizer()
    optimizer.run(args.output, args.goal)
