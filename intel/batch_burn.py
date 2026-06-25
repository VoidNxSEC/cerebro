#!/usr/bin/env python3
"""
Batch query processor - Consome créditos GCP em paralelo com Discovery Engine.
Otimizado para máxima velocidade e valor.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from google.cloud import discoveryengine_v1beta as discoveryengine
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

console = Console()


@dataclass
class QueryResult:
    question: str
    answer: Optional[str]
    citations: list[str]
    duration: float
    cost: float
    error: Optional[str] = None


class BatchBurner:
    def __init__(
        self,
        project_id: str,
        location: str,
        engine_id: str,
        workers: int = 10,
        rate_limit: Optional[float] = None,
    ):
        self.project_id = project_id
        self.location = location
        self.engine_id = engine_id
        self.workers = workers
        self.rate_limit = rate_limit  # queries per second
        self.client = discoveryengine.SearchServiceClient()

        self.serving_config = (
            f"projects/{project_id}/locations/{location}/"
            f"collections/default_collection/engines/{engine_id}/"
            f"servingConfigs/default_config"
        )

        # Stats
        self.total_queries = 0
        self.successful = 0
        self.failed = 0
        self.total_cost = 0.0
        self.start_time = None

    def query_with_rag(self, question: str) -> QueryResult:
        """Executa query com RAG (summary_spec) para máximo custo."""
        start = time.time()

        try:
            request = discoveryengine.SearchRequest(
                serving_config=self.serving_config,
                query=question,
                page_size=10,  # Máximo de resultados
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                        summary_result_count=10,  # MÁXIMO para queimar mais crédito
                        include_citations=True,
                        language_code="pt-BR",
                        model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                            version="preview"  # Preview models podem custar mais
                        ),
                        model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                            preamble=(
                                "Você é um assistente técnico especializado. "
                                "Forneça respostas detalhadas e práticas em português."
                            )
                        ),
                        ignore_adversarial_query=True,
                        use_semantic_chunks=True,
                    ),
                ),
            )

            response = self.client.search(request)

            # Extrair resposta e citações
            answer = None
            citations = []

            if response.summary:
                answer = response.summary.summary_text

                if hasattr(response.summary, 'summary_with_metadata'):
                    for citation in response.summary.summary_with_metadata.citations:
                        for source in citation.sources:
                            citations.append(source.reference_id)

            duration = time.time() - start

            return QueryResult(
                question=question,
                answer=answer,
                citations=citations,
                duration=duration,
                cost=0.004,  # USD por query com RAG
            )

        except Exception as e:
            duration = time.time() - start
            return QueryResult(
                question=question,
                answer=None,
                citations=[],
                duration=duration,
                cost=0.0,
                error=str(e),
            )

    def process_batch(self, questions: list[str], save_results: bool = True) -> list[QueryResult]:
        """Processa batch de queries em paralelo."""
        self.start_time = time.time()
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:

            task = progress.add_task(
                f"[cyan]Processing {len(questions)} queries...",
                total=len(questions)
            )

            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                # Submit all tasks
                future_to_question = {
                    executor.submit(self.query_with_rag, q): q
                    for q in questions
                }

                # Process as they complete
                for future in as_completed(future_to_question):
                    result = future.result()
                    results.append(result)

                    # Update stats
                    self.total_queries += 1
                    if result.error:
                        self.failed += 1
                    else:
                        self.successful += 1
                        self.total_cost += result.cost

                    progress.update(task, advance=1)

                    # Rate limiting
                    if self.rate_limit:
                        time.sleep(1.0 / self.rate_limit)

                    # Progress update every 50 queries
                    if self.total_queries % 50 == 0:
                        self._print_stats(interim=True)

        # Final stats
        self._print_stats(interim=False)

        # Save results
        if save_results:
            self._save_results(results)

        return results

    def _print_stats(self, interim: bool = False):
        """Imprime estatísticas."""
        elapsed = time.time() - self.start_time
        qps = self.total_queries / elapsed if elapsed > 0 else 0

        table = Table(title="📊 Batch Processing Stats" + (" (Interim)" if interim else ""))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Queries", f"{self.total_queries:,}")
        table.add_row("Successful", f"{self.successful:,}")
        table.add_row("Failed", f"{self.failed:,}")
        table.add_row("Success Rate", f"{(self.successful/self.total_queries*100):.1f}%" if self.total_queries > 0 else "0%")
        table.add_row("", "")
        table.add_row("Elapsed Time", f"{elapsed:.1f}s")
        table.add_row("Queries/sec", f"{qps:.2f}")
        table.add_row("", "")
        table.add_row("Cost (USD)", f"${self.total_cost:.2f}")
        table.add_row("Cost (BRL)", f"R$ {self.total_cost * 5.5:.2f}")

        console.print(table)

    def _save_results(self, results: list[QueryResult]):
        """Salva resultados em JSON."""
        output_file = Path(f"batch_results_{int(time.time())}.json")

        data = {
            "metadata": {
                "total_queries": self.total_queries,
                "successful": self.successful,
                "failed": self.failed,
                "total_cost_usd": self.total_cost,
                "total_cost_brl": self.total_cost * 5.5,
                "workers": self.workers,
                "timestamp": time.time(),
            },
            "results": [
                {
                    "question": r.question,
                    "answer": r.answer,
                    "citations": r.citations,
                    "duration": r.duration,
                    "cost": r.cost,
                    "error": r.error,
                }
                for r in results
            ],
        }

        output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        console.print(f"✅ Results saved to: {output_file}", style="green")


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Batch query processor for GCP credit burning")
    parser.add_argument("--file", type=str, required=True, help="Input file with queries (one per line)")
    parser.add_argument("--project", type=str, default=os.getenv("GOOGLE_CLOUD_PROJECT"), help="GCP Project ID")
    parser.add_argument("--location", type=str, default=os.getenv("GOOGLE_CLOUD_LOCATION", "global"), help="GCP Location")
    parser.add_argument("--engine", type=str, default=os.getenv("ENGINE_ID"), help="Discovery Engine ID")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--rate-limit", type=float, help="Max queries per second")
    parser.add_argument("--limit", type=int, help="Limit number of queries to process")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to JSON")

    args = parser.parse_args()

    # Validate args
    if not args.project:
        console.print("❌ Error: --project or GOOGLE_CLOUD_PROJECT env var required", style="red")
        return 1

    if not args.engine:
        console.print("❌ Error: --engine or ENGINE_ID env var required", style="red")
        return 1

    # Load queries
    queries_file = Path(args.file)
    if not queries_file.exists():
        console.print(f"❌ Error: File not found: {queries_file}", style="red")
        return 1

    queries = [line.strip() for line in queries_file.read_text().splitlines() if line.strip()]

    if args.limit:
        queries = queries[:args.limit]

    console.print(f"📋 Loaded {len(queries)} queries from {queries_file}", style="cyan")

    # Confirm
    estimated_cost_usd = len(queries) * 0.004
    estimated_cost_brl = estimated_cost_usd * 5.5

    console.print(f"\n💰 Estimated cost:", style="yellow")
    console.print(f"   USD: ${estimated_cost_usd:.2f}")
    console.print(f"   BRL: R$ {estimated_cost_brl:.2f}")
    console.print(f"   Workers: {args.workers}")
    console.print(f"   Rate limit: {args.rate_limit or 'None'}")

    if not console.input("\n🚀 Proceed? [y/N]: ").lower().startswith('y'):
        console.print("Cancelled.", style="yellow")
        return 0

    # Process
    burner = BatchBurner(
        project_id=args.project,
        location=args.location,
        engine_id=args.engine,
        workers=args.workers,
        rate_limit=args.rate_limit,
    )

    results = burner.process_batch(queries, save_results=not args.no_save)

    console.print(f"\n✅ Batch processing complete!", style="green")

    return 0


if __name__ == "__main__":
    exit(main())
