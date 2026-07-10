#!/usr/bin/env python3
"""
LOAD TEST - DIALOGFLOW CX (R$ 3.646,57)

Baseado no Relatório Técnico - Seção 4
Consome o crédito "Dialogflow CX Trial" através de sessões de chat

ESTRATÉGIA:
- Simula múltiplos usuários (sessões únicas)
- Cada detect_intent = 1 requisição cobrada
- Text session: ~$0.007 por requisição
- Com R$ 3.646,57 ≈ 93,503 sessões até esgotar (na prática, menos)

IMPORTANTE: Você precisa ter um AGENT criado no Dialogflow CX primeiro!
Console: https://dialogflow.cloud.google.com/cx/
"""
import os
import sys
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import dialogflowcx_v3 as dialogflow
from google.auth import default

# Scripts de conversação para teste de carga
CONVERSATION_SCRIPTS = [
    ["Olá", "Quero informações sobre produtos", "Obrigado"],
    ["Oi", "Preciso de ajuda", "Qual o horário de atendimento?"],
    ["Bom dia", "Gostaria de falar sobre serviços", "Entendi, obrigado"],
    ["Boa tarde", "Tenho uma dúvida", "Pode me ajudar?"],
    ["Como faço para contratar?", "Quais são os preços?", "Ok, vou pensar"],
    ["Oi", "Status do meu pedido", "Pedido número 12345"],
    ["Olá", "Quero cancelar", "Confirmo o cancelamento"],
    ["Boa noite", "Informações de entrega", "Obrigado pela ajuda"],
    ["Preciso de suporte técnico", "Meu produto não funciona", "Já tentei reiniciar"],
    ["Oi", "Quero fazer uma reclamação", "O produto chegou danificado"],
]

class DialogflowCXBurner:
    def __init__(self, project_id, location, agent_id):
        self.project_id = project_id
        self.location = location
        self.agent_id = agent_id

        # Métricas
        self.total_sessions = 0
        self.total_interactions = 0
        self.successful_interactions = 0
        self.failed_interactions = 0
        self.total_cost_usd = 0.0
        self.start_time = None

        # Client setup
        client_options = None
        if location != "global":
            api_endpoint = f"{location}-dialogflow.googleapis.com:443"
            client_options = {"api_endpoint": api_endpoint}

        self.client = dialogflow.SessionsClient(client_options=client_options)

    def simulate_user_conversation(self, conversation_script, user_id):
        """
        Simula uma conversa completa de um usuário

        IMPORTANTE: Cada detect_intent = 1 cobrança
        Uma conversa de 3 mensagens = 3 cobranças
        """
        # Gera session ID único para este "usuário"
        session_id = str(uuid.uuid4())
        session_path = self.client.session_path(
            project=self.project_id,
            location=self.location,
            agent=self.agent_id,
            session=session_id,
        )

        results = []

        for message in conversation_script:
            try:
                # Cria input de texto
                text_input = dialogflow.TextInput(text=message)
                query_input = dialogflow.QueryInput(
                    text=text_input,
                    language_code="pt-BR"  # Português
                )

                request = dialogflow.DetectIntentRequest(
                    session=session_path,
                    query_input=query_input
                )

                # EXECUTA - ISTO CONSOME O CRÉDITO!
                response = self.client.detect_intent(request=request)

                # Parse resposta
                response_texts = []
                for msg in response.query_result.response_messages:
                    if msg.text and msg.text.text:
                        response_texts.extend(msg.text.text)

                self.successful_interactions += 1
                cost = 0.007  # ~$0.007 por text session
                self.total_cost_usd += cost

                results.append({
                    'status': 'success',
                    'user_input': message,
                    'agent_response': ' '.join(response_texts)[:100],
                    'intent': response.query_result.match.intent.display_name if response.query_result.match.intent else "N/A",
                    'cost_usd': cost
                })

            except Exception as e:
                self.failed_interactions += 1
                results.append({
                    'status': 'failed',
                    'user_input': message,
                    'error': str(e)
                })

        self.total_sessions += 1
        return {
            'session_id': session_id[:8],
            'user_id': user_id,
            'results': results
        }

    def run_load_test(self, num_conversations: int, max_workers: int = 5):
        """
        Executa load test simulando múltiplos usuários conversando

        Args:
            num_conversations: Quantas conversas completas simular
            max_workers: Threads paralelas (cuidado com rate limits!)
        """
        print("="*60)
        print("🔥 DIALOGFLOW CX - LOAD TEST")
        print("="*60)
        print(f"\n📊 Configuração:")
        print(f"   Projeto: {self.project_id}")
        print(f"   Location: {self.location}")
        print(f"   Agent: {self.agent_id}")
        print(f"   Conversas: {num_conversations}")
        print(f"   Workers: {max_workers}")

        # Estimativa de custo
        # Média de 3 mensagens por conversa
        avg_messages = 3
        estimated_interactions = num_conversations * avg_messages
        estimated_cost = estimated_interactions * 0.007

        print(f"\n💰 Estimativa:")
        print(f"   Interações: ~{estimated_interactions}")
        print(f"   Custo: ~${estimated_cost:.2f} USD")

        # Confirmação
        if os.getenv("AUTO_CONFIRM") != "true":
            response = input("\n🚀 Continuar? (y/n): ").strip().lower()
            if response != 'y':
                print("❌ Cancelado")
                return

        self.start_time = time.time()

        # Prepara conversas
        conversations_to_run = []
        for i in range(num_conversations):
            script = CONVERSATION_SCRIPTS[i % len(CONVERSATION_SCRIPTS)]
            conversations_to_run.append((i, script))

        print(f"\n⏳ Simulando {num_conversations} conversas...")
        print("=" * 60)

        # Executa em paralelo
        all_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.simulate_user_conversation, script, user_id): user_id
                for user_id, script in conversations_to_run
            }

            for future in as_completed(futures):
                result = future.result()
                all_results.append(result)

                # Progress
                if len(all_results) % 10 == 0:
                    elapsed = time.time() - self.start_time
                    cps = len(all_results) / elapsed if elapsed > 0 else 0
                    print(f"   [{len(all_results)}/{num_conversations}] "
                          f"Sessões: {self.total_sessions} | "
                          f"Interações: {self.successful_interactions} | "
                          f"CPS: {cps:.2f} | "
                          f"Custo: ${self.total_cost_usd:.4f}")

        # Relatório
        self.print_final_report(all_results)

    def print_final_report(self, all_results):
        """Relatório final"""
        elapsed_time = time.time() - self.start_time

        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL - DIALOGFLOW CX")
        print("="*60)

        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Tempo Total: {elapsed_time:.2f}s")
        print(f"   Conversas/segundo: {len(all_results) / elapsed_time:.2f}")

        print(f"\n✅ RESULTADOS:")
        print(f"   Total de Sessões: {self.total_sessions}")
        print(f"   Total de Interações: {self.total_interactions}")
        print(f"   Sucesso: {self.successful_interactions}")
        print(f"   Falhas: {self.failed_interactions}")
        if self.total_interactions > 0:
            print(f"   Taxa de Sucesso: {(self.successful_interactions/self.total_interactions*100):.1f}%")

        print(f"\n💰 CONSUMO DE CRÉDITOS:")
        print(f"   Custo Total: ${self.total_cost_usd:.4f} USD")
        print(f"   Custo por Interação: ${self.total_cost_usd/self.total_interactions:.6f} USD")

        # Conversão BRL
        brl_rate = 5.5
        cost_brl = self.total_cost_usd * brl_rate
        remaining_credit = 3646.57 - cost_brl

        print(f"\n💳 CRÉDITO DIALOGFLOW CX:")
        print(f"   Consumido: R$ {cost_brl:.2f}")
        print(f"   Restante: R$ {remaining_credit:.2f}")
        print(f"   % Usado: {(cost_brl/3646.57*100):.2f}%")

        # Amostras
        print(f"\n📝 AMOSTRAS DE CONVERSAS:")
        for i, conv in enumerate(all_results[:3]):
            print(f"\n   Conversa {i+1} (Session: {conv['session_id']}...):")
            for interaction in conv['results'][:2]:  # Primeiras 2 interações
                if interaction['status'] == 'success':
                    print(f"      👤 User: {interaction['user_input']}")
                    print(f"      🤖 Agent: {interaction['agent_response']}...")
                    print(f"      🎯 Intent: {interaction['intent']}")

def main():
    print("="*60)
    print("🔥 DIALOGFLOW CX - CREDIT BURNER")
    print("="*60)

    # Config
    _, project = default()
    location = os.getenv("DIALOGFLOW_LOCATION", "us-central1")  # Dialogflow usa regional
    agent_id = os.getenv("DIALOGFLOW_AGENT_ID")

    if not agent_id:
        print("\n❌ DIALOGFLOW_AGENT_ID não configurado!")
        print("\n🔧 SETUP:")
        print("1. Crie um Agent em: https://dialogflow.cloud.google.com/cx/")
        print("2. Copie o Agent ID (formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)")
        print("3. Export:")
        print("   export DIALOGFLOW_AGENT_ID='seu-agent-id'")
        print("   export DIALOGFLOW_LOCATION='us-central1'  # ou sua região")
        sys.exit(1)

    num_conversations = int(os.getenv("NUM_CONVERSATIONS", "50"))
    max_workers = int(os.getenv("MAX_WORKERS", "5"))

    # Burn!
    burner = DialogflowCXBurner(project, location, agent_id)
    burner.run_load_test(num_conversations, max_workers)

if __name__ == "__main__":
    main()
