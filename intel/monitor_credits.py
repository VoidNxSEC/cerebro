#!/usr/bin/env python3
"""
Real-time credit consumption monitor usando BigQuery.
"""

import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from google.cloud import bigquery
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

console = Console()


@dataclass
class CreditStatus:
    total_queries: int
    gross_cost: float
    credits_applied: float
    net_cost: float
    last_updated: datetime


class CreditMonitor:
    def __init__(self, project_id: str, dataset: str = None, table: str = None):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id

        # Auto-detect billing table
        if not dataset or not table:
            dataset, table = self._detect_billing_table()

        self.dataset = dataset
        self.table = table

        # Credit IDs
        self.GENAI_CREDIT_ID = "01fcba1620b82830ec89167e55e859767b7a8525813b0b87545996daede01b04"
        self.DIALOGFLOW_CREDIT_ID = "0195bdacde99b9b9ca3d87c9bf6cfec6ab3d34af5d42edbc30e5e3c856e6b2bd"

    def _detect_billing_table(self):
        """Auto-detecta tabela de billing export."""
        query = f"""
        SELECT table_schema, table_name
        FROM `{self.project_id}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name LIKE 'gcp_billing_export_v1_%'
        LIMIT 1
        """

        try:
            results = self.client.query(query).result()
            for row in results:
                return row.table_schema, row.table_name
        except Exception as e:
            console.print(f"⚠️  Could not auto-detect billing table: {e}", style="yellow")

        return "billing_export", "gcp_billing_export_v1_*"

    def get_credit_status(self, days: int = 30) -> dict[str, CreditStatus]:
        """Busca status dos créditos."""
        query = f"""
        WITH credit_data AS (
            SELECT
                credits.id as credit_id,
                credits.name as credit_name,
                service.description as service,
                COUNT(*) as total_queries,
                SUM(cost) as gross_cost,
                SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c WHERE c.id IN ('{self.GENAI_CREDIT_ID}', '{self.DIALOGFLOW_CREDIT_ID}')), 0)) as credits_applied,
                SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) as net_cost
            FROM `{self.project_id}.{self.dataset}.{self.table}`
            WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                AND service.description IN ('Discovery Engine API', 'Dialogflow API')
            GROUP BY credit_id, credit_name, service
        )
        SELECT * FROM credit_data
        WHERE credit_id IN ('{self.GENAI_CREDIT_ID}', '{self.DIALOGFLOW_CREDIT_ID}')
        """

        results = {}

        try:
            for row in self.client.query(query).result():
                key = "genai" if row.credit_id == self.GENAI_CREDIT_ID else "dialogflow"
                results[key] = CreditStatus(
                    total_queries=row.total_queries,
                    gross_cost=abs(row.gross_cost),
                    credits_applied=abs(row.credits_applied),
                    net_cost=abs(row.net_cost),
                    last_updated=datetime.now(),
                )
        except Exception as e:
            console.print(f"⚠️  Error querying billing: {e}", style="yellow")

        return results

    def generate_table(self, status: dict[str, CreditStatus]) -> Table:
        """Gera tabela de status."""
        table = Table(title=f"💰 GCP Credit Consumption - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        table.add_column("Credit", style="cyan", width=20)
        table.add_column("Queries", justify="right", style="green")
        table.add_column("Gross Cost", justify="right", style="yellow")
        table.add_column("Credits Applied", justify="right", style="blue")
        table.add_column("Net Cost", justify="right", style="red")
        table.add_column("Remaining (BRL)", justify="right", style="magenta")

        # GenAI
        if "genai" in status:
            s = status["genai"]
            remaining = 6432.54 - (s.credits_applied * 5.5)
            table.add_row(
                "GenAI App Builder",
                f"{s.total_queries:,}",
                f"${s.gross_cost:.2f}",
                f"${s.credits_applied:.2f}",
                f"${s.net_cost:.2f}",
                f"R$ {remaining:.2f}",
            )
        else:
            table.add_row("GenAI App Builder", "0", "$0.00", "$0.00", "$0.00", "R$ 6,432.54")

        # Dialogflow
        if "dialogflow" in status:
            s = status["dialogflow"]
            remaining = 3646.57 - (s.credits_applied * 5.5)
            table.add_row(
                "Dialogflow CX",
                f"{s.total_queries:,}",
                f"${s.gross_cost:.2f}",
                f"${s.credits_applied:.2f}",
                f"${s.net_cost:.2f}",
                f"R$ {remaining:.2f}",
            )
        else:
            table.add_row("Dialogflow CX", "0", "$0.00", "$0.00", "$0.00", "R$ 3,646.57")

        # Total
        total_queries = sum(s.total_queries for s in status.values())
        total_gross = sum(s.gross_cost for s in status.values())
        total_credits = sum(s.credits_applied for s in status.values())
        total_net = sum(s.net_cost for s in status.values())
        total_remaining = 10079.11 - (total_credits * 5.5)

        table.add_row(
            "TOTAL",
            f"{total_queries:,}",
            f"${total_gross:.2f}",
            f"${total_credits:.2f}",
            f"${total_net:.2f}",
            f"R$ {total_remaining:.2f}",
            style="bold",
        )

        return table

    def monitor(self, interval: int = 60, days: int = 30):
        """Monitor em tempo real."""
        console.print(f"🔍 Monitoring credits every {interval}s (Ctrl+C to stop)\n")

        try:
            while True:
                status = self.get_credit_status(days=days)
                table = self.generate_table(status)
                console.clear()
                console.print(table)

                # Stats
                total_credits = sum(s.credits_applied for s in status.values())
                total_remaining = 10079.11 - (total_credits * 5.5)
                percent_used = ((10079.11 - total_remaining) / 10079.11) * 100

                console.print(f"\n📊 Overall Progress: {percent_used:.1f}% used")
                console.print(f"⏰ Next update in {interval}s...")

                time.sleep(interval)

        except KeyboardInterrupt:
            console.print("\n\n👋 Monitoring stopped.", style="yellow")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Monitor GCP credit consumption")
    parser.add_argument("--project", type=str, default=os.getenv("GOOGLE_CLOUD_PROJECT"), help="GCP Project ID")
    parser.add_argument("--dataset", type=str, help="BigQuery dataset (auto-detected if not provided)")
    parser.add_argument("--table", type=str, help="BigQuery table (auto-detected if not provided)")
    parser.add_argument("--interval", type=int, default=60, help="Update interval in seconds")
    parser.add_argument("--days", type=int, default=30, help="Days to look back")
    parser.add_argument("--once", action="store_true", help="Run once and exit")

    args = parser.parse_args()

    if not args.project:
        console.print("❌ Error: --project or GOOGLE_CLOUD_PROJECT env var required", style="red")
        return 1

    monitor = CreditMonitor(
        project_id=args.project,
        dataset=args.dataset,
        table=args.table,
    )

    if args.once:
        status = monitor.get_credit_status(days=args.days)
        table = monitor.generate_table(status)
        console.print(table)
    else:
        monitor.monitor(interval=args.interval, days=args.days)

    return 0


if __name__ == "__main__":
    exit(main())
