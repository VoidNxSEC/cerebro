#!/usr/bin/env python3
"""
Test script to identify which command module causes Typer alias error.

This script attempts to import and instantiate each command Typer app
individually to isolate the problematic module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_module(module_name: str, app_name: str):
    """Test importing and accessing a command module."""
    try:
        print(f"\n{'='*60}")
        print(f"Testing: {module_name}")
        print(f"{'='*60}")

        # Import the module
        module = __import__(f"cerebro.commands.{module_name}", fromlist=[app_name])
        app = getattr(module, app_name)

        # Try to access the app's info (this triggers Typer's internal validation)
        print(f"  ✓ Module imported successfully")
        print(f"  ✓ App object: {app}")
        print(f"  ✓ App name: {app.info.name}")
        print(f"  ✓ Commands: {len(app.registered_commands)}")

        # List commands
        for cmd in app.registered_commands:
            print(f"    - {cmd.name}")

        print(f"  ✓ {module_name} OK\n")
        return True

    except Exception as e:
        print(f"  ✗ ERROR in {module_name}:")
        print(f"    {type(e).__name__}: {e}")
        print(f"  ✗ {module_name} FAILED\n")
        return False

def main():
    print("="*60)
    print("Cerebro CLI Module Diagnostic Test")
    print("="*60)

    # Test each module
    modules = [
        ("gcp", "gcp_app"),
        ("strategy", "strategy_app"),
        ("content", "content_app"),
        ("testing", "testing_app"),
    ]

    results = {}
    for module_name, app_name in modules:
        results[module_name] = test_module(module_name, app_name)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = [m for m, status in results.items() if status]
    failed = [m for m, status in results.items() if not status]

    if passed:
        print(f"\n✓ PASSED ({len(passed)}):")
        for m in passed:
            print(f"  - {m}")

    if failed:
        print(f"\n✗ FAILED ({len(failed)}):")
        for m in failed:
            print(f"  - {m}")
    else:
        print("\n🎉 All modules passed!")

    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())
