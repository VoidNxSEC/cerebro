"""
Azure OpenAI Provider Implementation
"""

import os
import time
from typing import Any

from cerebro.interfaces.llm import LLMProvider

try:
    from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
except ImportError:
    AzureChatOpenAI = None
    AzureOpenAIEmbeddings = None


class AzureOpenAIProvider(LLMProvider):
    """
    LLMProvider implementation for Azure OpenAI Service.
    """

    def __init__(
        self,
        chat_deployment: str | None = None,
        embed_deployment: str | None = None,
    ):
        """
        Initialize the Azure OpenAI provider.
        Assumes standard ENV variables are set for Azure authentication:
        - AZURE_OPENAI_API_KEY
        - AZURE_OPENAI_ENDPOINT
        - OPENAI_API_VERSION
        """
        if AzureChatOpenAI is None:
            raise ImportError(
                "langchain-openai is not installed. Please install the `azure` optional group."
            )

        self.chat_deployment = chat_deployment or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
        self.embed_deployment = embed_deployment or os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-ada-002")

        self.chat_model = AzureChatOpenAI(
            azure_deployment=self.chat_deployment,
            temperature=0.0,
        )
        self.embed_model = AzureOpenAIEmbeddings(
            azure_deployment=self.embed_deployment,
        )

    def embed(self, text: str) -> list[float]:
        return self.embed_model.embed_query(text)

    def embed_batch(self, texts: list[str], batch_size: int = 20) -> list[list[float]]:
        # AzureOpenAIEmbeddings handles batching natively under the hood
        return self.embed_model.embed_documents(texts)

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.chat_model.invoke(prompt)
        return str(response.content)

    def grounded_generate(
        self, query: str, context: list[str], top_k: int = 5, **kwargs
    ) -> dict[str, Any]:
        """
        Grounded generation using context retrieved from vector store.
        """
        if not context:
            return {
                "answer": self.generate(query),
                "citations": [],
                "confidence": 0.0,
                "cost_estimate": 0.0,
                "snippets": [],
            }

        context_str = "\n\n".join(f"Snippet [{i+1}]: {c}" for i, c in enumerate(context[:top_k]))
        
        prompt = (
            f"You are a highly precise enterprise technical assistant.\n"
            f"Use the following pieces of retrieved context to answer the question.\n"
            f"If the answer is not in the context, explicitly say that you don't know.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )

        answer = self.generate(prompt)

        return {
            "answer": answer,
            "citations": [f"Snippet [{i+1}]" for i in range(min(len(context), top_k))],
            "confidence": 0.9,  # Mocked
            "cost_estimate": 0.01,  # Mocked
            "snippets": context[:top_k],
        }

    def health_check(self) -> bool:
        """
        Check if the Azure OpenAI endpoint is accessible.
        """
        try:
            self.generate("Ping")
            return True
        except Exception as e:
            print(f"Azure OpenAI health check failed: {e}")
            return False
