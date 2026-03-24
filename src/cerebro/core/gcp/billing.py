#!/usr/bin/env python3
"""
BigQuery Billing Auditor

Consolidated from audit_credits_bigquery.py
Validates credit consumption via BigQuery export
"""
import os
import sys
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from google.cloud import bigquery
from google.auth import default


@dataclass
class BillingTransaction:
    """Single billing transaction"""
    timestamp: datetime
    service_name: str
    sku_name: str
    sku_id: str
    credit_name: str
    credit_type: str
    gross_cost: float
    credit_amount: float
    net_cost: float
    usage_amount: Optional[float]
    usage_unit: Optional[str]


@dataclass
class CreditStatus:
    """Credit consumption summary"""
    total_transactions: int
    total_gross_cost: float
    total_credits_applied: float
    total_net_cost: float
    transactions: List[BillingTransaction]


class BillingAuditor:
    """
    BigQuery-based billing auditor

    Resolves the latency problem of the standard billing panel
    by querying the BigQuery export directly.
    """

    # Credit IDs from user's credits
    GENAI_APP_BUILDER_CREDIT_ID = "01fcba1620b82830ec89167e55e859767b7a8525813b0b87545996daede01b04"
    DIALOGFLOW_CX_CREDIT_ID = "0195bdacde99b9b9ca3d87c9bf6cfec6ab3d34af5d42edbc30e5e3c856e6b2bd"

    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: str = "billing_export",
        table_name: Optional[str] = None
    ):
        """
        Initialize BillingAuditor

        Args:
            project_id: GCP project ID (auto-detected if None)
            dataset_id: BigQuery dataset for billing export
            table_name: Billing export table name (auto-detected if None)
        """
        if project_id is None:
            _, project_id = default()

        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_name = table_name or os.getenv("BILLING_EXPORT_TABLE")

        self.client = bigquery.Client()

        if not self.table_name:
            # Try to detect table name
            self._detect_billing_table()

    def _detect_billing_table(self) -> None:
        """Auto-detect billing export table"""
        try:
            dataset = self.client.get_dataset(self.dataset_id)
            tables = list(self.client.list_tables(dataset))

            for table in tables:
                if table.table_id.startswith("gcp_billing_export"):
                    self.table_name = table.table_id
                    break
        except Exception:
            pass

    def get_table_reference(self) -> str:
        """Get full table reference"""
        if not self.table_name:
            raise ValueError(
                "BILLING_EXPORT_TABLE not configured. "
                "Set via environment variable or constructor parameter."
            )

        return f"{self.project_id}.{self.dataset_id}.{self.table_name}"

    def check_billing_export_setup(self) -> bool:
        """
        Validate billing export is configured

        Returns:
            True if setup is valid, False otherwise
        """
        try:
            dataset = self.client.get_dataset(self.dataset_id)
            tables = list(self.client.list_tables(dataset))

            if not tables:
                return False

            return any(
                table.table_id.startswith("gcp_billing_export")
                for table in tables
            )
        except Exception:
            return False

    def audit_credit_consumption(
        self,
        days_back: int = 7,
        limit: int = 500
    ) -> Optional[CreditStatus]:
        """
        Audit credit consumption from BigQuery

        Args:
            days_back: Number of days to look back
            limit: Maximum number of transactions to return

        Returns:
            CreditStatus with audit results, or None if query fails
        """
        table_ref = self.get_table_reference()

        query = f"""
        SELECT
          invoice.month,

          -- Service details
          service.description AS service_name,
          sku.description AS sku_name,
          sku.id AS sku_id,

          -- Credit details
          credits.name AS credit_name,
          credits.type AS credit_type,
          credits.amount AS credit_amount,

          -- Financial analysis (CRITICAL!)
          cost AS gross_cost,
          (cost + IFNULL(credits.amount, 0)) AS net_cost_to_wallet,

          -- Usage
          usage.amount AS usage_amount,
          usage.unit AS usage_unit,

          usage_start_time,
          usage_end_time

        FROM
          `{table_ref}`,
          UNNEST(credits) AS credits
        WHERE
          -- Filter by specific credits
          (
            credits.name LIKE '%GenAI App Builder%' OR
            credits.name LIKE '%Dialogflow CX Trial%' OR
            credits.id LIKE '%{self.GENAI_APP_BUILDER_CREDIT_ID}%' OR
            credits.id LIKE '%{self.DIALOGFLOW_CX_CREDIT_ID}%'
          )

          -- Time period
          AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)

        ORDER BY
          usage_start_time DESC
        LIMIT {limit}
        """

        try:
            query_job = self.client.query(query)
            results = query_job.result()

            transactions = []
            total_gross = 0.0
            total_credits = 0.0
            total_net = 0.0

            for row in results:
                gross = float(row.gross_cost) if row.gross_cost else 0.0
                credit = float(row.credit_amount) if row.credit_amount else 0.0
                net = float(row.net_cost_to_wallet) if row.net_cost_to_wallet else 0.0

                total_gross += gross
                total_credits += credit
                total_net += net

                transactions.append(BillingTransaction(
                    timestamp=row.usage_start_time,
                    service_name=row.service_name,
                    sku_name=row.sku_name,
                    sku_id=row.sku_id,
                    credit_name=row.credit_name,
                    credit_type=row.credit_type,
                    gross_cost=gross,
                    credit_amount=credit,
                    net_cost=net,
                    usage_amount=float(row.usage_amount) if row.usage_amount else None,
                    usage_unit=row.usage_unit
                ))

            return CreditStatus(
                total_transactions=len(transactions),
                total_gross_cost=total_gross,
                total_credits_applied=total_credits,
                total_net_cost=total_net,
                transactions=transactions
            )

        except Exception as e:
            raise RuntimeError(f"BigQuery audit failed: {e}")

    def validate_credits(self, days_back: int = 7) -> bool:
        """
        Validate that credits are being applied correctly

        Args:
            days_back: Number of days to audit

        Returns:
            True if net cost is ~0 (credits fully applied), False otherwise
        """
        status = self.audit_credit_consumption(days_back=days_back)

        if not status:
            return False

        if status.total_transactions == 0:
            return False  # No transactions found

        # Credits are valid if net cost is near zero
        return abs(status.total_net_cost) < 0.01


def main():
    """CLI entry point for billing audit"""
    print("="*60)
    print("💳 PHANTOM - BigQuery Billing Audit")
    print("="*60)
    print("\nBased on Technical Report - Section 5.2")
    print("Resolves: Panel latency + Definitive validation")

    try:
        auditor = BillingAuditor()

        # Step 1: Check setup
        print("\n🔍 Checking Billing Export configuration...")

        if not auditor.check_billing_export_setup():
            print(f"❌ Dataset '{auditor.dataset_id}' not found or empty")
            print("\n🔧 CONFIGURE BILLING EXPORT:")
            print("1. https://console.cloud.google.com/billing/export")
            print("2. 'Export detailed usage cost to BigQuery'")
            print(f"3. Create dataset: {auditor.dataset_id}")
            sys.exit(1)

        print(f"✅ Dataset '{auditor.dataset_id}' found")

        if auditor.table_name:
            print(f"✅ Using table: {auditor.table_name}")
        else:
            print("⚠️  No billing export table found")
            print("\n💡 Set BILLING_EXPORT_TABLE environment variable:")
            print("   export BILLING_EXPORT_TABLE='gcp_billing_export_v1_...'")
            sys.exit(1)

        print("\n" + "="*60)

        # Step 2: Execute audit
        days = int(os.getenv("AUDIT_DAYS", "7"))

        print(f"\n📊 Table: {auditor.get_table_reference()}")
        print(f"📅 Period: Last {days} days")
        print("\n⏳ Executing BigQuery query...")

        status = auditor.audit_credit_consumption(days_back=days)

        if not status:
            print("\n⚠️  Audit returned no data")
            sys.exit(1)

        # Display results
        print("\n" + "="*60)
        print("📋 AUDIT RESULTS")
        print("="*60)

        # Detailed view (first 10)
        for i, txn in enumerate(status.transactions[:10], 1):
            print(f"\n🔹 {txn.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Service: {txn.service_name}")
            print(f"   SKU: {txn.sku_name}")
            print(f"   Credit: {txn.credit_name}")
            print(f"   💰 Gross Cost: ${txn.gross_cost:.6f}")
            print(f"   💳 Credit Applied: ${txn.credit_amount:.6f}")
            print(f"   💵 Net Cost (your wallet): ${txn.net_cost:.6f}")
            if txn.usage_amount:
                print(f"   📊 Usage: {txn.usage_amount} {txn.usage_unit}")

        if len(status.transactions) > 10:
            print(f"\n... and {len(status.transactions) - 10} more transactions")

        # Financial summary
        print("\n" + "="*60)
        print("💰 FINANCIAL SUMMARY")
        print("="*60)
        print(f"Total Transactions: {status.total_transactions}")
        print(f"Gross Cost: ${status.total_gross_cost:.4f}")
        print(f"Credits Applied: ${status.total_credits_applied:.4f}")
        print(f"Net Cost (Paid): ${status.total_net_cost:.4f}")

        # CRITICAL VALIDATION
        print("\n" + "="*60)
        print("✅ CREDIT CONSUMPTION VALIDATION")
        print("="*60)

        if status.total_transactions == 0:
            print("⚠️  NO TRANSACTIONS WITH CREDIT FOUND")
            print("\nPossible causes:")
            print("1. Billing latency (wait 24-48h)")
            print("2. You haven't consumed any eligible services yet")
            print("3. Credits are not being applied (configuration issue)")
        elif abs(status.total_net_cost) < 0.01:
            print("🎉 TOTAL SUCCESS!")
            print(f"   • You consumed ${abs(status.total_gross_cost):.4f} of services")
            print(f"   • Credits covered 100% (${abs(status.total_credits_applied):.4f})")
            print("   • You were NOT charged ($0.00 to card)")
        else:
            print("⚠️  WARNING: Partial Charge Detected")
            print(f"   • Gross cost: ${status.total_gross_cost:.4f}")
            print(f"   • Credits: ${status.total_credits_applied:.4f}")
            print(f"   • YOU PAID: ${status.total_net_cost:.4f}")
            print("\n🔧 Action Required:")
            print("   → Review consumed SKUs")
            print("   → Verify services are eligible")

        print("\n✅ Audit complete!")
        print("\n📝 NEXT STEPS:")
        print("1. If net_cost > 0: Review architecture (you're being charged)")
        print("2. If net_cost = 0: Continue consuming safely")
        print("3. Run daily to monitor")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Billing Export configured?")
        print("2. BigQuery permissions (roles/bigquery.user)?")
        print("3. Table name correct?")
        sys.exit(1)


if __name__ == "__main__":
    main()
