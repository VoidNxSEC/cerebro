#!/usr/bin/env python3
"""
GROUNDED GENERATION API - THE REAL DEAL
Based on Gemini Deep Research findings (Dec 2025)

CONFIRMADO:
  ✅ Esta é a API CORRETA para usar os Trial credits
  ✅ Billing model: charge bruto + promotional refund = net $0
  ✅ Precisa billing account configurada (mesmo usando credits)
"""
import os
import sys
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.auth import default
from google.api_core.exceptions import GoogleAPICallError

def validate_setup():
    """Validações CRÍTICAS antes de chamar API"""
    print("🔍 Validando setup...")

    # 1. Auth
    try:
        credentials, project = default()
        print(f"✅ Auth OK: {project}")
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        print("\n🔧 FIX: gcloud auth application-default login")
        sys.exit(1)

    # 2. Billing account (CRÍTICO - mesmo usando credits!)
    print("\n💳 Billing Account Check:")
    print("   ⚠️  IMPORTANTE: Você PRECISA ter cartão cadastrado")
    print("   Motivo: API cobra primeiro, DEPOIS credita")
    print("   Net result = $0 (se credits aplicados)")
    print()
    print("   Verifique em:")
    print(f"   https://console.cloud.google.com/billing/projects/{project}")

    # 3. API habilitada
    print("\n🔌 API Check:")
    print("   Execute se ainda não fez:")
    print(f"   gcloud services enable discoveryengine.googleapis.com --project={project}")

    return project

def run_grounded_generation(
    project_id: str,
    location: str = "global",  # ← CRITICAL: tenta "global" primeiro
    query: str = "What is VOID FORTRESS?",
    model_id: str = "gemini-2.5-flash"
):
    """
    Grounded Generation API - Configuração Refinada

    DEBUGGING GUIDE baseado no 404 que você teve:

    1. Location: Tenta "global" primeiro
       - Se 404: tenta "us-central1"
       - Se ainda 404: tenta "us"

    2. Endpoint: Precisa do regional endpoint correto
       - global: discoveryengine.googleapis.com
       - regional: {location}-discoveryengine.googleapis.com

    3. Location path: Formato EXATO importa
       - projects/{project}/locations/{location}
    """
    print("\n" + "="*60)
    print("🚀 GROUNDED GENERATION API - REFINED")
    print("="*60)
    print(f"📍 Location: {location}")
    print(f"🤖 Model: {model_id}")
    print(f"❓ Query: {query}")

    try:
        # Client setup com endpoint CORRETO
        client_options = None
        if location != "global":
            api_endpoint = f"{location}-discoveryengine.googleapis.com"
            client_options = {"api_endpoint": api_endpoint}
            print(f"🌐 Endpoint: {api_endpoint}")
        else:
            print(f"🌐 Endpoint: discoveryengine.googleapis.com (global)")

        client = discoveryengine.GroundedGenerationServiceClient(
            client_options=client_options
        )

        # Location path - formato EXATO
        location_path = f"projects/{project_id}/locations/{location}"
        print(f"📂 Path: {location_path}")

        # Request configuration
        request = discoveryengine.GenerateGroundedContentRequest(
            location=location_path,

            # Generation spec
            generation_spec=discoveryengine.GenerateGroundedContentRequest.GenerationSpec(
                model_id=model_id,
                # Opcional: temperature, top_p, etc
            ),

            # User query
            contents=[
                discoveryengine.GroundedGenerationContent(
                    role="user",
                    parts=[
                        discoveryengine.GroundedGenerationContent.Part(text=query)
                    ]
                )
            ],

            # Grounding source - Google Search
            grounding_spec=discoveryengine.GenerateGroundedContentRequest.GroundingSpec(
                grounding_sources=[
                    discoveryengine.GenerateGroundedContentRequest.GroundingSource(
                        google_search_source=discoveryengine.GenerateGroundedContentRequest.GroundingSource.GoogleSearchSource()
                    )
                ]
            )
        )

        # Execute
        print("\n⏳ Executando request...")
        print("   (Pode levar 5-15 segundos)")

        response = client.generate_grounded_content(request)

        # Success!
        print("\n" + "="*60)
        print("✅ SUCESSO! CÓDIGO 200!")
        print("="*60)

        # Display response
        print("\n📝 RESPOSTA:")
        print("-" * 60)
        for candidate in response.candidates:
            for part in candidate.content.parts:
                print(part.text)
        print("-" * 60)

        # Grounding metadata (se disponível)
        if hasattr(response, 'grounding_metadata'):
            print("\n📚 GROUNDING SOURCES:")
            # TODO: parse grounding sources
            print("   (Fontes web usadas na resposta)")

        # Billing info
        print("\n💰 BILLING INFO:")
        print("   API: Grounded Generation (Google Search)")
        print("   Custo bruto: $35.00 / 1,000 queries")
        print("   Esta query: ~$0.035")
        print()
        print("   📊 COMO VALIDAR CREDITS:")
        print("   1. Aguarde 24-48h (billing sync)")
        print("   2. Acesse: https://console.cloud.google.com/billing/")
        print("   3. Procure por:")
        print("      • Charge: 'Grounded Generation API' +$0.035")
        print("      • Credit: 'Promotional (GenAI App Builder)' -$0.035")
        print("      • Net: $0.00")
        print()
        print("   Se não aparecer promotional credit:")
        print("   → Credits não foram aplicados")
        print("   → Você foi cobrado na billing account")
        print("   → Precisa troubleshoot enrollment")

        return response

    except GoogleAPICallError as e:
        print("\n" + "="*60)
        print(f"❌ ERRO: {e.message}")
        print("="*60)

        # Debugging específico por erro
        if "404" in str(e):
            print("\n🔧 TROUBLESHOOTING 404:")
            print(f"   Tentou location: {location}")
            print()
            print("   OPÇÕES:")
            print("   1. Tenta location='us-central1':")
            print(f"      export GOOGLE_CLOUD_LOCATION='us-central1'")
            print()
            print("   2. Verifica se API tá habilitada:")
            print(f"      gcloud services list --enabled --project={project_id} | grep discovery")
            print()
            print("   3. Verifica permissões:")
            print("      Precisa role: roles/discoveryengine.admin")

        elif "403" in str(e):
            print("\n🔧 TROUBLESHOOTING 403:")
            print("   1. API não habilitada:")
            print(f"      gcloud services enable discoveryengine.googleapis.com --project={project_id}")
            print()
            print("   2. Permissões:")
            print("      gcloud projects add-iam-policy-binding {project_id} \\")
            print("        --member='user:SEU_EMAIL' \\")
            print("        --role='roles/discoveryengine.admin'")

        elif "400" in str(e):
            print("\n🔧 TROUBLESHOOTING 400:")
            print("   Provavelmente request malformado")
            print("   Verifique:")
            print(f"   • Model ID: {model_id}")
            print(f"   • Location path: {location_path}")

        return None

    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        print(f"   Type: {type(e)}")
        return None

def main():
    print("="*60)
    print("🎯 GROUNDED GENERATION - VALIDATED APPROACH")
    print("="*60)
    print("\n📜 Based on Gemini Deep Research findings:")
    print("   ✅ This IS the correct API for Trial credits")
    print("   ✅ Billing model: charge + promotional refund")
    print("   ✅ Requires billing account (even for free usage)")
    print()

    # Validate
    project = validate_setup()

    # Config
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    query = os.getenv("SEARCH_QUERY", "What is VOID FORTRESS?")

    print("\n" + "="*60)
    print("🚦 READY TO RUN")
    print("="*60)
    print(f"Project: {project}")
    print(f"Location: {location}")
    print(f"Query: {query}")
    print()

    # Confirma
    print("⚠️  Isso vai fazer UMA query que:")
    print("   • Cobra ~$0.035 bruto")
    print("   • Deve ser refundado via promotional credit")
    print("   • Net esperado: $0.00")
    print()

    if os.getenv("AUTO_CONFIRM") != "true":
        print("Continuar? (y/n)")
        response = input(">>> ").strip().lower()
        if response != 'y':
            print("❌ Cancelado")
            return

    # RUN
    result = run_grounded_generation(
        project_id=project,
        location=location,
        query=query
    )

    if result:
        print("\n" + "="*60)
        print("🎉 VALIDAÇÃO COMPLETA!")
        print("="*60)
        print("\n📝 PRÓXIMOS PASSOS:")
        print("   1. ✅ Código funcionou (200 OK)")
        print("   2. ⏰ Aguarde 48h")
        print("   3. 📊 Check billing reports")
        print("   4. ✅ Confirme promotional credit offset")
        print()
        print("   Se offset aparecer: 🎉 SUCESSO TOTAL")
        print("   Se não aparecer: 🔧 Troubleshoot enrollment")
    else:
        print("\n⚠️  Código não executou")
        print("   Siga troubleshooting acima")

if __name__ == "__main__":
    main()
