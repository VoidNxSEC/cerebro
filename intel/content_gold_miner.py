#!/usr/bin/env python3
"""
CONTENT GOLD MINER - Analisa batch results e extrai os top 1% insights para viralizar

ROI: 1 post viral = 10k+ views = 50 recruiter msgs = 5 offers
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter
from datetime import datetime

class ContentGoldMiner:
    """Minera batch_results_*.json e extrai gold nuggets para content."""

    def __init__(self):
        self.viral_triggers = [
            "surprising", "counter-intuitive", "nobody talks about",
            "hidden", "secret", "mistake", "wrong", "failed",
            "lessons learned", "wish I knew", "changed my mind",
            "vs", "better than", "faster than", "simpler",
            "production", "real world", "at scale",
        ]

        self.content_formats = {
            "thread": "Twitter/X thread (10-15 tweets)",
            "linkedin_post": "LinkedIn post (1000-1300 chars)",
            "blog_outline": "Blog post outline with sections",
            "newsletter": "Newsletter section (400-600 words)",
            "talk_outline": "Conference talk outline (30min)",
        }

    def load_batch_results(self, results_dir: str = ".") -> List[Dict]:
        """Load all batch_results_*.json files."""

        results = []
        for file in Path(results_dir).glob("batch_results_*.json"):
            try:
                data = json.loads(file.read_text())
                # Add filename for tracking
                for result in data.get("results", []):
                    result["source_file"] = file.name
                results.extend(data.get("results", []))
            except Exception as e:
                print(f"⚠️  Error loading {file}: {e}")

        return results

    def score_insight(self, result: Dict) -> float:
        """Score insight by viral potential (0-100)."""

        score = 0.0
        answer = (result.get("answer") or "").lower()
        question = result.get("question", "").lower()

        # Length score (sweet spot: 200-800 chars)
        length = len(answer)
        if 200 <= length <= 800:
            score += 20
        elif 800 < length <= 1500:
            score += 10

        # Citation count (more sources = more credible)
        citation_count = len(result.get("citations", []))
        score += min(citation_count * 5, 20)  # Max 20 points

        # Viral trigger words
        for trigger in self.viral_triggers:
            if trigger in answer or trigger in question:
                score += 3

        # Specificity (numbers, company names, versions)
        numbers = len(re.findall(r'\d+', answer))
        score += min(numbers * 2, 15)

        # Tech mentions (indicates depth)
        tech_keywords = [
            "rust", "go", "python", "kubernetes", "docker",
            "aws", "gcp", "azure", "postgres", "redis",
            "react", "vue", "nextjs", "typescript",
        ]
        tech_mentions = sum(1 for tech in tech_keywords if tech in answer)
        score += min(tech_mentions * 3, 15)

        # Actionability (has code, commands, steps)
        actionable_markers = ["```", "step 1", "first", "example:", "try this"]
        if any(marker in answer for marker in actionable_markers):
            score += 10

        # Controversy (strong opinions)
        controversial = ["wrong", "mistake", "don't use", "avoid", "overrated"]
        if any(word in answer for word in controversial):
            score += 8

        return min(score, 100)

    def extract_gold(self, results: List[Dict], top_n: int = 20) -> List[Dict]:
        """Extract top N highest-scoring insights."""

        # Score all
        scored = []
        for result in results:
            if result.get("answer"):  # Only if we got an answer
                score = self.score_insight(result)
                scored.append({
                    **result,
                    "viral_score": score,
                })

        # Sort by score
        scored.sort(key=lambda x: x["viral_score"], reverse=True)

        return scored[:top_n]

    def categorize_content(self, gold: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize by content type."""

        categories = {
            "technical_deep_dive": [],
            "comparison": [],
            "lessons_learned": [],
            "how_to": [],
            "contrarian": [],
            "production_war_story": [],
        }

        for item in gold:
            question = item["question"].lower()
            answer = (item.get("answer") or "").lower()

            if "vs" in question or "comparison" in question:
                categories["comparison"].append(item)
            elif any(word in question for word in ["lesson", "learned", "mistake", "wish"]):
                categories["lessons_learned"].append(item)
            elif question.startswith("how") or "tutorial" in question:
                categories["how_to"].append(item)
            elif any(word in answer for word in ["wrong", "don't", "avoid", "overrated"]):
                categories["contrarian"].append(item)
            elif "production" in question or "scale" in question:
                categories["production_war_story"].append(item)
            else:
                categories["technical_deep_dive"].append(item)

        return categories

    def generate_content_ideas(self, gold: List[Dict]) -> List[Dict]:
        """Generate specific content ideas from gold insights."""

        ideas = []

        for item in gold[:15]:  # Top 15
            question = item["question"]
            answer = item.get("answer", "")
            score = item["viral_score"]

            # Extract key points (first 3 sentences or bullet points)
            sentences = re.split(r'[.!?]\s+', answer)
            key_points = sentences[:3]

            ideas.append({
                "title": self._generate_title(question, answer),
                "format": self._suggest_format(question, answer),
                "hook": key_points[0] if key_points else "",
                "key_points": key_points,
                "viral_score": score,
                "original_question": question,
                "cta": self._generate_cta(question),
            })

        return ideas

    def _generate_title(self, question: str, answer: str) -> str:
        """Generate catchy title."""

        # Extract main subject
        if "how" in question.lower():
            return question.replace("how to", "How I").replace("?", "")
        elif "vs" in question.lower():
            return question.replace("?", ": The Honest Comparison")
        elif "why" in question.lower():
            return question.replace("why", "Why").replace("?", " (and what to do instead)")
        else:
            return f"What I learned about {question[:50]}..."

    def _suggest_format(self, question: str, answer: str) -> str:
        """Suggest best content format."""

        length = len(answer)

        if length < 300:
            return "twitter_thread"
        elif length < 800:
            return "linkedin_post"
        elif length < 2000:
            return "blog_post"
        else:
            return "newsletter_section"

    def _generate_cta(self, question: str) -> str:
        """Generate call-to-action."""

        ctas = [
            "What's your experience with this? Share in comments.",
            "Disagree? Let me know why - always learning.",
            "Found this useful? Follow for more technical insights.",
            "Working on something similar? DM me, let's chat.",
        ]

        import random
        return random.choice(ctas)

    def export_content_calendar(self, ideas: List[Dict], days: int = 30) -> str:
        """Export 30-day content calendar."""

        calendar = []
        calendar.append("# 30-DAY CONTENT CALENDAR (Generated from Batch Results)\n")
        calendar.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        calendar.append(f"Total posts: {min(len(ideas), days)}\n")
        calendar.append("\n---\n\n")

        for day, idea in enumerate(ideas[:days], 1):
            calendar.append(f"## Day {day} - {idea['format'].upper()}\n")
            calendar.append(f"**Title:** {idea['title']}\n")
            calendar.append(f"**Hook:** {idea['hook']}\n")
            calendar.append(f"**Viral Score:** {idea['viral_score']:.0f}/100\n")
            calendar.append(f"\n**Key Points:**\n")
            for i, point in enumerate(idea['key_points'][:3], 1):
                calendar.append(f"{i}. {point}\n")
            calendar.append(f"\n**CTA:** {idea['cta']}\n")
            calendar.append(f"\n**Source:** {idea['original_question']}\n")
            calendar.append("\n---\n\n")

        return "".join(calendar)

    def run(self, results_dir: str = ".", top_n: int = 30, output_dir: str = "content_output"):
        """Mine gold and generate content calendar."""

        print("⛏️  CONTENT GOLD MINER - Extracting viral insights...\n")

        # Load all results
        print("📂 Loading batch results...")
        results = self.load_batch_results(results_dir)
        print(f"   Found {len(results)} total query results\n")

        if not results:
            print("❌ No batch results found. Run batch_burn.py first!")
            return

        # Extract gold
        print(f"🏆 Scoring and extracting top {top_n} insights...")
        gold = self.extract_gold(results, top_n)
        print(f"   Average viral score: {sum(g['viral_score'] for g in gold) / len(gold):.1f}/100\n")

        # Categorize
        print("📊 Categorizing content...")
        categories = self.categorize_content(gold)
        for cat, items in categories.items():
            if items:
                print(f"   {cat}: {len(items)} insights")
        print()

        # Generate content ideas
        print("💡 Generating content ideas...")
        ideas = self.generate_content_ideas(gold)
        print(f"   Created {len(ideas)} ready-to-post ideas\n")

        # Export
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Calendar
        calendar = self.export_content_calendar(ideas, days=30)
        calendar_file = output_path / "content_calendar_30days.md"
        calendar_file.write_text(calendar)
        print(f"📅 Content calendar: {calendar_file}")

        # Gold insights JSON
        gold_file = output_path / "gold_insights.json"
        gold_file.write_text(json.dumps(gold, indent=2, ensure_ascii=False))
        print(f"💎 Gold insights: {gold_file}")

        # Stats
        stats = {
            "total_results_analyzed": len(results),
            "gold_insights_extracted": len(gold),
            "content_ideas_generated": len(ideas),
            "categories": {cat: len(items) for cat, items in categories.items()},
            "top_5_insights": [
                {
                    "question": g["question"],
                    "score": g["viral_score"],
                }
                for g in gold[:5]
            ],
            "estimated_reach": f"{len(ideas) * 1000}-{len(ideas) * 5000} views/month",
            "estimated_roi": "5-10 recruiter inbounds/month, 1-2 offers",
        }

        stats_file = output_path / "mining_stats.json"
        stats_file.write_text(json.dumps(stats, indent=2))
        print(f"📊 Stats: {stats_file}\n")

        # Summary
        print("✅ Mining complete!")
        print(f"\n🎯 Top 5 viral insights:")
        for i, g in enumerate(gold[:5], 1):
            print(f"   {i}. [{g['viral_score']:.0f}/100] {g['question'][:80]}...")

        print(f"\n💰 ROI Potential:")
        print(f"   {len(ideas)} posts × 1-5k views = {len(ideas) * 1000:,}-{len(ideas) * 5000:,} total views")
        print(f"   Estimated: 5-10 recruiter inbounds/month")
        print(f"   Potential: 1-2 job offers from visibility")

        return ideas


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mine batch results for viral content")
    parser.add_argument("--results-dir", default=".", help="Directory with batch_results_*.json files")
    parser.add_argument("--top-n", type=int, default=30, help="Number of top insights to extract")
    parser.add_argument("--output-dir", default="content_output", help="Output directory")

    args = parser.parse_args()

    miner = ContentGoldMiner()
    miner.run(args.results_dir, args.top_n, args.output_dir)
