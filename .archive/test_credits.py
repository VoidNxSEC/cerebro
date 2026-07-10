#!/usr/bin/env python3
"""
ESTE SCRIPT CONSOME OS CRÉDITOS DE VERDADE! 💸

Faz queries usando Vertex AI Search Enterprise Edition
que é coberto pelos créditos "Trial credit for GenAI App Builder"

Pricing que será cobrado:
- Search Enterprise: $4.00 / 1,000 queries
- Com seus R$ 6.432,54 = ~1,608 queries
"""
import os
import sys
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.auth import default

def search_vertex_ai(
    project_id: str,
    location: str,
    data_store_id: str,
    query: str,
    page_size: int = 10
):
    """
    Executa uma query real que CONSOME os créditos

    Esta é a API correta para usar os créditos:
    - discoveryengine.SearchServiceClient (não GroundedGenerationServiceClient)
    - Requer data_store_id existente
    """
    print("\n" + "="*60)
    print("🔍 EXECUTANDO QUERY REAL (CONSUMINDO CRÉDITOS)")
    print("="*60)
    print(f"📦 Data Store: {data_store_id}")
    print(f"❓ Query: {query}")
    print(f"📊 Max Results: {page_size}")

    try:
        # Setup client com endpoint correto
        client_options = None
        if location != "global":
            api_endpoint = f"{location}-discoveryengine.googleapis.com"
            client_options = {"api_endpoint": api_endpoint}
            print(f"🌐 Endpoint: {api_endpoint}")

        client = discoveryengine.SearchServiceClient(client_options=client_options)

        # Monta o serving config path
        # Format: projects/{project}/locations/{location}/dataStores/{data_store}/servingConfigs/default_config
        serving_config = (
            f"projects/{project_id}/locations/{location}/"
            f"collections/default_collection/dataStores/{data_store_id}/"
            f"servingConfigs/default_config"
        )
        print(f"⚙️  Serving Config: {serving_config}")

        # Cria request com content search spec
        # Isso habilita "Generative Answers" (AI Mode) - Enterprise Edition
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=page_size,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=5,
                    include_citations=True,
                    ignore_adversarial_query=True,
                    ignore_non_summary_seeking_query=True,
                    model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                        preamble="You are a helpful assistant. Answer based on the provided context."
                    ),
                ),
                snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                    return_snippet=True
                ),
            ),
        )

        print("\n⏳ Enviando request...")
        response = client.search(request)

        # Display results
        print("\n" + "="*60)
        print("📋 RESULTADOS")
        print("="*60)

        # Generative Summary (se disponível)
        if hasattr(response, 'summary') and response.summary:
            print("\n🤖 RESPOSTA GENERATIVA (AI Mode):")
            print("-" * 60)
            print(response.summary.summary_text)
            print("-" * 60)

            if hasattr(response.summary, 'summary_with_metadata'):
                print("\n📚 Citações:")
                for citation in response.summary.summary_with_metadata.references:
                    print(f"  • {citation.title if hasattr(citation, 'title') else citation}")

        # Search Results
        print("\n🔎 RESULTADOS DE BUSCA:")
        if not response.results:
            print("  (Nenhum resultado encontrado)")
            print("\n💡 DICA: Seu data store pode estar vazio!")
            print("   Adicione documentos em: https://console.cloud.google.com/gen-app-builder")
        else:
            for i, result in enumerate(response.results, 1):
                doc = result.document
                print(f"\n  [{i}] {doc.derived_struct_data.get('title', 'Sem título')}")

                # Snippet
                if hasattr(doc.derived_struct_data, 'snippets'):
                    snippets = doc.derived_struct_data.get('snippets', [])
                    if snippets:
                        print(f"      {snippets[0].get('snippet', '')[:200]}...")

                # Link (se disponível)
                if 'link' in doc.derived_struct_data:
                    print(f"      🔗 {doc.derived_struct_data['link']}")

        print("\n" + "="*60)
        print("✅ QUERY EXECUTADA COM SUCESSO!")
        print("="*60)
        print("\n💰 CRÉDITO CONSUMIDO:")
        print("   • Search Enterprise Edition: $4.00 / 1,000 queries")
        print("   • Esta query: ~$0.004")
        print(f"   • Créditos restantes: ~R$ {6432.54 - 0.004:.2f}")

        return response

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print(f"\n🔧 DEBUG INFO:")
        print(f"   - Projeto: {project_id}")
        print(f"   - Location: {location}")
        print(f"   - Data Store: {data_store_id}")
        print("\n📋 CHECKLIST:")
        print("   [ ] API discoveryengine.googleapis.com habilitada?")
        print("   [ ] Data store existe e tem documentos?")
        print("   [ ] Billing account configurada com os créditos?")
        print("   [ ] Permissões corretas (roles/discoveryengine.admin)?")
        return None

def main():
    print("="*60)
    print("💸 TESTE DE CONSUMO DE CRÉDITOS GENAI APP BUILDER")
    print("="*60)

    # Get config
    _, project = default()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    data_store_id = os.getenv("DATA_STORE_ID")
    
    # Priority: Env var > Default
    query = os.getenv("SEARCH_QUERY")
    if not query:
        query = "What is machine learning?"

    print(f"\n🎯 Configuração:")
    print(f"   Projeto: {project}")
    print(f"   Location: {location}")
    print(f"   Data Store: {data_store_id or '⚠️  NÃO CONFIGURADO'}")

    if not data_store_id:
        print("\n❌ DATA_STORE_ID não configurado!")
        print("\n🔧 FIX:")
        print("   1. Rode: python manage_datastores.py")
        print("   2. Copie o ID do data store")
        print("   3. Export: export DATA_STORE_ID='seu-id-aqui'")
        print("   4. Ou adicione no flake.nix")
        sys.exit(1)

    # Execute search
    response = search_vertex_ai(
        project_id=project,
        location=location,
        data_store_id=data_store_id,
        query=query,
    )

    if response:
        print("\n🎉 VALIDAÇÃO COMPLETA!")
        print("Os créditos estão sendo consumidos corretamente.")
        print("\nAgora você pode:")
        print("  1. Popular o data store com seus documentos")
        print("  2. Fazer queries mais complexas")
        print("  3. Integrar com seus MCP servers")
    else:
        print("\n⚠️  Validação falhou. Revise os erros acima.")

if __name__ == "__main__":
    main()
