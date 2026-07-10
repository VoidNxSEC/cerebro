import re
import os
from pathlib import Path

def generate_docs():
    """
    Generates documentation for Cerebro CLI commands by parsing 
    src/phantom/cli.py directly.
    """
    print("📚 Starting Documentation Generation...")
    
    cli_path = Path("src/phantom/cli.py")
    if not cli_path.exists():
        print("❌ src/phantom/cli.py not found.")
        return

    content = cli_path.read_text()
    
    # Regex to find command definitions
    # Matches:
    # @app.command("name") ... def func(args): """docstring"""
    # or @group.command("name")
    
    # We look for the pattern: decorator -> newline(s) -> def -> docstring
    # We iterate manually to handle multiline signatures
    
    commands = []
    
    # Split by lines to process somewhat linearly or use a big regex
    # A big regex is better for capturing multiline function defs
    
    pattern = re.compile(
        r'@(\w+)\.command\("([\w-]+)"(?:,.*?)?\)\s*\n'  # Decorator: group, name
        r'(?:async )?def (\w+)\((.*?)\):\s*\n'           # Signature: func_name, args
        r'\s*"""(.*?)"""',                               # Docstring
        re.DOTALL | re.MULTILINE
    )
    
    matches = pattern.finditer(content)
    
    for match in matches:
        group_var = match.group(1)
        cmd_slug = match.group(2)
        func_name = match.group(3)
        args_str = match.group(4)
        docstring = match.group(5)
        
        # Map variable names to CLI subcommand groups
        group_map = {
            "app": "",
            "knowledge_app": "knowledge",
            "ops_app": "ops",
            "rag_app": "rag"
        }
        
        group_name = group_map.get(group_var, group_var.replace("_app", ""))
        full_name = f"cerebro {group_name} {cmd_slug}".replace("  ", " ").strip()
        
        # Parse Args
        params = []
        # Normalize args string
        args_clean = args_str.replace("\n", " ").strip()
        
        # Simple parser for "name: type = default"
        if args_clean:
            # Handle commas, ignoring quotes
            parts = []
            current = ""
            in_quote = False
            for char in args_clean:
                if char == '"' or char == "'": in_quote = not in_quote
                if char == ',' and not in_quote:
                    parts.append(current.strip())
                    current = ""
                else:
                    current += char
            if current: parts.append(current.strip())
            
            for p in parts:
                if ":" in p and "self" not in p:
                    try:
                        p_name = p.split(":")[0].strip()
                        rest = p.split(":")[1]
                        
                        p_type = "str"
                        p_default = "Required"
                        
                        if "=" in rest:
                            p_type = rest.split("=")[0].strip()
                            p_default = rest.split("=")[1].strip()
                        else:
                            p_type = rest.strip()
                            
                        params.append({"name": p_name, "type": p_type, "default": p_default})
                    except:
                        pass

        commands.append({
            "name": full_name,
            "description": docstring.strip(),
            "params": params,
            "func_name": func_name
        })

    print(f"✅ Found {len(commands)} commands.")

    # 3. Generate Markdown
    out_dir = Path("docs/commands")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    index_content = "# 🧠 Cerebro CLI Command Reference\n\n"
    
    for cmd in sorted(commands, key=lambda x: x['name']):
        safe_filename = cmd["name"].replace(" ", "_") + ".md"
        desc_short = cmd['description'].splitlines()[0] if cmd['description'] else ''
        index_content += f"- [{cmd['name']}]({safe_filename}) - {desc_short}\n"
        
        md_content = f"""# Command: `{cmd['name']}`

## 1. Descrição
{cmd['description']}

**Sintaxe:**
```bash
{cmd['name']} [OPTIONS] [ARGS]
```

## 2. Parâmetros

| Nome | Tipo | Default | Descrição |
|------|------|---------|-----------|"""
        if cmd["params"]:
            for p in cmd["params"]:
                p_type = p['type'].replace("typer.", "").replace("Optional[", "").replace("]", "")
                p_default = p['default'].replace("typer.Option(", "").replace("typer.Argument(", "").rstrip(")")
                md_content += f"| `{p['name']}` | `{p_type}` | `{p_default}` | - |\n"
        else:
            md_content += "| - | - | - | - |\n"

        md_content += f"""

## 3. Exemplos
```bash
# Exemplo padrão
{cmd['name']}
```

## 4. Saída
* **Formato:** Texto Rich (Console) ou JSON (se aplicável).
* **Logs:** Erros são enviados para stderr.

## 5. Erros Comuns
* `Exit Code 1`: Falha na execução ou dependência ausente.

## 6. Dependências
* Módulo: `src/phantom/cli.py`
* Função: `{cmd['func_name']}`

## 7. Testes
* Verifique `tests/test_cli.py` para cobertura.

---
*Gerado automaticamente em {os.popen('date').read().strip()}*
"""
        (out_dir / safe_filename).write_text(md_content)
        print(f"   Gerado: {safe_filename}")
    
    (out_dir / "README.md").write_text(index_content)
    print(f"✨ Documentation generated in {out_dir}")

if __name__ == "__main__":
    generate_docs()
