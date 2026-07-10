# Contributing to Cerebro

Welcome to the Cerebro project! This document outlines the development workflow, architecture, and contribution guidelines.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Development Setup](#development-setup)
4. [Code Organization](#code-organization)
5. [Adding New Providers](#adding-new-providers)
6. [Testing](#testing)
7. [Code Quality](#code-quality)
8. [Commit Guidelines](#commit-guidelines)

## Project Overview

**Cerebro** (formerly Phantom) is a Knowledge Extraction and RAG (Retrieval Augmented Generation) platform that:
- Extracts and analyzes code semantically
- Builds a vector store for knowledge retrieval
- Provides enterprise-grade data platform capabilities
- Supports both local MVP and cloud-native deployments

## Architecture

### Modular Provider Pattern

Cerebro uses a **pluggable provider architecture** to decouple business logic from specific implementations:

```
┌─────────────────────────────────────────────────────────┐
│                   RigorousRAGEngine                      │
│              (Core RAG Logic - Provider Agnostic)        │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────────┐  ┌──────────────────────┐
│  LLMProvider     │  │ VectorStoreProvider  │
│  (Interface)     │  │ (Interface)          │
└────────┬─────────┘  └──────────┬───────────┘
         │                       │
    ┌────┴────┐            ┌─────┴──────┐
    │          │            │            │
    ▼          ▼            ▼            ▼
┌────────┐ ┌────────┐  ┌────────┐  ┌────────┐
│Vertex  │ │Claude  │  │Chroma  │  │Pinecone│
│  AI    │ │  API   │  │  DB    │  │        │
└────────┘ └────────┘  └────────┘  └────────┘
```

### Module Structure

```
src/phantom/
├── interfaces/              # Abstract base classes
│   ├── llm.py              # LLMProvider interface
│   └── vector_store.py     # VectorStoreProvider interface
├── providers/              # Concrete implementations
│   ├── gcp/
│   │   └── vertex_ai_llm.py
│   ├── chroma/
│   │   └── chroma_vector_store.py
│   └── (future providers)
├── core/                   # Core business logic
│   ├── rag/
│   │   └── engine.py       # RigorousRAGEngine (uses providers)
│   ├── extraction/
│   └── gcp/
├── cli.py                  # CLI interface
└── __init__.py
```

## Development Setup

### Prerequisites

- Python 3.13+
- Poetry (dependency management)
- NixOS (optional, for reproducible builds)

### Installation

```bash
# Clone the repository
git clone https://gitlab.com/voidnx/cerebro.git
cd cerebro

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Google Cloud
export GCP_PROJECT_ID="your-project-id"
export DATA_STORE_ID="your-data-store-id"

# Optional: For local development
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Code Organization

### Interfaces (Abstract Base Classes)

All providers must implement one of the core interfaces:

#### LLMProvider Interface

```python
from phantom.interfaces.llm import LLMProvider

class MyLLMProvider(LLMProvider):
    def embed(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        pass
    
    def embed_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """Generate embeddings for multiple texts with batching."""
        pass
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    def grounded_generate(self, query: str, context: List[str], top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """Generate text grounded in context with citations."""
        pass
    
    def health_check(self) -> bool:
        """Check provider health."""
        pass
```

#### VectorStoreProvider Interface

```python
from phantom.interfaces.vector_store import VectorStoreProvider

class MyVectorStoreProvider(VectorStoreProvider):
    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]], **kwargs) -> int:
        """Add documents with embeddings."""
        pass
    
    def search(self, query_embedding: List[float], top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        pass
    
    def delete_documents(self, document_ids: List[str]) -> int:
        """Delete documents."""
        pass
    
    def clear(self) -> None:
        """Clear all documents."""
        pass
    
    def get_document_count(self) -> int:
        """Get document count."""
        pass
    
    def health_check(self) -> bool:
        """Check provider health."""
        pass
```

## Adding New Providers

### Example: Adding an OpenAI LLM Provider

1. **Create the provider file:**

```bash
mkdir -p src/phantom/providers/openai
touch src/phantom/providers/openai/__init__.py
touch src/phantom/providers/openai/openai_llm.py
```

2. **Implement the LLMProvider interface:**

```python
# src/phantom/providers/openai/openai_llm.py
from phantom.interfaces.llm import LLMProvider
import openai

class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key
    
    def embed(self, text: str) -> List[float]:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response['data'][0]['embedding']
    
    def embed_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            response = openai.Embedding.create(
                input=batch,
                model="text-embedding-3-small"
            )
            embeddings.extend([item['embedding'] for item in response['data']])
        return embeddings
    
    def generate(self, prompt: str, **kwargs) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response['choices'][0]['message']['content']
    
    def grounded_generate(self, query: str, context: List[str], top_k: int = 5, **kwargs) -> Dict[str, Any]:
        context_text = "\n".join(context[:top_k])
        prompt = f"Based on the following context:\n{context_text}\n\nAnswer: {query}"
        answer = self.generate(prompt, **kwargs)
        return {
            "answer": answer,
            "citations": [],
            "confidence": 0.8,
            "cost_estimate": 0.01,
        }
    
    def health_check(self) -> bool:
        try:
            openai.Model.list()
            return True
        except:
            return False
```

3. **Update the provider's __init__.py:**

```python
# src/phantom/providers/openai/__init__.py
from .openai_llm import OpenAILLMProvider

__all__ = ["OpenAILLMProvider"]
```

4. **Use the new provider in your code:**

```python
from phantom.core.rag.engine import RigorousRAGEngine
from phantom.providers.openai import OpenAILLMProvider

llm = OpenAILLMProvider(api_key="sk-...")
engine = RigorousRAGEngine(llm_provider=llm)
```

## Testing

### Running Tests Locally

Before pushing, always run tests locally to catch issues early:

```bash
# Run all tests
just test

# Run unit tests only
just test-unit

# Run integration tests
just test-integration

# Run Vertex AI limit tests
just test-vertex-limits

# Run full CI pipeline locally (simulates GitLab CI)
just ci-local

# Run individual CI checks
just validate-imports
just validate-syntax
just lint
just format
```

### CI/CD Pipeline

The project uses **GitLab CI/CD** for automated testing on every push and merge request:

1. **Validate Stage:** Quick import and syntax checks
2. **Test Stage:** Unit tests, integration tests, linting, formatting
3. **Build Stage:** Docker image creation (manual trigger)
4. **Deploy Stage:** Cloud Run deployment (manual trigger)
5. **Monitor Stage:** Health checks and reporting

See [docs/GITLAB_CI_CD.md](../docs/GITLAB_CI_CD.md) for detailed pipeline documentation.

### Writing Tests

Tests should follow these patterns:

**Unit Tests** (mock all external dependencies):

```python
from unittest.mock import MagicMock, patch
from phantom.core.rag.engine import RigorousRAGEngine
from phantom.interfaces.llm import LLMProvider

def test_rag_engine_with_mocked_providers():
    mock_llm = MagicMock(spec=LLMProvider)
    mock_llm.grounded_generate.return_value = {
        "answer": "Test answer",
        "citations": [],
        "confidence": 0.9,
        "cost_estimate": 0.004,
    }
    
    engine = RigorousRAGEngine(llm_provider=mock_llm)
    result = engine.query_with_metrics("test query")
    
    assert "Test answer" in result["answer"]
```

**Integration Tests** (use real or semi-real components):

```python
@pytest.mark.integration
def test_vertex_ai_embeddings():
    from phantom.providers.gcp.vertex_ai_llm import VertexAILLMProvider
    
    provider = VertexAILLMProvider(project_id="test-project")
    embeddings = provider.embed_batch(["hello", "world"])
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 768  # Embedding dimension
```

## Code Quality

### Linting

```bash
# Check code style
just lint

# Fix code style issues
just lint-fix

# Format code
just format

# Run all quality checks
just quality
```

### Code Standards

- **Style Guide:** PEP 8 (enforced by ruff)
- **Type Hints:** Required for all public functions
- **Docstrings:** Required for all classes and public methods
- **Test Coverage:** Aim for >80% coverage

### Pre-commit Hooks

(Optional) Set up pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build, dependencies, etc.

**Examples:**

```
feat(providers): add OpenAI LLM provider

- Implement LLMProvider interface for OpenAI API
- Add support for GPT-4 and embedding models
- Include rate limiting and error handling

Closes #123
```

```
fix(rag): handle empty vector store gracefully

- Return empty results instead of raising error
- Add logging for debugging

Fixes #456
```

## Troubleshooting

### Common Issues

**Issue:** `ImportError: No module named 'phantom'`

**Solution:** Ensure you're in the Poetry virtual environment:
```bash
poetry shell
```

**Issue:** `GCP authentication failed`

**Solution:** Set up credentials:
```bash
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS="~/.config/gcloud/application_default_credentials.json"
```

**Issue:** Tests fail with `ResourceExhausted` errors

**Solution:** This is expected for integration tests without proper GCP setup. Use unit tests with mocks for CI/CD.

## Resources

- [Project README](README.md)
- [Architecture Documentation](docs/ARCHITECTURE_DATA_FLOW.md)
- [TODO Plan](TODO_PLAN.md)
- [Next Steps](NEXT-STEPS.md)

## Questions?

Open an issue on GitLab or contact the maintainers.

---

**Happy Contributing! 🚀**
