#!/usr/bin/env bash
set -e

echo "🏗️  Building Phantom SOC Core..."

# Build Rust Control Plane
echo "🦀 Building Control Plane (Rust)..."
nix build .#control-plane --option restrict-eval false
echo "✅ Control Plane Built."

# Setup Python Data Plane
echo "🐍 Setting up Data Plane (Python)..."
cd data-plane
# Check if poetry is available and install deps
if command -v poetry >/dev/null 2>&1; then
    poetry install --no-root
    echo "✅ Data Plane Dependencies Installed."
else
    echo "⚠️  Poetry not found. Skipping dependency installation."
fi
cd ..

echo "✨ Core Systems Ready."
