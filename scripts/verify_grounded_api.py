#!/usr/bin/env python3
"""
TESTE: GroundedGenerationServiceClient - v1 vs v1beta

Baseado na pesquisa, vamos testar se o problema é usar v1beta
quando deveríamos usar v1 (stable)
"""
import sys
from google.auth import default

print("="*60)
print("🔬 TESTE: Grounded Generation API v1 vs v1beta")
print("="*60)

_, project = default()

# Teste 1: v1beta (o que estamos usando e FALHA)
print("\n[TEST 1] Tentando com v1beta...")
try:
    from google.cloud import discoveryengine_v1beta as discoveryengine_beta

    client_beta = discoveryengine_beta.GroundedGenerationServiceClient()
    location_path = f"projects/{project}/locations/global"

    request_beta = discoveryengine_beta.GenerateGroundedContentRequest(
        location=location_path,
        generation_spec=discoveryengine_beta.GenerateGroundedContentRequest.GenerationSpec(
            model_id="gemini-1.5-flash",
        ),
        contents=[
            discoveryengine_beta.GroundedGenerationContent(
                role="user",
                parts=[discoveryengine_beta.GroundedGenerationContent.Part(text="What is AI?")],
            )
        ],
        grounding_spec=discoveryengine_beta.GenerateGroundedContentRequest.GroundingSpec(
            grounding_sources=[
                discoveryengine_beta.GenerateGroundedContentRequest.GroundingSource(
                    google_search_source=discoveryengine_beta.GenerateGroundedContentRequest.GroundingSource.GoogleSearchSource()
                )
            ]
        )
    )

    response_beta = client_beta.generate_grounded_content(request_beta)
    print("✅ v1beta FUNCIONOU!")
    print(f"   Response: {response_beta}")

except Exception as e:
    print(f"❌ v1beta FALHOU: {e}")

# Teste 2: v1 (stable)
print("\n[TEST 2] Tentando com v1 (stable)...")
try:
    from google.cloud import discoveryengine_v1 as discoveryengine_v1

    client_v1 = discoveryengine_v1.GroundedGenerationServiceClient()
    location_path_v1 = f"projects/{project}/locations/global"

    request_v1 = discoveryengine_v1.GenerateGroundedContentRequest(
        location=location_path_v1,
        generation_spec=discoveryengine_v1.GenerateGroundedContentRequest.GenerationSpec(
            model_id="gemini-1.5-flash",
        ),
        contents=[
            discoveryengine_v1.GroundedGenerationContent(
                role="user",
                parts=[discoveryengine_v1.GroundedGenerationContent.Part(text="What is AI?")],
            )
        ],
        grounding_spec=discoveryengine_v1.GenerateGroundedContentRequest.GroundingSpec(
            grounding_sources=[
                discoveryengine_v1.GenerateGroundedContentRequest.GroundingSource(
                    google_search_source=discoveryengine_v1.GenerateGroundedContentRequest.GroundingSource.GoogleSearchSource()
                )
            ]
        )
    )

    response_v1 = client_v1.generate_grounded_content(request_v1)
    print("✅ v1 FUNCIONOU!")
    print(f"   Response: {response_v1}")

except Exception as e:
    print(f"❌ v1 FALHOU: {e}")

# Teste 3: Informações sobre disponibilidade
print("\n[TEST 3] Verificando disponibilidade da API...")
try:
    from google.cloud import discoveryengine_v1

    client = discoveryengine_v1.GroundedGenerationServiceClient()

    print(f"✅ Client criado com sucesso")
    print(f"   Endpoint: {client._api_endpoint}")
    print(f"   Transport: {type(client._transport).__name__}")

    # Tenta obter metadata do serviço
    print(f"\n📋 Métodos disponíveis no client:")
    grounding_methods = [m for m in dir(client) if 'ground' in m.lower() and not m.startswith('_')]
    for method in grounding_methods:
        print(f"   - {method}")

except Exception as e:
    print(f"❌ Erro ao inspecionar client: {e}")

print("\n" + "="*60)
print("📝 CONCLUSÃO")
print("="*60)
print("""
Se AMBOS falharam com 'Method not found':
  → A API pode estar em preview/allowlist apenas
  → Seu projeto pode não ter acesso
  → A funcionalidade pode ter sido movida para outra API

Se um deles FUNCIONOU:
  → Use a versão que funcionou!
  → Atualize grounded_generation.py com a versão correta
""")
