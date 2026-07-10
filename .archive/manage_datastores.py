#!/usr/bin/env python3
"""
Gerencia Data Stores no Vertex AI Search
Um data store é OBRIGATÓRIO para fazer queries
"""
import os
import sys
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.api_core import exceptions
from google.auth import default

def get_project_and_location():
    """Pega configuração do ambiente"""
    _, project = default()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    return project, location

def list_data_stores(client, parent):
    """Lista data stores existentes"""
    print("\n📚 Data Stores existentes:")
    try:
        request = discoveryengine.ListDataStoresRequest(parent=parent)
        response = client.list_data_stores(request=request)

        found = False
        for data_store in response:
            found = True
            print(f"\n  📦 {data_store.display_name}")
            print(f"     ID: {data_store.name.split('/')[-1]}")
            print(f"     Type: {data_store.content_config}")
            print(f"     Industry: {data_store.industry_vertical}")

        if not found:
            print("  (Nenhum data store encontrado)")
        return found
    except exceptions.PermissionDenied as e:
        print(f"  ❌ Sem permissão: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False

def create_sample_data_store(client, parent, data_store_id="test-search-datastore"):
    """Cria um data store de teste"""
    print(f"\n🔨 Criando data store '{data_store_id}'...")

    try:
        # Configuração do data store
        data_store = discoveryengine.DataStore(
            display_name="Test Search DataStore",
            industry_vertical=discoveryengine.IndustryVertical.GENERIC,
            content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
            solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        )

        request = discoveryengine.CreateDataStoreRequest(
            parent=parent,
            data_store=data_store,
            data_store_id=data_store_id,
        )

        # Operação pode demorar
        operation = client.create_data_store(request=request)
        print("  ⏳ Aguardando criação (pode levar alguns segundos)...")
        response = operation.result(timeout=120)

        print(f"  ✅ Data Store criado: {response.name}")
        return response.name.split('/')[-1]

    except exceptions.AlreadyExists:
        print(f"  ℹ️  Data store '{data_store_id}' já existe")
        return data_store_id
    except Exception as e:
        print(f"  ❌ Erro ao criar: {e}")
        return None

def main():
    print("="*60)
    print("📦 GERENCIAMENTO DE DATA STORES")
    print("="*60)

    project, location = get_project_and_location()
    print(f"\n🎯 Projeto: {project}")
    print(f"📍 Location: {location}")

    # Setup client
    try:
        client_options = None
        if location != "global":
            api_endpoint = f"{location}-discoveryengine.googleapis.com"
            client_options = {"api_endpoint": api_endpoint}
            print(f"🌐 Endpoint: {api_endpoint}")

        client = discoveryengine.DataStoreServiceClient(client_options=client_options)
        parent = f"projects/{project}/locations/{location}/collections/default_collection"
        print(f"📂 Parent: {parent}")

    except Exception as e:
        print(f"\n❌ Erro ao criar client: {e}")
        print("\n🔧 FIX: Verifique se a API está habilitada:")
        print(f"   gcloud services enable discoveryengine.googleapis.com --project={project}")
        sys.exit(1)

    # Lista existentes
    has_stores = list_data_stores(client, parent)

    # Se não tem nenhum, oferece criar
    if not has_stores:
        print("\n💡 Nenhum data store encontrado. Deseja criar um de teste? (y/n)")
        response = input(">>> ").strip().lower()

        if response == 'y':
            data_store_id = create_sample_data_store(client, parent)
            if data_store_id:
                print("\n" + "="*60)
                print("✅ PRÓXIMO PASSO: Popular o data store")
                print("="*60)
                print(f"\n📝 Salve este ID para usar nas queries:")
                print(f"   export DATA_STORE_ID='{data_store_id}'")
                print("\n🔧 Para adicionar documentos:")
                print("   1. Via Console: https://console.cloud.google.com/gen-app-builder")
                print("   2. Via API: usar ImportDocumentsRequest (próximo script)")
    else:
        print("\n✅ Você já tem data stores configurados!")
        print("📝 Use um deles para fazer queries no próximo script")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
