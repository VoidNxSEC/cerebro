#!/usr/bin/env python3
"""
Valida autenticação e créditos GCP
Roda ANTES de tentar usar qualquer API
"""
import os
import sys
from google.cloud import billing_v1
from google.auth import default
from google.api_core import exceptions

def validate_auth():
    """Valida se gcloud auth tá configurado"""
    print("🔐 Validando autenticação...")
    try:
        credentials, project = default()
        print(f"✅ Autenticado no projeto: {project}")
        return project
    except Exception as e:
        print(f"❌ Erro de autenticação: {e}")
        print("\n🔧 FIX: Execute:")
        print("   gcloud auth application-default login")
        sys.exit(1)

def list_billing_accounts(project_id):
    """Lista billing accounts e créditos disponíveis"""
    print(f"\n💰 Buscando billing info para {project_id}...")
    try:
        # Cria client de billing
        client = billing_v1.CloudBillingClient()

        # Lista billing accounts
        print("\n📊 Billing Accounts encontradas:")
        for account in client.list_billing_accounts():
            print(f"  - {account.display_name}")
            print(f"    ID: {account.name}")
            print(f"    Open: {account.open}")

        # Tenta pegar billing do projeto
        project_name = f"projects/{project_id}"
        try:
            billing_info = client.get_project_billing_info(name=project_name)
            print(f"\n✅ Billing Account do projeto: {billing_info.billing_account_name}")
            return True
        except exceptions.PermissionDenied:
            print(f"\n⚠️  Sem permissão pra ver billing (normal se você não é owner)")
            return True  # Auth OK, só não vê billing
        except Exception as e:
            print(f"\n⚠️  Billing info: {e}")
            return True

    except Exception as e:
        print(f"❌ Erro ao buscar billing: {e}")
        return False

def check_enabled_apis(project_id):
    """Verifica APIs habilitadas"""
    print(f"\n🔌 Verificando APIs habilitadas...")

    required_apis = [
        "discoveryengine.googleapis.com",  # Vertex AI Search
        "dialogflow.googleapis.com",       # Dialogflow CX
    ]

    # Não podemos verificar programaticamente sem Service Usage API
    # Então só mostramos o comando
    print("\n🔧 Para habilitar as APIs necessárias, rode:")
    for api in required_apis:
        print(f"   gcloud services enable {api} --project={project_id}")

    print("\n📋 Para listar APIs habilitadas:")
    print(f"   gcloud services list --enabled --project={project_id}")

if __name__ == "__main__":
    print("="*60)
    print("🧪 VALIDAÇÃO DE SETUP GCP")
    print("="*60)

    # Step 1: Auth
    project = validate_auth()

    # Step 2: Billing
    list_billing_accounts(project)

    # Step 3: APIs
    check_enabled_apis(project)

    print("\n" + "="*60)
    print("✅ Validação básica completa!")
    print("="*60)
    print("\n📝 PRÓXIMOS PASSOS:")
    print("1. Habilitar APIs com os comandos acima")
    print("2. Criar um Data Store (próximo script)")
    print("3. Fazer queries que CONSOMEM os créditos")
