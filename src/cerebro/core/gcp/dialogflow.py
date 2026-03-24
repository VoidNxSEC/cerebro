#!/usr/bin/env python3
"""
Dialogflow CX Manager

Consolidated from burn_dialogflow_cx.py
Manages Dialogflow CX sessions and conversations
"""
import os
import sys
import uuid
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from google.cloud import dialogflowcx_v3 as dialogflow
    from google.auth import default
    DIALOGFLOW_AVAILABLE = True
except ImportError:
    DIALOGFLOW_AVAILABLE = False


# Default conversation scripts for testing (Portuguese)
DEFAULT_CONVERSATION_SCRIPTS = [
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


@dataclass
class ConversationMetrics:
    """Metrics from a conversation load test"""
    total_sessions: int
    total_interactions: int
    successful_interactions: int
    failed_interactions: int
    total_cost_usd: float
    duration_seconds: float
    conversations_per_second: float


class DialogflowCXManager:
    """
    Dialogflow CX Session Manager

    Pricing:
    - Text session: ~$0.007 per request
    - Audio session: ~$0.06 per minute
    """

    TEXT_SESSION_COST = 0.007  # USD per text interaction

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        agent_id: Optional[str] = None
    ):
        """
        Initialize DialogflowCXManager

        Args:
            project_id: GCP project ID (auto-detected if None)
            location: Dialogflow location (default: us-central1)
            agent_id: Dialogflow CX agent ID
        """
        if not DIALOGFLOW_AVAILABLE:
            raise ImportError("google-cloud-dialogflow-cx is required for DialogflowCXManager")

        if project_id is None:
            _, project_id = default()

        self.project_id = project_id
        self.location = location
        self.agent_id = agent_id or os.getenv("DIALOGFLOW_AGENT_ID")

        if not self.agent_id:
            raise ValueError(
                "agent_id must be provided or set via DIALOGFLOW_AGENT_ID env var"
            )

        # Metrics
        self.total_sessions = 0
        self.total_interactions = 0
        self.successful_interactions = 0
        self.failed_interactions = 0
        self.total_cost_usd = 0.0
        self.start_time = None

        # Setup client
        client_options = None
        if location != "global":
            api_endpoint = f"{location}-dialogflow.googleapis.com:443"
            client_options = {"api_endpoint": api_endpoint}

        self.client = dialogflow.SessionsClient(client_options=client_options)

    def create_session(self) -> str:
        """
        Create a new session path

        Returns:
            Session path string
        """
        session_id = str(uuid.uuid4())
        return self.client.session_path(
            project=self.project_id,
            location=self.location,
            agent=self.agent_id,
            session=session_id,
        )

    def detect_intent(
        self,
        session_path: str,
        text: str,
        language_code: str = "pt-BR"
    ) -> dialogflow.DetectIntentResponse:
        """
        Send a text message and get response

        Args:
            session_path: Session path from create_session()
            text: User message
            language_code: Language code (default: pt-BR)

        Returns:
            DetectIntentResponse

        Raises:
            RuntimeError: If request fails
        """
        try:
            text_input = dialogflow.TextInput(text=text)
            query_input = dialogflow.QueryInput(
                text=text_input,
                language_code=language_code
            )

            request = dialogflow.DetectIntentRequest(
                session=session_path,
                query_input=query_input
            )

            response = self.client.detect_intent(request=request)
            return response

        except Exception as e:
            raise RuntimeError(f"Detect intent failed: {e}")

    def simulate_conversation(
        self,
        conversation_script: List[str],
        user_id: int,
        language_code: str = "pt-BR"
    ) -> Dict[str, Any]:
        """
        Simulate a complete user conversation

        Args:
            conversation_script: List of messages to send
            user_id: User identifier for tracking
            language_code: Language code

        Returns:
            Dict with conversation results
        """
        session_path = self.create_session()
        session_id = session_path.split('/')[-1]

        results = []

        for message in conversation_script:
            try:
                response = self.detect_intent(session_path, message, language_code)

                # Parse response
                response_texts = []
                for msg in response.query_result.response_messages:
                    if msg.text and msg.text.text:
                        response_texts.extend(msg.text.text)

                self.successful_interactions += 1
                self.total_cost_usd += self.TEXT_SESSION_COST

                results.append({
                    'status': 'success',
                    'user_input': message,
                    'agent_response': ' '.join(response_texts)[:100],
                    'intent': (
                        response.query_result.match.intent.display_name
                        if response.query_result.match.intent
                        else "N/A"
                    ),
                    'cost_usd': self.TEXT_SESSION_COST
                })

            except Exception as e:
                self.failed_interactions += 1
                results.append({
                    'status': 'failed',
                    'user_input': message,
                    'error': str(e)
                })

        self.total_sessions += 1
        self.total_interactions += len(conversation_script)

        return {
            'session_id': session_id[:8],
            'user_id': user_id,
            'results': results
        }

    def run_load_test(
        self,
        num_conversations: int,
        max_workers: int = 5,
        conversation_scripts: Optional[List[List[str]]] = None,
        auto_confirm: bool = False
    ) -> ConversationMetrics:
        """
        Run load test simulating multiple conversations

        Args:
            num_conversations: Number of conversations to simulate
            max_workers: Parallel workers (be careful with rate limits!)
            conversation_scripts: Custom conversation scripts (uses defaults if None)
            auto_confirm: Skip confirmation prompt

        Returns:
            ConversationMetrics with results
        """
        scripts = conversation_scripts or DEFAULT_CONVERSATION_SCRIPTS

        print("="*60)
        print("🔥 PHANTOM - Dialogflow CX Load Test")
        print("="*60)
        print(f"\n📊 Configuration:")
        print(f"   Project: {self.project_id}")
        print(f"   Location: {self.location}")
        print(f"   Agent: {self.agent_id}")
        print(f"   Conversations: {num_conversations}")
        print(f"   Workers: {max_workers}")

        # Cost estimate
        avg_messages = sum(len(s) for s in scripts) / len(scripts)
        estimated_interactions = int(num_conversations * avg_messages)
        estimated_cost = estimated_interactions * self.TEXT_SESSION_COST

        print(f"\n💰 Estimate:")
        print(f"   Interactions: ~{estimated_interactions}")
        print(f"   Cost: ~${estimated_cost:.2f} USD")

        # Confirmation
        if not auto_confirm and os.getenv("AUTO_CONFIRM") != "true":
            response = input("\n🚀 Continue? (y/n): ").strip().lower()
            if response != 'y':
                print("❌ Cancelled")
                return ConversationMetrics(
                    total_sessions=0,
                    total_interactions=0,
                    successful_interactions=0,
                    failed_interactions=0,
                    total_cost_usd=0.0,
                    duration_seconds=0.0,
                    conversations_per_second=0.0
                )

        self.start_time = time.time()

        # Prepare conversations
        conversations_to_run = []
        for i in range(num_conversations):
            script = scripts[i % len(scripts)]
            conversations_to_run.append((i, script))

        print(f"\n⏳ Simulating {num_conversations} conversations...")
        print("=" * 60)

        # Execute in parallel
        all_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.simulate_conversation, script, user_id): user_id
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
                          f"Sessions: {self.total_sessions} | "
                          f"Interactions: {self.successful_interactions} | "
                          f"CPS: {cps:.2f} | "
                          f"Cost: ${self.total_cost_usd:.4f}")

        duration = time.time() - self.start_time
        cps = self.total_sessions / duration if duration > 0 else 0

        # Final report
        print("\n" + "="*60)
        print("📊 FINAL RESULTS")
        print("="*60)
        print(f"\n⏱️  Duration: {duration:.2f}s")
        print(f"✅ Successful sessions: {self.total_sessions}")
        print(f"💬 Total interactions: {self.total_interactions}")
        print(f"✅ Successful: {self.successful_interactions}")
        print(f"❌ Failed: {self.failed_interactions}")
        print(f"📈 Conversations/sec: {cps:.2f}")
        print(f"💰 Total cost: ${self.total_cost_usd:.4f} USD")

        if self.failed_interactions > 0:
            print(f"\n⚠️  {self.failed_interactions} interactions failed")

        print("\n✅ Load test complete!")

        return ConversationMetrics(
            total_sessions=self.total_sessions,
            total_interactions=self.total_interactions,
            successful_interactions=self.successful_interactions,
            failed_interactions=self.failed_interactions,
            total_cost_usd=self.total_cost_usd,
            duration_seconds=duration,
            conversations_per_second=cps
        )


def main():
    """CLI entry point for Dialogflow CX testing"""
    print("="*60)
    print("🗣️  PHANTOM - Dialogflow CX Manager")
    print("="*60)

    agent_id = os.getenv("DIALOGFLOW_AGENT_ID")
    location = os.getenv("DIALOGFLOW_LOCATION", "us-central1")

    if not agent_id:
        print("\n❌ DIALOGFLOW_AGENT_ID not configured!")
        print("\n🔧 FIX:")
        print("1. Create agent at: https://dialogflow.cloud.google.com/cx/")
        print("2. Copy the agent ID (UUID format)")
        print("3. Export: export DIALOGFLOW_AGENT_ID='your-agent-id-here'")
        sys.exit(1)

    print(f"\n🎯 Configuration:")
    print(f"   Agent ID: {agent_id}")
    print(f"   Location: {location}")

    try:
        manager = DialogflowCXManager(location=location, agent_id=agent_id)

        num_conversations = int(os.getenv("NUM_CONVERSATIONS", "10"))
        max_workers = int(os.getenv("MAX_WORKERS", "5"))

        metrics = manager.run_load_test(
            num_conversations=num_conversations,
            max_workers=max_workers
        )

        print("\n🎉 Test complete!")
        print(f"Total cost: ${metrics.total_cost_usd:.4f}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Agent created and ID correct?")
        print("2. API dialogflow.googleapis.com enabled?")
        print("3. Permissions correct (roles/dialogflow.admin)?")
        sys.exit(1)


if __name__ == "__main__":
    main()
