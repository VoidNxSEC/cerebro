#!/usr/bin/env bash
# Quick-start: limpa e reconfigura tudo

set -e

echo "🧹 Limpando ambiente anterior..."
rm -rf .venv
rm -f .venv/.deps_installed

echo "📦 Criando novo venv..."
python3 -m venv .venv

echo "🚀 Ativando venv..."
source .venv/bin/activate

echo "📥 Instalando dependências fresh..."
pip install --upgrade pip
pip install \
  google-cloud-discoveryengine \
  google-auth

echo ""
echo "✅ Setup completo!"
echo ""
echo "🔧 Agora rode:"
echo "   source .venv/bin/activate"
echo "   python validate_credits.py"
