"""Tests for the Cerebro CLI."""

import importlib.util
from unittest.mock import patch

from typer.testing import CliRunner

from cerebro.cli import app

runner = CliRunner()


def test_info_command():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "CEREBRO" in result.stdout
    assert "GCP Integration" in result.stdout


def test_info_reports_rag_runtime_when_local_runtime_is_available():
    original_find_spec = importlib.util.find_spec

    def fake_find_spec(module_name: str):
        if module_name in {"google.cloud", "tree_sitter"}:
            return None
        return original_find_spec(module_name)

    with patch("cerebro.cli._has_rag_runtime_support", return_value=True):
        with patch("cerebro.cli.importlib.util.find_spec", side_effect=fake_find_spec):
            result = runner.invoke(app, ["info"])

    assert result.exit_code == 0
    assert "RAG Runtime" in result.stdout
    assert "Installed" in result.stdout


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    from cerebro import __version__
    assert f"v{__version__}" in result.stdout


def test_version_output_format():
    """Version output should be a single line with 'Cerebro CLI vX.Y.Z'."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("Cerebro CLI v")


def test_help_lists_command_groups():
    """--help should list all registered command groups."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "knowledge" in result.stdout
    assert "ops" in result.stdout
    assert "rag" in result.stdout


def test_help_shows_info_and_version():
    """--help should mention info and version commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "info" in result.stdout
    assert "version" in result.stdout


def test_knowledge_help():
    """knowledge --help should show sub-commands."""
    result = runner.invoke(app, ["knowledge", "--help"])
    assert result.exit_code == 0
    assert "analyze" in result.stdout


def test_ops_help():
    """ops --help should show sub-commands."""
    result = runner.invoke(app, ["ops", "--help"])
    assert result.exit_code == 0
    assert "health" in result.stdout
    assert "status" in result.stdout


def test_rag_help():
    """rag --help should show sub-commands."""
    result = runner.invoke(app, ["rag", "--help"])
    assert result.exit_code == 0
    assert "backend" in result.stdout
    assert "backends" in result.stdout
    assert "ingest" in result.stdout
    assert "query" in result.stdout
    assert "status" in result.stdout


def test_rag_status_command():
    """rag status should print the current runtime status."""

    with patch(
        "cerebro.core.rag.engine.get_rag_runtime_status_snapshot",
        return_value={
            "healthy": True,
            "mode": "local",
            "backend": "chroma",
            "llm_provider": "llamacpp",
            "namespace": "prod",
            "collection_name": "cerebro_documents",
            "document_count": 42,
            "details": {"persist_directory": "./data/vector_db"},
            "error": None,
        },
    ):
        result = runner.invoke(app, ["rag", "status"])

    assert result.exit_code == 0
    assert "CEREBRO RAG Runtime" in result.stdout
    assert "chroma" in result.stdout
    assert "42" in result.stdout


def test_rag_init_command():
    """rag init should initialize the configured backend and print details."""

    with patch("cerebro.core.rag.engine.RigorousRAGEngine") as mock_engine_cls:
        mock_engine = mock_engine_cls.return_value
        mock_engine.vector_store_provider.backend_name = "pgvector"
        mock_engine.initialize_runtime.return_value = {
            "backend": "pgvector",
            "initialized": True,
            "table_name": "cerebro_documents",
        }
        result = runner.invoke(app, ["rag", "init"])

    assert result.exit_code == 0
    assert "Backend initialized: pgvector" in result.stdout
    assert "cerebro_documents" in result.stdout


def test_rag_smoke_command():
    """rag smoke should print the smoke validation summary."""

    with patch("cerebro.core.rag.engine.RigorousRAGEngine") as mock_engine_cls:
        mock_engine = mock_engine_cls.return_value
        mock_engine.run_smoke_test.return_value = {
            "healthy": True,
            "backend": "pgvector",
            "namespace": "__cerebro_smoke__",
            "write_check": True,
            "document_count": 42,
            "query_hits": 1,
            "steps": [
                {"name": "initialize", "ok": True, "detail": "backend=pgvector"},
                {"name": "query", "ok": True, "detail": "hits=1"},
            ],
            "error": None,
        }
        result = runner.invoke(app, ["rag", "smoke"])

    assert result.exit_code == 0
    assert "CEREBRO RAG Smoke Test" in result.stdout
    assert "pgvector" in result.stdout
    assert "hits=1" in result.stdout


def test_rag_migrate_command():
    """rag migrate should copy vectors from a source backend into the active backend."""

    with patch("cerebro.settings.get_settings") as mock_settings:
        mock_settings.return_value.vector_store_provider = "pgvector"
        with patch("cerebro.providers.vector_store_factory.build_vector_store_provider") as mock_builder:
            mock_source_provider = mock_builder.return_value
            mock_source_provider.backend_name = "chroma"
            with patch("cerebro.core.rag.engine.RigorousRAGEngine") as mock_engine_cls:
                mock_engine = mock_engine_cls.return_value
                mock_engine.migrate_documents.return_value = {
                    "source_backend": "chroma",
                    "destination_backend": "pgvector",
                    "source_namespace": None,
                    "destination_namespace": "prod",
                    "source_count": 10,
                    "migrated_count": 10,
                    "destination_count_before": 0,
                    "destination_count_after": 10,
                    "batch_size": 200,
                    "batches": 1,
                    "cleared_destination": False,
                }
                result = runner.invoke(app, ["rag", "migrate", "--from-provider", "chroma"])

    assert result.exit_code == 0
    assert "CEREBRO RAG Migration" in result.stdout
    assert "chroma" in result.stdout
    assert "pgvector" in result.stdout


def test_rag_backends_list_command():
    """rag backends list should show supported backends and aliases."""

    with patch("cerebro.settings.get_settings") as mock_settings:
        mock_settings.return_value.vector_store_provider = "pgvector"
        result = runner.invoke(app, ["rag", "backends", "list"])

    assert result.exit_code == 0
    assert "CEREBRO RAG Backends" in result.stdout
    assert "pgvector" in result.stdout
    assert "chroma" in result.stdout


def test_rag_backend_info_command():
    """rag backend info should proxy active backend status details."""

    with patch(
        "cerebro.core.rag.engine.get_rag_runtime_status_snapshot",
        return_value={
            "healthy": True,
            "mode": "local",
            "backend": "pgvector",
            "llm_provider": "llamacpp",
            "namespace": "prod",
            "collection_name": "cerebro_documents",
            "document_count": 42,
            "details": {"schema": "public", "table_name": "cerebro_documents"},
            "error": None,
        },
    ):
        result = runner.invoke(app, ["rag", "backend", "info"])

    assert result.exit_code == 0
    assert "CEREBRO RAG Runtime" in result.stdout
    assert "pgvector" in result.stdout


def test_rag_backend_health_command():
    """rag backend health should summarize backend health and exit zero when healthy."""

    with patch(
        "cerebro.core.rag.engine.get_rag_runtime_status_snapshot",
        return_value={
            "healthy": True,
            "mode": "local",
            "backend": "pgvector",
            "llm_provider": "llamacpp",
            "namespace": "prod",
            "collection_name": "cerebro_documents",
            "document_count": 42,
            "details": {},
            "error": None,
        },
    ):
        result = runner.invoke(app, ["rag", "backend", "health"])

    assert result.exit_code == 0
    assert "CEREBRO RAG Backend Health" in result.stdout
    assert "pgvector" in result.stdout


def test_rag_backend_init_command():
    """rag backend init should delegate to the active backend bootstrap path."""

    with patch("cerebro.core.rag.engine.RigorousRAGEngine") as mock_engine_cls:
        mock_engine = mock_engine_cls.return_value
        mock_engine.vector_store_provider.backend_name = "pgvector"
        mock_engine.initialize_runtime.return_value = {
            "backend": "pgvector",
            "initialized": True,
            "table_name": "cerebro_documents",
        }
        result = runner.invoke(app, ["rag", "backend", "init"])

    assert result.exit_code == 0
    assert "Backend initialized: pgvector" in result.stdout


def test_rag_backend_smoke_command():
    """rag backend smoke should expose the integrated smoke workflow."""

    with patch("cerebro.core.rag.engine.RigorousRAGEngine") as mock_engine_cls:
        mock_engine = mock_engine_cls.return_value
        mock_engine.run_smoke_test.return_value = {
            "healthy": True,
            "backend": "pgvector",
            "namespace": "__cerebro_smoke__",
            "write_check": True,
            "document_count": 42,
            "query_hits": 1,
            "steps": [
                {"name": "initialize", "ok": True, "detail": "backend=pgvector"},
                {"name": "query", "ok": True, "detail": "hits=1"},
            ],
            "error": None,
        }
        result = runner.invoke(app, ["rag", "backend", "smoke"])

    assert result.exit_code == 0
    assert "CEREBRO RAG Smoke Test" in result.stdout


def test_rag_backend_migrate_command():
    """rag backend migrate should proxy the migration workflow."""

    with patch("cerebro.settings.get_settings") as mock_settings:
        mock_settings.return_value.vector_store_provider = "pgvector"
        with patch("cerebro.providers.vector_store_factory.build_vector_store_provider") as mock_builder:
            mock_source_provider = mock_builder.return_value
            mock_source_provider.backend_name = "chroma"
            with patch("cerebro.core.rag.engine.RigorousRAGEngine") as mock_engine_cls:
                mock_engine = mock_engine_cls.return_value
                mock_engine.migrate_documents.return_value = {
                    "source_backend": "chroma",
                    "destination_backend": "pgvector",
                    "source_namespace": None,
                    "destination_namespace": "prod",
                    "source_count": 10,
                    "migrated_count": 10,
                    "destination_count_before": 0,
                    "destination_count_after": 10,
                    "batch_size": 200,
                    "batches": 1,
                    "cleared_destination": False,
                }
                result = runner.invoke(app, ["rag", "backend", "migrate", "--from-provider", "chroma"])

    assert result.exit_code == 0
    assert "CEREBRO RAG Migration" in result.stdout


def test_no_args_shows_help():
    """Running with no args should show help (no_args_is_help=True)."""
    result = runner.invoke(app, [])
    # Typer uses exit code 0 or 2 for help display
    assert result.exit_code in (0, 2)
    output = result.stdout + (result.stderr if hasattr(result, 'stderr') and result.stderr else "")
    assert "Usage" in output or "usage" in output.lower()


def test_invalid_command():
    """An unknown command should produce a non-zero exit code."""
    result = runner.invoke(app, ["nonexistent-command-xyz"])
    assert result.exit_code != 0
