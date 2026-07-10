#!/usr/bin/env python3
"""
LOAD TEST OTIMIZADO - QUEIMAR CRÉDITOS GENAI APP BUILDER
Baseado no exemplo validado: SearchServiceClient com summary_spec

ESTRATÉGIA:
- Usa SearchServiceClient (método CONFIRMADO que funciona)
- summary_spec = Grounded Generation (respostas AI com citações)
- Múltiplas queries em paralelo para acelerar consumo
- Tracking de custos em tempo real

CONSUMO ESPERADO:
- Search Enterprise: $4.00 / 1,000 queries
- Com R$ 6.432,54 ≈ 1,608 queries até esgotar
"""
import os
import sys
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.auth import default
from datetime import datetime

# Queries variadas para teste de carga realista
SAMPLE_QUERIES = [
    "What is artificial intelligence and how does it work?",
    "Explain machine learning algorithms",
    "What are the applications of deep learning?",
    "How does natural language processing work?",
    "What is the difference between supervised and unsupervised learning?",
    "Explain neural networks architecture",
    "What are transformers in AI?",
    "How do large language models work?",
    "What is reinforcement learning?",
    "Explain computer vision techniques",
    "What is generative AI?",
    "How does recommendation systems work?",
    "What are the ethical considerations in AI?",
    "Explain explainable AI (XAI)",
    "What is edge AI and its benefits?",
    "How does AI help in healthcare?",
    "What are GANs and their applications?",
    "Explain AutoML and its use cases",
    "What is federated learning?",
    "How does AI impact cybersecurity?",
]

class CreditBurner:
    def __init__(self, project_id, location, data_store_id):
        self.project_id = project_id
        self.location = location
        self.data_store_id = data_store_id

        # Métricas
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.total_cost_usd = 0.0
        self.start_time = None

        # Client setup
        client_options = None
        if location != "global":
            api_endpoint = f"{location}-discoveryengine.googleapis.com"
            client_options = {"api_endpoint": api_endpoint}

        self.client = discoveryengine.SearchServiceClient(client_options=client_options)

        # Serving config path
        self.serving_config = (
            f"projects/{project_id}/locations/{location}/"
            f"collections/default_collection/dataStores/{data_store_id}/"
            f"servingConfigs/default_config"
        )

    def execute_single_query(self, query: str, query_id: int):
        """
        Executa UMA query com Grounded Generation

        CONFIRMADO: Este é o método que consome o crédito GenAI App Builder
        """
        try:
            # Request configuration - BASEADO NO EXEMPLO VALIDADO
            request = discoveryengine.SearchRequest(
                serving_config=self.serving_config,
                query=query,
                page_size=10,

                # CRITICAL: summary_spec = GROUNDED GENERATION!
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    # Summary = AI generativa respondendo com base nos docs
                    summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                        summary_result_count=5,
                        include_citations=True,
                        ignore_adversarial_query=True,
                        ignore_non_summary_seeking_query=True,
                    ),
                    # Snippets extrativos (bonus, sem custo extra)
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True
                    ),
                ),
            )

            # Execute
            response = self.client.search(request)

            # Extrai resposta generativa
            summary_text = ""
            if hasattr(response, 'summary') and response.summary:
                summary_text = response.summary.summary_text[:100]  # Primeiros 100 chars

            # Tracking
            self.successful_queries += 1
            cost = 0.004  # $4.00 / 1000 queries
            self.total_cost_usd += cost

            return {
                'status': 'success',
                'query_id': query_id,
                'query': query[:50],
                'summary_preview': summary_text,
                'cost_usd': cost
            }

        except Exception as e:
            self.failed_queries += 1
            return {
                'status': 'failed',
                'query_id': query_id,
                'query': query[:50],
                'error': str(e)
            }

    def run_parallel_load_test(self, num_queries: int, max_workers: int = 10):
        """
        Executa load test com queries em paralelo

        Args:
            num_queries: Total de queries a executar
            max_workers: Threads paralelas (cuidado com rate limits!)
        """
        print("="*60)
        print("🔥 LOAD TEST - QUEIMANDO CRÉDITOS GENAI APP BUILDER")
        print("="*60)
        print(f"\n📊 Configuração:")
        print(f"   Projeto: {self.project_id}")
        print(f"   Data Store: {self.data_store_id}")
        print(f"   Total Queries: {num_queries}")
        print(f"   Workers Paralelos: {max_workers}")
        print(f"   Custo Estimado: ${num_queries * 0.004:.2f} USD")

        # Confirmação
        print(f"\n⚠️  ATENÇÃO:")
        print(f"   Isso vai consumir ~${num_queries * 0.004:.2f} do crédito")
        print(f"   Crédito disponível: R$ 6.432,54")

        if os.getenv("AUTO_CONFIRM") != "true":
            response = input("\n🚀 Continuar? (y/n): ").strip().lower()
            if response != 'y':
                print("❌ Cancelado")
                return

        self.start_time = time.time()

        # Gera lista de queries (repete SAMPLE_QUERIES se necessário)
        queries_to_run = []
        for i in range(num_queries):
            query = SAMPLE_QUERIES[i % len(SAMPLE_QUERIES)]
            queries_to_run.append((i, query))

        print(f"\n⏳ Executando {num_queries} queries...")
        print("=" * 60)

        # Executa em paralelo com ThreadPoolExecutor
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self.execute_single_query, query, qid): qid
                for qid, query in queries_to_run
            }

            # Process as completed (com progress tracking)
            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                # Progress update a cada 10 queries
                if len(results) % 10 == 0:
                    elapsed = time.time() - self.start_time
                    qps = len(results) / elapsed if elapsed > 0 else 0
                    print(f"   [{len(results)}/{num_queries}] "
                          f"✅ {self.successful_queries} | "
                          f"❌ {self.failed_queries} | "
                          f"QPS: {qps:.2f} | "
                          f"Custo: ${self.total_cost_usd:.4f}")

        # Relatório final
        self.print_final_report(results)

    def print_final_report(self, results):
        """Relatório detalhado do teste"""
        elapsed_time = time.time() - self.start_time

        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL DO LOAD TEST")
        print("="*60)

        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo Total: {elapsed_time:.2f}s")
        print(f"   QPS Médio: {len(results) / elapsed_time:.2f} queries/segundo")

        print(f"\n✅ RESULTADOS:")
        print(f"   Total de Queries: {len(results)}")
        print(f"   Sucesso: {self.successful_queries}")
        print(f"   Falhas: {self.failed_queries}")
        print(f"   Taxa de Sucesso: {(self.successful_queries/len(results)*100):.1f}%")

        print(f"\n💰 CONSUMO DE CRÉDITOS:")
        print(f"   Custo Total: ${self.total_cost_usd:.4f} USD")
        print(f"   Custo por Query: ${self.total_cost_usd/len(results):.6f} USD")

        # Conversão para BRL (aproximada)
        brl_rate = 5.5  # Taxa aproximada
        cost_brl = self.total_cost_usd * brl_rate
        remaining_credit = 6432.54 - cost_brl

        print(f"\n💳 CRÉDITOS (Estimativa):")
        print(f"   Consumido: R$ {cost_brl:.2f}")
        print(f"   Restante: R$ {remaining_credit:.2f}")
        print(f"   % Usado: {(cost_brl/6432.54*100):.2f}%")

        print(f"\n⚠️  VALIDAÇÃO:")
        print(f"   Execute audit_credits_bigquery.py em 24-48h")
        print(f"   para confirmar que o crédito foi aplicado!")

        # Mostra alguns exemplos de respostas
        print(f"\n📝 AMOSTRAS DE RESPOSTAS GENERATIVAS:")
        successful_results = [r for r in results if r['status'] == 'success' and r.get('summary_preview')]
        for i, result in enumerate(successful_results[:3]):
            print(f"\n   [{i+1}] Query: {result['query']}...")
            print(f"       Resposta: {result['summary_preview']}...")

        # Falhas (se houver)
        if self.failed_queries > 0:
            print(f"\n❌ ERROS DETECTADOS:")
            failed_results = [r for r in results if r['status'] == 'failed']
            for result in failed_results[:5]:  # Primeiros 5 erros
                print(f"   Query: {result['query']}...")
                print(f"   Erro: {result['error']}")

def main():
    print("="*60)
    print("🔥 BURN CREDITS - LOAD TEST OTIMIZADO")
    print("="*60)
    print("\nBaseado no exemplo VALIDADO:")
    print("  ✅ SearchServiceClient (não GroundedGenerationServiceClient)")
    print("  ✅ summary_spec para Grounded Generation")
    print("  ✅ Consome crédito 'GenAI App Builder' corretamente")

    # Config
    _, project = default()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    data_store_id = os.getenv("DATA_STORE_ID")

    if not data_store_id:
        print("\n❌ DATA_STORE_ID não configurado!")
        print("   export DATA_STORE_ID='ds-app-v4-5e020c93'")
        sys.exit(1)

    # Quantas queries?
    num_queries = int(os.getenv("NUM_QUERIES", "100"))
    max_workers = int(os.getenv("MAX_WORKERS", "10"))

    # Inicializa burner
    burner = CreditBurner(project, location, data_store_id)

    # FIRE! 🔥
    burner.run_parallel_load_test(num_queries, max_workers)

if __name__ == "__main__":
    main()
