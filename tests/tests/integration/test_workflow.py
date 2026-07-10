import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from phantom.core.extraction.analyze_code import HermeticAnalyzer, RepoMetrics
from phantom.core.rag.engine import RigorousRAGEngine
from phantom.interfaces.llm import LLMProvider
from phantom.interfaces.vector_store import VectorStoreProvider

@pytest.mark.integration
class TestPhantomWorkflow:
    """
    Integration tests for the full Phantom workflow:
    Analyze -> Ingest -> Query
    """

    @pytest.fixture(scope="class")
    def test_data_dir(self):
        base_dir = Path("./data/test_integration")
        base_dir.mkdir(parents=True, exist_ok=True)
        yield base_dir
        # Cleanup after tests
        if base_dir.exists():
            shutil.rmtree(base_dir)

    def test_1_analyze_repo(self, test_data_dir):
        """Test code analysis on a dummy file."""
        # Create a dummy python file
        repo_path = test_data_dir / "dummy_repo"
        repo_path.mkdir(exist_ok=True)
        (repo_path / "main.py").write_text("def hello():\n    print('world')")

        analyzer = HermeticAnalyzer()
        result = analyzer.analyze_repo(repo_path)
        
        assert len(result["artifacts"]) > 0
        assert result["artifacts"][0].name == "hello"
        
        # Save artifacts for ingestion
        import json
        jsonl_path = test_data_dir / "artifacts.jsonl"
        with open(jsonl_path, "w") as f:
            for a in result["artifacts"]:
                doc = {
                    "jsonData": json.dumps({
                        "title": a.name,
                        "content": a.content,
                        "repo": "dummy_repo",
                        "context": "test"
                    })
                }
                f.write(json.dumps(doc) + "\n")
        
        assert jsonl_path.exists()

    def test_2_ingest_artifacts(self, test_data_dir):
        """Test ingestion with mocked providers."""
        # Create mock providers
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.import_documents.return_value = "operation-123"
        
        mock_vector_store = MagicMock(spec=VectorStoreProvider)
        mock_vector_store.add_documents.return_value = 1
        
        # Mock GCS storage
        with patch("phantom.core.rag.engine.storage.Client") as mock_storage:
            mock_bucket = MagicMock()
            mock_storage.return_value.get_bucket.return_value = mock_bucket
            
            engine = RigorousRAGEngine(
                llm_provider=mock_llm,
                vector_store_provider=mock_vector_store,
                persist_directory=str(test_data_dir / "vector_db"),
                data_store_id="test-store"
            )
            engine.project_id = "test-project"
            
            jsonl_path = test_data_dir / "artifacts.jsonl"
            count = engine.ingest(str(jsonl_path))
            
            assert count > 0
            mock_llm.import_documents.assert_called_once()

    def test_3_query_rag(self, test_data_dir):
        """Test querying with mocked providers."""
        # Create mock providers
        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.grounded_generate.return_value = {
            "answer": "The hello function prints world.",
            "citations": ["repo/main.py"],
            "confidence": 0.95,
            "cost_estimate": 0.004,
        }
        
        mock_vector_store = MagicMock(spec=VectorStoreProvider)
        mock_vector_store.search.return_value = [
            {
                "id": "doc_1",
                "content": "def hello():\n    print('world')",
                "metadata": {"source": "repo/main.py"},
                "similarity": 0.95,
            }
        ]
        
        engine = RigorousRAGEngine(
            llm_provider=mock_llm,
            vector_store_provider=mock_vector_store,
            persist_directory=str(test_data_dir / "vector_db")
        )
        
        result = engine.query_with_metrics("What does hello do?")
        
        assert "hello" in result["answer"]
        assert result["metrics"]["avg_confidence"] == 0.95
        assert "100%" in result["metrics"]["hit_rate_k"]
