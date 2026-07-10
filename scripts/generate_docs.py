from __future__ import annotations

import ast
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class CommandParameter:
    name: str
    kind: str
    annotation: str
    default: str
    required: bool
    help_text: str
    cli_flags: list[str]


@dataclass
class CommandDoc:
    name: str
    group_path: list[str]
    command_slug: str
    func_name: str
    description: str
    params: list[CommandParameter]
    examples: list[str]
    source_line: int


class DocumentationGenerator:
    """Generate markdown command reference files from the Typer CLI source."""

    def __init__(self, format: str = "markdown"):
        if format != "markdown":
            raise ValueError(f"Unsupported documentation format: {format}")
        self.format = format

    def generate(self, project: str | Path = ".", output: str | Path = "docs/") -> dict[str, int | str]:
        project_path = Path(project).expanduser().resolve()
        cli_path = project_path / "src" / "cerebro" / "cli.py"

        if not cli_path.exists():
            raise FileNotFoundError(f"{cli_path} not found.")

        module = ast.parse(cli_path.read_text(encoding="utf-8"))
        commands = self._extract_commands(module)
        output_dir = Path(output).expanduser().resolve()
        commands_dir = output_dir / "commands"
        mermaid_dir = output_dir / "mermaid"
        visualization_dir = output_dir / "visualization"
        commands_dir.mkdir(parents=True, exist_ok=True)
        mermaid_dir.mkdir(parents=True, exist_ok=True)
        visualization_dir.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now().isoformat(timespec="seconds")

        index_content = self._render_index(commands, generated_at)

        for cmd in sorted(commands, key=lambda item: item.name):
            safe_filename = cmd.name.replace(" ", "_") + ".md"
            (commands_dir / safe_filename).write_text(
                self._render_command_markdown(cmd),
                encoding="utf-8",
            )

        (commands_dir / "README.md").write_text(index_content, encoding="utf-8")
        (commands_dir / "catalog.json").write_text(
            json.dumps(self._build_catalog(commands, generated_at), indent=2),
            encoding="utf-8",
        )
        (mermaid_dir / "command-topology.mmd").write_text(
            self._render_mermaid_topology(commands),
            encoding="utf-8",
        )
        (mermaid_dir / "command-groups.mmd").write_text(
            self._render_mermaid_groups(commands),
            encoding="utf-8",
        )
        (visualization_dir / "scene.json").write_text(
            json.dumps(self._build_scene_graph(commands, generated_at), indent=2),
            encoding="utf-8",
        )
        (visualization_dir / "manifest.json").write_text(
            json.dumps(self._build_visualization_manifest(commands, generated_at), indent=2),
            encoding="utf-8",
        )

        return {
            "pages": len(commands),
            "groups": len({tuple(cmd.group_path) for cmd in commands}),
            "mermaid_diagrams": 2,
            "visualization_assets": 2,
            "output_dir": str(commands_dir),
        }

    def _extract_commands(self, module: ast.Module) -> list[CommandDoc]:
        typer_paths = self._build_typer_paths(module)
        commands: list[CommandDoc] = []

        for node in module.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            for decorator in node.decorator_list:
                command_info = self._parse_command_decorator(decorator)
                if command_info is None:
                    continue

                group_var, command_name = command_info
                if group_var not in typer_paths:
                    continue

                command_path = ["cerebro", *typer_paths[group_var], command_name]
                full_name = " ".join(part for part in command_path if part)
                docstring = ast.get_docstring(node) or ""
                commands.append(
                    CommandDoc(
                        name=full_name,
                        group_path=list(typer_paths[group_var]),
                        command_slug=command_name,
                        func_name=node.name,
                        description=docstring.strip(),
                        params=self._extract_parameters(node),
                        examples=self._extract_examples(docstring, full_name),
                        source_line=node.lineno,
                    )
                )

        return commands

    def _build_typer_paths(self, module: ast.Module) -> dict[str, list[str]]:
        typer_names = {"app"}

        for node in module.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            if self._is_typer_constructor(node.value):
                typer_names.add(target.id)

        paths: dict[str, list[str]] = {"app": []}
        pending_edges: list[tuple[str, str, str]] = []

        for node in module.body:
            if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
                continue
            call = node.value
            if not self._is_add_typer_call(call):
                continue

            parent_name = call.func.value.id
            child_arg = call.args[0] if call.args else None
            if not isinstance(child_arg, ast.Name):
                continue
            child_name = child_arg.id
            if parent_name not in typer_names or child_name not in typer_names:
                continue

            mounted_name = self._kwarg_literal(call, "name") or child_name.replace("_app", "")
            pending_edges.append((parent_name, child_name, mounted_name))

        changed = True
        while changed:
            changed = False
            for parent_name, child_name, mounted_name in pending_edges:
                if parent_name in paths and child_name not in paths:
                    paths[child_name] = [*paths[parent_name], mounted_name]
                    changed = True

        for typer_name in typer_names:
            paths.setdefault(typer_name, [typer_name.replace("_app", "")] if typer_name != "app" else [])

        return paths

    def _extract_parameters(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[CommandParameter]:
        positional_args = [arg for arg in node.args.args if arg.arg != "self"]
        defaults = [None] * (len(positional_args) - len(node.args.defaults)) + list(node.args.defaults)

        params: list[CommandParameter] = []
        for arg, default_node in zip(positional_args, defaults):
            annotation = ast.unparse(arg.annotation) if arg.annotation is not None else "Any"
            parsed = self._parse_typer_parameter(default_node)

            params.append(
                CommandParameter(
                    name=arg.arg,
                    kind=parsed["kind"],
                    annotation=annotation,
                    default=parsed["default"],
                    required=parsed["required"],
                    help_text=parsed["help_text"],
                    cli_flags=parsed["cli_flags"],
                )
            )

        return params

    def _parse_typer_parameter(self, default_node: ast.AST | None) -> dict[str, object]:
        if default_node is None:
            return {
                "kind": "argument",
                "default": "Required",
                "required": True,
                "help_text": "",
                "cli_flags": [],
            }

        if isinstance(default_node, ast.Call) and self._is_typer_helper_call(default_node):
            helper_name = self._call_name(default_node.func)
            kind = "option" if helper_name.endswith("Option") else "argument"
            raw_default = self._literal_or_source(default_node.args[0]) if default_node.args else "Required"
            help_text = self._kwarg_literal(default_node, "help") or ""
            cli_flags = [
                self._literal_or_source(arg)
                for arg in default_node.args[1:]
                if isinstance(self._literal_or_source(arg), str)
            ]

            required = raw_default in {"...", "Ellipsis", "Required"}
            default = "Required" if required else str(raw_default)

            return {
                "kind": kind,
                "default": default,
                "required": required,
                "help_text": help_text,
                "cli_flags": [flag for flag in cli_flags if flag.startswith("-")],
            }

        return {
            "kind": "argument",
            "default": self._literal_or_source(default_node),
            "required": False,
            "help_text": "",
            "cli_flags": [],
        }

    def _parse_command_decorator(self, decorator: ast.AST) -> tuple[str, str] | None:
        if not isinstance(decorator, ast.Call):
            return None
        if not isinstance(decorator.func, ast.Attribute):
            return None
        if decorator.func.attr != "command":
            return None
        if not isinstance(decorator.func.value, ast.Name):
            return None

        group_var = decorator.func.value.id
        command_name = (
            self._literal_or_source(decorator.args[0])
            if decorator.args
            else self._kwarg_literal(decorator, "name")
        )
        if not isinstance(command_name, str):
            return None
        return group_var, command_name

    def _extract_examples(self, docstring: str, fallback_command: str) -> list[str]:
        lines = [line.rstrip() for line in docstring.splitlines()]
        examples: list[str] = []
        collecting = False

        for line in lines:
            stripped = line.strip()
            lowered = stripped.lower()
            if lowered in {"example:", "examples:"}:
                collecting = True
                continue
            if collecting:
                if not stripped:
                    if examples:
                        break
                    continue
                examples.append(stripped)

        if not examples:
            examples.append(fallback_command)

        return examples

    def _render_command_markdown(self, cmd: CommandDoc) -> str:
        syntax = self._render_syntax(cmd)
        markdown = f"""# Command: `{cmd.name}`

## 0. Metadata
| Field | Value |
|-------|-------|
| Group | `{' '.join(cmd.group_path) if cmd.group_path else 'root'}` |
| Command | `{cmd.command_slug}` |
| Function | `{cmd.func_name}` |
| Source | `src/cerebro/cli.py:{cmd.source_line}` |
| Syntax | `{syntax}` |

## 1. Description
{cmd.description or "No description provided."}

**Syntax:**
```bash
{syntax}
```

## 2. Parameters

| Name | Kind | Type | Required | Default | CLI | Description |
|------|------|------|----------|---------|-----|-------------|"""

        if cmd.params:
            for param in cmd.params:
                cli = ", ".join(param.cli_flags) if param.cli_flags else "-"
                markdown += (
                    f"\n| `{param.name}` | `{param.kind}` | `{param.annotation}` | "
                    f"`{'yes' if param.required else 'no'}` | `{param.default}` | "
                    f"`{cli}` | {param.help_text or '-'} |"
                )
        else:
            markdown += "\n| - | - | - | - | - | - | - |"

        markdown += """

## 3. Examples
```bash
"""
        markdown += "\n".join(cmd.examples)
        markdown += f"""
```

## 4. Output
* Format: Rich console output or JSON when the command supports it.
* Errors: failures are reported to stderr and usually return exit code 1.

## 5. Source
* Module: `src/cerebro/cli.py`
* Function: `{cmd.func_name}`
* Line: `{cmd.source_line}`

## 6. Tests
* Check `tests/test_cli.py` for CLI coverage.

---
*Generated automatically at {os.popen('date').read().strip()}*
"""
        return markdown

    def _render_index(self, commands: list[CommandDoc], generated_at: str) -> str:
        grouped: dict[tuple[str, ...], list[CommandDoc]] = defaultdict(list)
        for cmd in commands:
            grouped[tuple(cmd.group_path)].append(cmd)

        lines = [
            "# Cerebro CLI Command Reference",
            "",
            f"> Generated: {generated_at}",
            f"> Total commands: {len(commands)}",
            f"> Command groups: {len(grouped)}",
            "",
            "## Executive Summary",
            "",
            "| Group | Commands |",
            "|-------|----------|",
        ]

        for group_path, items in sorted(grouped.items(), key=lambda item: (item[0], len(item[1]))):
            label = "root" if not group_path else " ".join(group_path)
            lines.append(f"| `{label}` | {len(items)} |")

        lines.append("")

        for group_path, items in sorted(grouped.items(), key=lambda item: item[0]):
            heading = "Root Commands" if not group_path else f"Group: {' '.join(group_path)}"
            lines.extend([f"## {heading}", ""])
            for cmd in sorted(items, key=lambda item: item.name):
                safe_filename = cmd.name.replace(" ", "_") + ".md"
                desc_short = cmd.description.splitlines()[0] if cmd.description else ""
                lines.append(f"- [{cmd.name}]({safe_filename}) - {desc_short}")
            lines.append("")

        return "\n".join(lines)

    def _render_mermaid_topology(self, commands: list[CommandDoc]) -> str:
        lines = [
            "---",
            "title: Cerebro CLI Command Topology",
            "---",
            "flowchart TD",
            "    root[cerebro]",
        ]

        seen_groups: set[tuple[str, ...]] = set()
        for cmd in sorted(commands, key=lambda item: item.name):
            parent_id = "root"
            current_path: list[str] = []
            for segment in cmd.group_path:
                current_path.append(segment)
                group_key = tuple(current_path)
                group_id = self._node_id("group", current_path)
                if group_key not in seen_groups:
                    lines.append(f"    {group_id}[{self._escape_mermaid_label(segment)}]")
                    lines.append(f"    {parent_id} --> {group_id}")
                    seen_groups.add(group_key)
                parent_id = group_id

            command_id = self._node_id("command", [cmd.name])
            lines.append(f"    {command_id}[{self._escape_mermaid_label(cmd.command_slug)}]")
            lines.append(f"    {parent_id} --> {command_id}")

            for param in cmd.params:
                param_id = self._node_id("param", [cmd.name, param.name])
                label = f"{param.name}: {param.annotation}"
                lines.append(f"    {param_id}[{self._escape_mermaid_label(label)}]")
                lines.append(f"    {command_id} -.-> {param_id}")

        return "\n".join(lines) + "\n"

    def _render_mermaid_groups(self, commands: list[CommandDoc]) -> str:
        grouped: dict[tuple[str, ...], list[CommandDoc]] = defaultdict(list)
        for cmd in commands:
            grouped[tuple(cmd.group_path)].append(cmd)

        lines = [
            "---",
            "title: Cerebro CLI Group Heatmap",
            "---",
            "mindmap",
            "  root((cerebro))",
        ]

        for group_path, items in sorted(grouped.items(), key=lambda item: item[0]):
            if not group_path:
                for cmd in sorted(items, key=lambda item: item.name):
                    lines.append(f"    {self._escape_mermaid_label(cmd.command_slug)}")
                continue

            indent = "    "
            for depth, segment in enumerate(group_path, start=1):
                lines.append(f"{indent}{self._escape_mermaid_label(segment)}")
                indent += "  "

            for cmd in sorted(items, key=lambda item: item.name):
                lines.append(f"{indent}{self._escape_mermaid_label(cmd.command_slug)}")

        return "\n".join(lines) + "\n"

    def _build_catalog(self, commands: list[CommandDoc], generated_at: str) -> dict[str, object]:
        return {
            "generated_at": generated_at,
            "total_commands": len(commands),
            "commands": [
                {
                    "name": cmd.name,
                    "group_path": cmd.group_path,
                    "command_slug": cmd.command_slug,
                    "func_name": cmd.func_name,
                    "description": cmd.description,
                    "source_line": cmd.source_line,
                    "syntax": self._render_syntax(cmd),
                    "params": [
                        {
                            "name": param.name,
                            "kind": param.kind,
                            "annotation": param.annotation,
                            "default": param.default,
                            "required": param.required,
                            "help_text": param.help_text,
                            "cli_flags": param.cli_flags,
                        }
                        for param in cmd.params
                    ],
                    "examples": cmd.examples,
                }
                for cmd in sorted(commands, key=lambda item: item.name)
            ],
        }

    def _build_scene_graph(self, commands: list[CommandDoc], generated_at: str) -> dict[str, object]:
        nodes: list[dict[str, object]] = []
        edges: list[dict[str, str]] = []
        seen_nodes: set[str] = set()

        def add_node(node_id: str, **payload):
            if node_id in seen_nodes:
                return
            seen_nodes.add(node_id)
            nodes.append({"id": node_id, **payload})

        add_node(
            "cerebro",
            type="root",
            label="cerebro",
            depth=0,
            position={"x": 0, "y": 0, "z": 0},
        )

        for cmd in sorted(commands, key=lambda item: item.name):
            parent_id = "cerebro"
            for depth, segment in enumerate(cmd.group_path, start=1):
                group_id = self._node_id("group", cmd.group_path[:depth])
                add_node(
                    group_id,
                    type="group",
                    label=segment,
                    depth=depth,
                    position={"x": depth * 4, "y": -depth * 2, "z": depth},
                )
                edges.append({"source": parent_id, "target": group_id, "kind": "contains"})
                parent_id = group_id

            command_id = self._node_id("command", [cmd.name])
            add_node(
                command_id,
                type="command",
                label=cmd.command_slug,
                depth=len(cmd.group_path) + 1,
                position={"x": (len(cmd.group_path) + 1) * 5, "y": -len(cmd.params), "z": cmd.source_line / 10},
                metadata={
                    "full_name": cmd.name,
                    "source_line": cmd.source_line,
                    "func_name": cmd.func_name,
                },
            )
            edges.append({"source": parent_id, "target": command_id, "kind": "contains"})

            for index, param in enumerate(cmd.params, start=1):
                param_id = self._node_id("param", [cmd.name, param.name])
                add_node(
                    param_id,
                    type="parameter",
                    label=param.name,
                    depth=len(cmd.group_path) + 2,
                    position={"x": (len(cmd.group_path) + 2) * 5, "y": -index, "z": index},
                    metadata={
                        "annotation": param.annotation,
                        "kind": param.kind,
                        "required": param.required,
                    },
                )
                edges.append({"source": command_id, "target": param_id, "kind": "parameter"})

        return {
            "generated_at": generated_at,
            "scene": "cerebro-cli-topology",
            "nodes": nodes,
            "edges": edges,
            "layout": {
                "type": "layered-3d",
                "x_axis": "hierarchy_depth",
                "y_axis": "parameter_density",
                "z_axis": "source_line",
            },
        }

    def _build_visualization_manifest(self, commands: list[CommandDoc], generated_at: str) -> dict[str, object]:
        group_summary: dict[str, int] = defaultdict(int)
        for cmd in commands:
            label = "root" if not cmd.group_path else " ".join(cmd.group_path)
            group_summary[label] += 1

        return {
            "generated_at": generated_at,
            "project": "cerebro",
            "artifacts": {
                "markdown_index": "commands/README.md",
                "catalog_json": "commands/catalog.json",
                "mermaid_topology": "mermaid/command-topology.mmd",
                "mermaid_groups": "mermaid/command-groups.mmd",
                "scene_graph": "visualization/scene.json",
            },
            "visualization_targets": [
                {
                    "name": "Mermaid",
                    "status": "ready",
                    "use_case": "docs, dashboards, markdown previews",
                },
                {
                    "name": "Three.js",
                    "status": "ready-via-scene-json",
                    "use_case": "interactive 3D command topology",
                },
                {
                    "name": "A-Frame",
                    "status": "ready-via-scene-json",
                    "use_case": "WebXR and immersive browser visualization",
                },
                {
                    "name": "Babylon.js",
                    "status": "ready-via-scene-json",
                    "use_case": "advanced scene rendering and holographic UI prototypes",
                },
            ],
            "summary": {
                "total_commands": len(commands),
                "total_groups": len(group_summary),
                "group_distribution": dict(sorted(group_summary.items())),
            },
            "note": (
                "This manifest does not generate physical holograms. "
                "It emits structured graph assets that holographic or XR-capable renderers can consume."
            ),
        }

    def _render_syntax(self, cmd: CommandDoc) -> str:
        parts = [cmd.name]
        for param in cmd.params:
            if param.kind == "option":
                flag = param.cli_flags[0] if param.cli_flags else f"--{param.name.replace('_', '-')}"
                token = f"{flag} <{param.name}>"
                parts.append(token if param.required else f"[{token}]")
            else:
                token = f"<{param.name}>"
                parts.append(token if param.required else f"[{token}]")
        return " ".join(parts)

    def _is_typer_constructor(self, value: ast.AST) -> bool:
        return isinstance(value, ast.Call) and self._call_name(value.func).endswith("Typer")

    def _is_add_typer_call(self, call: ast.Call) -> bool:
        return (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "add_typer"
            and isinstance(call.func.value, ast.Name)
        )

    def _is_typer_helper_call(self, call: ast.Call) -> bool:
        helper_name = self._call_name(call.func)
        return helper_name.endswith("Option") or helper_name.endswith("Argument")

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = self._call_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    def _kwarg_literal(self, call: ast.Call, keyword_name: str) -> str | None:
        for keyword in call.keywords:
            if keyword.arg == keyword_name:
                value = self._literal_or_source(keyword.value)
                return value if isinstance(value, str) else str(value)
        return None

    def _literal_or_source(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant):
            if node.value is Ellipsis:
                return "Ellipsis"
            return str(node.value)
        return ast.unparse(node)

    def _node_id(self, prefix: str, parts: list[str]) -> str:
        raw = "_".join(parts).lower()
        safe = "".join(char if char.isalnum() else "_" for char in raw)
        return f"{prefix}_{safe}".strip("_")

    def _escape_mermaid_label(self, label: str) -> str:
        return label.replace('"', "'").replace("[", "(").replace("]", ")")


def generate_docs() -> dict[str, int | str]:
    """Backward-compatible entrypoint used by the legacy shell wrapper."""
    print("Starting documentation generation...")
    generator = DocumentationGenerator(format="markdown")
    result = generator.generate(project=".", output="docs")
    print(f"Generated {result['pages']} pages in {result['output_dir']}")
    return result


if __name__ == "__main__":
    generate_docs()
