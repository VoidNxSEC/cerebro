#!/usr/bin/env python3
"""
Credit Audit Module

Wrapper around BillingAuditor for credit consumption validation
"""
import sys
from cerebro.core.gcp import BillingAuditor


def audit_credits(days_back: int = 7, verbose: bool = True) -> dict:
    """
    Audit credit consumption via BigQuery

    Args:
        days_back: Number of days to audit
        verbose: Print detailed output

    Returns:
        Dict with audit results
    """
    auditor = BillingAuditor()

    # Check setup
    if not auditor.check_billing_export_setup():
        if verbose:
            print("❌ Billing Export not configured")
            print("\n🔧 SETUP:")
            print("1. https://console.cloud.google.com/billing/export")
            print("2. 'Export detailed usage cost to BigQuery'")
            print(f"3. Create dataset: {auditor.dataset_id}")

        return {"status": "error", "message": "Billing export not configured"}

    # Run audit
    try:
        status = auditor.audit_credit_consumption(days_back=days_back)

        if verbose:
            print(f"\n✅ Audit complete!")
            print(f"Transactions: {status.total_transactions}")
            print(f"Gross cost: ${status.total_gross_cost:.4f}")
            print(f"Credits applied: ${status.total_credits_applied:.4f}")
            print(f"Net cost: ${status.total_net_cost:.4f}")

            if abs(status.total_net_cost) < 0.01:
                print("\n🎉 SUCCESS! Credits fully applied ($0.00 charged)")
            else:
                print(f"\n⚠️  WARNING: ${status.total_net_cost:.4f} charged to card")

        return {
            "status": "success",
            "total_transactions": status.total_transactions,
            "total_gross_cost": status.total_gross_cost,
            "total_credits_applied": status.total_credits_applied,
            "total_net_cost": status.total_net_cost,
            "fully_covered": abs(status.total_net_cost) < 0.01
        }

    except Exception as e:
        if verbose:
            print(f"❌ Audit failed: {e}")

        return {"status": "error", "message": str(e)}


def main():
    """CLI entry point"""
    import os

    days = int(os.getenv("AUDIT_DAYS", "7"))
    result = audit_credits(days_back=days, verbose=True)

    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
