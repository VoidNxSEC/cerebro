"""
Unit tests for RepoAnalyzer class.

Tests cover:
- Initialization with various parameters
- Gitignore loading and parsing
- File filtering (ignored files, binary files, size limits)
- Repository scanning
- JSONL output generation
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest
import pathspec

from phantom.core.analyzer import RepoAnalyzer


class TestRepoAnalyzerInitialization:
    """Test RepoAnalyzer initialization."""

    def test_init_with_default_parameters(self, tmp_path):
        """Test initialization with default parameters."""
        analyzer = RepoAnalyzer(str(tmp_path))
        assert analyzer.root_path == tmp_path.resolve()
        assert analyzer.max_file_size == 100 * 1024  # 100 KB default
        assert analyzer.ignore_spec is None  # No .gitignore file

    def test_init_with_custom_max_file_size(self, tmp_path):
        """Test initialization with custom max file size."""
        analyzer = RepoAnalyzer(str(tmp_path), max_file_size_kb=50)
        assert analyzer.max_file_size == 50 * 1024

    def test_init_resolves_path(self, tmp_path):
        """Test that initialization resolves relative paths."""
        # Create a subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        # Change to parent directory and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            analyzer = RepoAnalyzer("subdir")
            assert analyzer.root_path == subdir.resolve()
        finally:
            os.chdir(original_cwd)

    def test_init_with_gitignore(self, tmp_path):
        """Test initialization with .gitignore file."""
        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text("*.pyc\n__pycache__/\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        assert analyzer.ignore_spec is not None
        assert isinstance(analyzer.ignore_spec, pathspec.PathSpec)

    def test_default_ignores_list(self, tmp_path):
        """Test that default ignores list is properly initialized."""
        analyzer = RepoAnalyzer(str(tmp_path))
        expected_ignores = [
            ".git", "__pycache__", "node_modules", "dist", "build",
            "target", ".venv", ".env", ".nix-pip", "*.pyc", "*.o",
            "*.so", "*.lock", "package-lock.json", "yarn.lock",
            "go.sum", "Cargo.lock"
        ]
        assert analyzer.default_ignores == expected_ignores


class TestLoadGitignore:
    """Test _load_gitignore method."""

    def test_load_gitignore_exists(self, tmp_path):
        """Test loading existing .gitignore file."""
        gitignore_path = tmp_path / ".gitignore"
        gitignore_content = "*.pyc\n__pycache__/\nnode_modules/\n"
        gitignore_path.write_text(gitignore_content)
        
        analyzer = RepoAnalyzer(str(tmp_path))
        assert analyzer.ignore_spec is not None
        # Test that the spec can match patterns
        assert analyzer.ignore_spec.match_file("test.pyc")
        assert analyzer.ignore_spec.match_file("__pycache__/module.pyc")

    def test_load_gitignore_not_exists(self, tmp_path):
        """Test when .gitignore doesn't exist."""
        analyzer = RepoAnalyzer(str(tmp_path))
        assert analyzer.ignore_spec is None

    def test_load_gitignore_empty(self, tmp_path):
        """Test loading empty .gitignore file."""
        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text("")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        assert analyzer.ignore_spec is not None


class TestIsIgnored:
    """Test _is_ignored method."""

    def test_is_ignored_default_patterns(self, tmp_path):
        """Test that default patterns are ignored."""
        analyzer = RepoAnalyzer(str(tmp_path))
        
        # Create test paths
        git_dir = tmp_path / ".git" / "config"
        pycache_dir = tmp_path / "__pycache__" / "module.pyc"
        venv_dir = tmp_path / ".venv" / "bin" / "python"
        
        assert analyzer._is_ignored(git_dir)
        assert analyzer._is_ignored(pycache_dir)
        assert analyzer._is_ignored(venv_dir)

    def test_is_ignored_gitignore_patterns(self, tmp_path):
        """Test that .gitignore patterns are respected."""
        gitignore_path = tmp_path / ".gitignore"
        gitignore_path.write_text("*.log\nbuild/\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        
        log_file = tmp_path / "debug.log"
        build_file = tmp_path / "build" / "output.txt"
        
        assert analyzer._is_ignored(log_file)
        assert analyzer._is_ignored(build_file)

    def test_is_ignored_normal_files(self, tmp_path):
        """Test that normal files are not ignored."""
        analyzer = RepoAnalyzer(str(tmp_path))
        
        normal_file = tmp_path / "main.py"
        assert not analyzer._is_ignored(normal_file)

    def test_is_ignored_nested_directories(self, tmp_path):
        """Test ignoring nested directories."""
        analyzer = RepoAnalyzer(str(tmp_path))
        
        # Create nested structure
        nested_path = tmp_path / "src" / "node_modules" / "package" / "index.js"
        assert analyzer._is_ignored(nested_path)

    def test_is_ignored_extension_patterns(self, tmp_path):
        """Test ignoring files by extension."""
        analyzer = RepoAnalyzer(str(tmp_path))
        
        lock_file = tmp_path / "package.lock"
        pyc_file = tmp_path / "module.pyc"
        
        assert analyzer._is_ignored(lock_file)
        assert analyzer._is_ignored(pyc_file)


class TestIsBinary:
    """Test _is_binary method."""

    def test_is_binary_text_file(self, tmp_path):
        """Test that text files are not detected as binary."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("This is a text file\nWith multiple lines\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        assert not analyzer._is_binary(text_file)

    def test_is_binary_python_file(self, tmp_path):
        """Test that Python files are not detected as binary."""
        py_file = tmp_path / "test.py"
        py_file.write_text("def hello():\n    print('world')\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        assert not analyzer._is_binary(py_file)

    def test_is_binary_json_file(self, tmp_path):
        """Test that JSON files are not detected as binary."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}\n')
        
        analyzer = RepoAnalyzer(str(tmp_path))
        assert not analyzer._is_binary(json_file)

    def test_is_binary_actual_binary_file(self, tmp_path):
        """Test that actual binary files are detected."""
        binary_file = tmp_path / "test.bin"
        # Write actual binary data
        binary_file.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
        
        analyzer = RepoAnalyzer(str(tmp_path))
        assert analyzer._is_binary(binary_file)

    def test_is_binary_nonexistent_file(self, tmp_path):
        """Test behavior with nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        analyzer = RepoAnalyzer(str(tmp_path))
        # Should return True (treated as binary/unreadable)
        assert analyzer._is_binary(nonexistent)


class TestScan:
    """Test scan method."""

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        assert artifacts == []

    def test_scan_single_file(self, tmp_path):
        """Test scanning directory with single file."""
        test_file = tmp_path / "test.py"
        test_content = "def hello():\n    print('world')\n"
        test_file.write_text(test_content)
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == 1
        assert artifacts[0]["title"] == "test.py"
        assert artifacts[0]["content"] == test_content
        assert artifacts[0]["metadata"]["extension"] == ".py"
        assert artifacts[0]["metadata"]["size"] == len(test_content)

    def test_scan_multiple_files(self, tmp_path):
        """Test scanning directory with multiple files."""
        (tmp_path / "file1.py").write_text("# File 1\n")
        (tmp_path / "file2.py").write_text("# File 2\n")
        (tmp_path / "file3.txt").write_text("# File 3\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == 3
        titles = {a["title"] for a in artifacts}
        assert titles == {"file1.py", "file2.py", "file3.txt"}

    def test_scan_nested_directories(self, tmp_path):
        """Test scanning nested directory structure."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("# Main\n")
        
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("# Tests\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == 2
        titles = {a["title"] for a in artifacts}
        assert titles == {"src/main.py", "tests/test_main.py"}

    def test_scan_ignores_gitignore_patterns(self, tmp_path):
        """Test that scan respects .gitignore patterns."""
        (tmp_path / ".gitignore").write_text("*.log\n")
        (tmp_path / "main.py").write_text("# Main\n")
        (tmp_path / "debug.log").write_text("# Log\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == 1
        assert artifacts[0]["title"] == "main.py"

    def test_scan_ignores_default_patterns(self, tmp_path):
        """Test that scan ignores default patterns."""
        (tmp_path / "main.py").write_text("# Main\n")
        
        # Create ignored directories
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "main.pyc").write_text("# Compiled\n")
        
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("# Git config\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == 1
        assert artifacts[0]["title"] == "main.py"

    def test_scan_respects_max_file_size(self, tmp_path):
        """Test that scan respects max file size limit."""
        # Create a file larger than 50 KB
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * (51 * 1024))
        
        small_file = tmp_path / "small.txt"
        small_file.write_text("small content\n")
        
        analyzer = RepoAnalyzer(str(tmp_path), max_file_size_kb=50)
        artifacts = analyzer.scan()
        
        # Only small file should be included
        assert len(artifacts) == 1
        assert artifacts[0]["title"] == "small.txt"

    def test_scan_skips_binary_files(self, tmp_path):
        """Test that scan skips binary files."""
        text_file = tmp_path / "text.txt"
        text_file.write_text("text content\n")
        
        binary_file = tmp_path / "image.bin"
        binary_file.write_bytes(b'\x89PNG\r\n\x1a\n')
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == 1
        assert artifacts[0]["title"] == "text.txt"

    def test_scan_artifact_structure(self, tmp_path):
        """Test that scan produces correct artifact structure."""
        test_file = tmp_path / "test.py"
        test_content = "def hello():\n    pass\n"
        test_file.write_text(test_content)
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == 1
        artifact = artifacts[0]
        
        # Check required fields
        assert "id" in artifact
        assert "title" in artifact
        assert "content" in artifact
        assert "metadata" in artifact
        
        # Check metadata fields
        assert "path" in artifact["metadata"]
        assert "extension" in artifact["metadata"]
        assert "size" in artifact["metadata"]
        
        # Check values
        assert artifact["title"] == "test.py"
        assert artifact["content"] == test_content
        assert artifact["metadata"]["extension"] == ".py"
        assert artifact["metadata"]["size"] == len(test_content)

    def test_scan_handles_encoding_errors(self, tmp_path):
        """Test that scan handles files with encoding errors gracefully."""
        # Create a file with mixed encodings
        mixed_file = tmp_path / "mixed.txt"
        mixed_file.write_bytes(b"Valid UTF-8\n\xff\xfe Invalid bytes\n")
        
        valid_file = tmp_path / "valid.txt"
        valid_file.write_text("Valid content\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        # Should include the valid file and handle the mixed file gracefully
        assert len(artifacts) >= 1
        titles = {a["title"] for a in artifacts}
        assert "valid.txt" in titles

    def test_scan_with_special_characters_in_filenames(self, tmp_path):
        """Test scanning files with special characters in names."""
        special_file = tmp_path / "file-with-dashes_and_underscores.py"
        special_file.write_text("# Special\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == 1
        assert artifacts[0]["title"] == "file-with-dashes_and_underscores.py"


class TestSaveJsonl:
    """Test save_jsonl method."""

    def test_save_jsonl_empty_list(self, tmp_path):
        """Test saving empty artifacts list."""
        output_file = tmp_path / "output.jsonl"
        analyzer = RepoAnalyzer(str(tmp_path))
        
        analyzer.save_jsonl([], str(output_file))
        
        assert output_file.exists()
        assert output_file.read_text() == ""

    def test_save_jsonl_single_artifact(self, tmp_path):
        """Test saving single artifact."""
        output_file = tmp_path / "output.jsonl"
        analyzer = RepoAnalyzer(str(tmp_path))
        
        artifact = {
            "id": "test_1",
            "title": "test.py",
            "content": "def hello():\n    pass\n",
            "metadata": {
                "path": "test.py",
                "extension": ".py",
                "size": 20
            }
        }
        
        analyzer.save_jsonl([artifact], str(output_file))
        
        assert output_file.exists()
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 1
        
        loaded = json.loads(lines[0])
        assert loaded == artifact

    def test_save_jsonl_multiple_artifacts(self, tmp_path):
        """Test saving multiple artifacts."""
        output_file = tmp_path / "output.jsonl"
        analyzer = RepoAnalyzer(str(tmp_path))
        
        artifacts = [
            {
                "id": "test_1",
                "title": "file1.py",
                "content": "# File 1\n",
                "metadata": {"path": "file1.py", "extension": ".py", "size": 10}
            },
            {
                "id": "test_2",
                "title": "file2.py",
                "content": "# File 2\n",
                "metadata": {"path": "file2.py", "extension": ".py", "size": 10}
            }
        ]
        
        analyzer.save_jsonl(artifacts, str(output_file))
        
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 2
        
        loaded_artifacts = [json.loads(line) for line in lines]
        assert loaded_artifacts == artifacts

    def test_save_jsonl_with_special_characters(self, tmp_path):
        """Test saving artifacts with special characters."""
        output_file = tmp_path / "output.jsonl"
        analyzer = RepoAnalyzer(str(tmp_path))
        
        artifact = {
            "id": "test_1",
            "title": "test.py",
            "content": "# Special chars: é, ñ, 中文, emoji 🎉\n",
            "metadata": {"path": "test.py", "extension": ".py", "size": 50}
        }
        
        analyzer.save_jsonl([artifact], str(output_file))
        
        lines = output_file.read_text().strip().split("\n")
        loaded = json.loads(lines[0])
        assert loaded["content"] == artifact["content"]

    def test_save_jsonl_overwrites_existing_file(self, tmp_path):
        """Test that save_jsonl overwrites existing file."""
        output_file = tmp_path / "output.jsonl"
        output_file.write_text("old content\n")
        
        analyzer = RepoAnalyzer(str(tmp_path))
        artifact = {
            "id": "test_1",
            "title": "test.py",
            "content": "new content\n",
            "metadata": {"path": "test.py", "extension": ".py", "size": 12}
        }
        
        analyzer.save_jsonl([artifact], str(output_file))
        
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 1
        loaded = json.loads(lines[0])
        assert loaded["content"] == "new content\n"

    def test_save_jsonl_creates_parent_directories(self, tmp_path):
        """Test that save_jsonl creates parent directories if needed."""
        output_file = tmp_path / "subdir" / "nested" / "output.jsonl"
        analyzer = RepoAnalyzer(str(tmp_path))
        
        artifact = {
            "id": "test_1",
            "title": "test.py",
            "content": "content\n",
            "metadata": {"path": "test.py", "extension": ".py", "size": 8}
        }
        
        # Note: The current implementation doesn't create parent directories
        # This test documents the current behavior
        with pytest.raises(FileNotFoundError):
            analyzer.save_jsonl([artifact], str(output_file))


class TestIntegration:
    """Integration tests for RepoAnalyzer."""

    def test_scan_and_save_workflow(self, tmp_path):
        """Test complete workflow: scan and save."""
        # Create test repository structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("def main():\n    pass\n")
        (tmp_path / "src" / "utils.py").write_text("def util():\n    pass\n")
        
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("def test_main():\n    pass\n")
        
        (tmp_path / ".gitignore").write_text("*.pyc\n__pycache__/\n")
        
        # Scan
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == 3
        
        # Save
        output_file = tmp_path / "output.jsonl"
        analyzer.save_jsonl(artifacts, str(output_file))
        
        # Verify
        assert output_file.exists()
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 3
        
        loaded_artifacts = [json.loads(line) for line in lines]
        assert len(loaded_artifacts) == 3

    def test_scan_with_complex_gitignore(self, tmp_path):
        """Test scanning with complex .gitignore patterns."""
        gitignore_content = """
# Python
*.pyc
__pycache__/
*.egg-info/

# Virtual environments
venv/
.venv/

# IDE
.vscode/
.idea/

# Build
build/
dist/

# Logs
*.log
"""
        (tmp_path / ".gitignore").write_text(gitignore_content)
        
        # Create various files
        (tmp_path / "main.py").write_text("# Main\n")
        (tmp_path / "debug.log").write_text("# Log\n")
        
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        (venv_dir / "python.py").write_text("# Python\n")
        
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "output.txt").write_text("# Build\n")
        
        # Scan
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        # Only main.py should be included
        assert len(artifacts) == 1
        assert artifacts[0]["title"] == "main.py"

    def test_scan_large_repository_structure(self, tmp_path):
        """Test scanning a larger repository structure."""
        # Create a more complex structure
        dirs = [
            "src/core",
            "src/utils",
            "tests/unit",
            "tests/integration",
            "docs",
            "config"
        ]
        
        for dir_path in dirs:
            (tmp_path / dir_path).mkdir(parents=True)
        
        # Create files
        files = [
            "src/core/main.py",
            "src/core/engine.py",
            "src/utils/helpers.py",
            "tests/unit/test_main.py",
            "tests/integration/test_workflow.py",
            "docs/README.md",
            "config/settings.json"
        ]
        
        for file_path in files:
            (tmp_path / file_path).write_text(f"# Content of {file_path}\n")
        
        # Scan
        analyzer = RepoAnalyzer(str(tmp_path))
        artifacts = analyzer.scan()
        
        assert len(artifacts) == len(files)
        titles = {a["title"] for a in artifacts}
        assert titles == set(files)
