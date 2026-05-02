#!/usr/bin/env python3
"""
GCP Authentication and Validation

Consolidated from validate_credits.py
"""
import sys
from dataclasses import dataclass

from google.api_core import exceptions
from google.auth import default
from google.auth.credentials import Credentials
from google.cloud import billing_v1


@dataclass
class SetupStatus:
    """Status of GCP setup"""
    authenticated: bool
    project_id: str | None
    billing_enabled: bool
    required_apis: list[str]
    errors: list[str]


def get_credentials() -> tuple[Credentials, str]:
    """
    Get Google Cloud credentials and project ID

    Returns:
        Tuple of (credentials, project_id)

    Raises:
        RuntimeError: If authentication fails
    """
    try:
        credentials, project = default()
        return credentials, project
    except Exception as e:
        raise RuntimeError(
            f"Authentication failed: {e}\n"
            "Fix: gcloud auth application-default login"
        )


def get_project_id() -> str:
    """
    Get the current GCP project ID

    Returns:
        str: Project ID
    """
    _, project = get_credentials()
    return project


def validate_setup(verbose: bool = True) -> SetupStatus:
    """
    Validate complete GCP setup

    Args:
        verbose: Print status messages

    Returns:
        SetupStatus with validation results
    """
    status = SetupStatus(
        authenticated=False,
        project_id=None,
        billing_enabled=False,
        required_apis=[
            "discoveryengine.googleapis.com",
            "dialogflow.googleapis.com",
        ],
        errors=[]
    )

    if verbose:
        print("="*60)
        print("🧪 PHANTOM - GCP Setup Validation")
        print("="*60)

    # Step 1: Authentication
    if verbose:
        print("\n🔐 Validating authentication...")

    try:
        credentials, project = get_credentials()
        status.authenticated = True
        status.project_id = project

        if verbose:
            print(f"✅ Authenticated on project: {project}")
    except RuntimeError as e:
        status.errors.append(str(e))
        if verbose:
            print(f"❌ {e}")
        return status

    # Step 2: Billing
    if verbose:
        print(f"\n💰 Checking billing for {project}...")

    try:
        client = billing_v1.CloudBillingClient()

        if verbose:
            print("\n📊 Billing Accounts found:")

        for account in client.list_billing_accounts():
            if verbose:
                print(f"  - {account.display_name}")
                print(f"    ID: {account.name}")
                print(f"    Open: {account.open}")

        project_name = f"projects/{project}"
        try:
            billing_info = client.get_project_billing_info(name=project_name)
            status.billing_enabled = True

            if verbose:
                print(f"\n✅ Billing Account: {billing_info.billing_account_name}")

        except exceptions.PermissionDenied:
            if verbose:
                print("\n⚠️  No permission to view billing (normal if not owner)")
            status.billing_enabled = True  # Assume enabled

        except Exception as e:
            status.errors.append(f"Billing check failed: {e}")
            if verbose:
                print(f"\n⚠️  Billing info: {e}")

    except Exception as e:
        status.errors.append(f"Billing API error: {e}")
        if verbose:
            print(f"❌ Error fetching billing: {e}")

    # Step 3: APIs
    if verbose:
        print("\n🔌 Required APIs:")
        print("\n🔧 To enable required APIs, run:")
        for api in status.required_apis:
            print(f"   gcloud services enable {api} --project={project}")

        print("\n📋 To list enabled APIs:")
        print(f"   gcloud services list --enabled --project={project}")

    # Final status
    if verbose:
        print("\n" + "="*60)
        if status.authenticated and status.billing_enabled:
            print("✅ Validation complete!")
        else:
            print("⚠️  Validation completed with warnings")
        print("="*60)

        if status.errors:
            print("\n❌ Errors:")
            for error in status.errors:
                print(f"  - {error}")

    return status


def main():
    """CLI entry point"""
    status = validate_setup(verbose=True)

    print("\n📝 NEXT STEPS:")
    print("1. Enable APIs with the commands above")
    print("2. Create a Data Store (cerebro gcp datastores create)")
    print("3. Run queries that consume credits")

    sys.exit(0 if status.authenticated else 1)


if __name__ == "__main__":
    main()
