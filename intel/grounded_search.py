import os
import sys

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import discoveryengine_v1beta as discoveryengine

# Removido: from dotenv import load_dotenv
# Removido: load_dotenv()


def get_env_var(var_name):
    # Pega direto do ambiente do sistema
    value = os.getenv(var_name)
    if (
        not value or "SEU_ID" in value
    ):  # Checagem simples pra evitar rodar com placeholder
        print(
            f"ERRO: A variável '{var_name}' não foi encontrada ou ainda é o placeholder."
        )
        print(
            "Dica: Verifique se você editou o 'flake.nix' e rodou 'nix develop' ou recarregou o direnv."
        )
        sys.exit(1)
    return value


def run_grounded_search():
    project_id = get_env_var("GOOGLE_CLOUD_PROJECT_ID")
    # As outras têm defaults caso o Nix não injete, mas o ideal é vir do flake
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    model_id = os.getenv("GENAI_MODEL", "gemini-1.5-flash")
    query_text = os.getenv("SEARCH_QUERY", "Explique o que é Kubernetes.")

    print(f"🚀 Iniciando busca...")
    print(f"   Projeto: {project_id}")
    print(f"   Query: {query_text}")

    try:
        # Define o endpoint regional se necessário
        client_options = None
        if location != "global":
            client_options = {
                "api_endpoint": f"{location}-discoveryengine.googleapis.com"
            }

        print(f"DEBUG: client_options={client_options}")
        client = discoveryengine.GroundedGenerationServiceClient(
            client_options=client_options
        )
        location_path = client.common_location_path(
            project=project_id, location=location
        )
        print(f"DEBUG: location_path={location_path}")

        request = discoveryengine.GenerateGroundedContentRequest(
            location=location_path,
            generation_spec=discoveryengine.GenerateGroundedContentRequest.GenerationSpec(
                model_id=model_id,
            ),
            contents=[
                discoveryengine.GroundedGenerationContent(
                    role="user",
                    parts=[
                        discoveryengine.GroundedGenerationContent.Part(text=query_text)
                    ],
                )
            ],
            grounding_spec=discoveryengine.GenerateGroundedContentRequest.GroundingSpec(
                grounding_sources=[
                    discoveryengine.GenerateGroundedContentRequest.GroundingSource(
                        google_search_source=discoveryengine.GenerateGroundedContentRequest.GroundingSource.GoogleSearchSource()
                    )
                ]
            ),
        )

        response = client.generate_grounded_content(request)

        print("\n" + "=" * 40)
        print("RESPOSTA (Via Vertex AI Grounding):")
        print("=" * 40)
        for candidate in response.candidates:
            for part in candidate.content.parts:
                print(part.text, end="")
        print("\n" + "=" * 40)

    except GoogleAPICallError as e:
        print(f"\n❌ Erro na API: {e.message}")
        print(
            f"Detalhes: Verifique se a API 'Discovery Engine' está ativada no projeto {project_id}"
        )
    except Exception as e:
        print(f"\n❌ Erro: {e}")


if __name__ == "__main__":
    run_grounded_search()
