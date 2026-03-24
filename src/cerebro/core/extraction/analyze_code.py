# src/cerebro/core/extraction/analyze_code.py
"""
PHANTOM Deep Intelligence Engine
- Advanced AST Analysis
- Dependency Mapping
- Security & Performance Heuristics
"""

import ast
import fnmatch
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    from tree_sitter_languages import get_language, get_parser
    TREESITTER_AVAILABLE = True
except ImportError:
    TREESITTER_AVAILABLE = False


@dataclass
class RepoMetrics:
    name: str
    loc: int = 0
    functions: int = 0
    classes: int = 0
    dependencies: List[str] = field(default_factory=list)
    complexity_score: int = 0
    security_hints: List[str] = field(default_factory=list)
    performance_hints: List[str] = field(default_factory=list)
    task_context: Optional[str] = None
    hook_results: Dict[str, str] = field(default_factory=dict)


def validate_repository_path(repo_path: Path):
    """Validate that the path exists and is a directory."""
    if not repo_path.exists():
        raise ValueError(f"Repository path does not exist: {repo_path}")
    if not repo_path.is_dir():
        raise ValueError(f"Repository path is not a directory: {repo_path}")


@dataclass
class CodeArtifact:
    repo: str
    file_path: str
    artifact_type: str
    name: str
    content: str
    context: str
    dependencies: List[str]
    documentation: str
    metadata: Dict


class HermeticAnalyzer:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.parsers = {}
        if TREESITTER_AVAILABLE:
            for lang in ["python", "nix", "rust", "bash", "typescript", "javascript"]:
                try:
                    self.parsers[lang] = get_parser(lang)
                except Exception:
                    pass

    def run_hooks(
        self, stage: str, hooks_config: List[Dict], repo_path: Path
    ) -> Dict[str, str]:
        """
        Execute hooks with enhanced metadata support.

        Supported hook metadata:
        - description: Human-readable description of the hook
        - command: Shell command to execute
        - allow_failure: Continue execution if hook fails (default: False)
        - timeout: Command timeout in seconds (default: 120)
        - retry: Retry on failure (default: False)
        """
        results = {}
        if not hooks_config:
            return results

        print(f"🪝  Running {stage} hooks...")
        for hook in hooks_config:
            cmd = hook.get("command")
            desc = hook.get("description", cmd)
            allow_fail = hook.get("allow_failure", False)
            timeout = hook.get("timeout", 120)
            retry_on_fail = hook.get("retry", False)

            if not cmd:
                continue

            print(f"   ▶ {desc}")
            attempts = 2 if retry_on_fail else 1
            last_error = None

            for attempt in range(attempts):
                try:
                    if attempt > 0:
                        print(f"   🔄 Retry attempt {attempt + 1}/{attempts}")

                    # Run in the repo directory with timeout
                    res = subprocess.run(
                        cmd,
                        shell=True,
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )

                    if res.returncode == 0:
                        status = "✅"
                        results[desc] = f"{status} (Exit: {res.returncode})"
                        print(f"   ✅ Success")
                        break
                    else:
                        status = "❌"
                        last_error = res.stderr.strip()

                        if not retry_on_fail or attempt == attempts - 1:
                            results[desc] = f"{status} (Exit: {res.returncode})"
                            if not allow_fail:
                                print(f"   ❌ Failed: {last_error}")
                            else:
                                print(f"   ⚠️  Failed (allowed): {last_error}")
                            break

                except subprocess.TimeoutExpired:
                    results[desc] = f"❌ Timeout after {timeout}s"
                    print(f"   ⏱️  Timeout after {timeout}s")
                    if not retry_on_fail or attempt == attempts - 1:
                        break
                except Exception as e:
                    results[desc] = f"❌ Error: {str(e)}"
                    print(f"   ❌ Exception: {e}")
                    if not retry_on_fail or attempt == attempts - 1:
                        break

        return results

    def detect_language(self, file_path: Path) -> Optional[str]:
        mapping = {
            ".py": "python",
            ".nix": "nix",
            ".rs": "rust",
            ".sh": "bash",
            ".ts": "typescript",
            ".js": "javascript",
        }
        return mapping.get(file_path.suffix.lower())

    def analyze_repo(self, repo_path: Path, hooks: Optional[Dict] = None) -> Dict:
        """Perform deep analysis of a complete repository."""
        artifacts = []
        metrics = RepoMetrics(
            name=repo_path.name,
        )

        # 0. Run Pre-Analyze Hooks
        if hooks and "pre_analyze" in hooks:
            pre_results = self.run_hooks("pre_analyze", hooks["pre_analyze"], repo_path)
            metrics.hook_results.update(pre_results)

        # 1. Analyze Dependencies (Filesystem Scan)
        metrics.dependencies = self.extract_external_deps(repo_path)

        # Global excludes
        excludes = self.config.get("global", {}).get("exclude", [])
        # Always exclude .git and common ignores
        excludes.extend(
            [
                ".git",
                ".venv",
                "__pycache__",
                "node_modules",
                ".pytest_cache",
                ".nix-pip",
            ]
        )

        # 2. Analyze Code
        print(f"🔍 Scanning: {repo_path}")
        for file_path in repo_path.rglob("*"):
            # Check exclusions
            if any(
                fnmatch.fnmatch(part, pat)
                for part in file_path.parts
                for pat in excludes
            ):
                # print(f"Skipped (exclude): {file_path}")
                continue

            if file_path.is_file():
                if any(part.startswith(".") for part in file_path.parts):
                    # print(f"Skipped (hidden): {file_path}")
                    continue

                lang = self.detect_language(file_path)
                if not lang:
                    continue

                # print(f"Analyzing: {file_path} ({lang})")
                content = file_path.read_text(errors="ignore")
                metrics.loc += len(content.splitlines())

                # Python uses AST, no need for TreeSitter
                if lang == "python" or lang in self.parsers:
                    file_artifacts = self.analyze_file(file_path, lang, content)
                    artifacts.extend(file_artifacts)

                    # Update count metrics
                    metrics.functions += sum(
                        1 for a in file_artifacts if a.artifact_type == "function"
                    )
                    metrics.classes += sum(
                        1 for a in file_artifacts if a.artifact_type == "class"
                    )

                    # Security and Performance Heuristics
                    self.check_heuristics(content, metrics)

        # 3. Run Post-Analyze Hooks
        if hooks and "post_analyze" in hooks:
            post_results = self.run_hooks(
                "post_analyze", hooks["post_analyze"], repo_path
            )
            metrics.hook_results.update(post_results)

        return {"artifacts": artifacts, "metrics": asdict(metrics)}

    def extract_external_deps(self, repo_path: Path) -> List[str]:
        deps = []
        dep_files = {
            "requirements.txt": r"^([a-zA-Z0-9\-_]+)",
            "pyproject.toml": r'([a-zA-Z0-9\-_]+)\s*=\s*["\'{]',
            "package.json": r'"([a-zA-Z0-9\-_@\/]+)"\s*:',
            "Cargo.toml": r"^([a-zA-Z0-9\-_]+)\s*=",
        }
        for file_name, pattern in dep_files.items():
            f_path = repo_path / file_name
            if f_path.exists():
                content = f_path.read_text(errors="ignore")
                found = re.findall(pattern, content, re.MULTILINE)
                deps.extend(found)
        return list(set(deps))

    def check_heuristics(self, content: str, metrics: RepoMetrics):
        # Security
        sec_patterns = {
            "hardcoded_key": r'(?i)(key|secret|password|token)\s*=\s*["\"][a-zA-Z0-9]{10,}',
            "unsafe_exec": r"(os\.system|subprocess\.run|eval|exec)\(",
        }
        for key, p in sec_patterns.items():
            if re.search(p, content):
                metrics.security_hints.append(key)

        # Performance
        perf_patterns = {
            "no_cache": r"(?i)(cache=False|no-cache)",
            "heavy_loop": r"for .* in range\(len\(.*\)\)",
        }
        for key, p in perf_patterns.items():
            if re.search(p, content):
                metrics.performance_hints.append(key)

    def analyze_file(
        self, file_path: Path, lang: str, content: str
    ) -> List[CodeArtifact]:
        artifacts = []
        if lang == "python":
            try:
                ast_tree = ast.parse(content)
                for node in ast.walk(ast_tree):
                    if isinstance(
                        node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    ):
                        a_type = (
                            "function"
                            if not isinstance(node, ast.ClassDef)
                            else "class"
                        )
                        artifacts.append(
                            CodeArtifact(
                                repo=repo_name(file_path),
                                file_path=str(file_path),
                                artifact_type=a_type,
                                name=node.name,
                                content=ast.get_source_segment(content, node) or "",
                                context="",
                                dependencies=[],
                                documentation=ast.get_docstring(node) or "",
                                metadata={"line": node.lineno},
                            )
                        )
            except:
                pass
        return artifacts


def repo_name(file_path: Path) -> str:
    for p in ["projects", "Projects", "low-level"]:
        if p in file_path.parts:
            idx = file_path.parts.index(p)
            return (
                file_path.parts[idx + 1] if len(file_path.parts) > idx + 1 else "root"
            )
    return file_path.parts[0] if file_path.parts else "unknown"
