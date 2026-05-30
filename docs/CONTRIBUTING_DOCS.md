# 📖 Documentation Guidelines

The Phantom/Cerebro documentation is **auto-generated** from the source code.
We strictly adhere to the DRY (Don't Repeat Yourself) principle.

## 🔄 How it Works

1.  **Source of Truth:** The code itself (`src/phantom/cli.py`) is the source.
2.  **Docstrings:** Command descriptions are extracted from function docstrings.
3.  **Arguments:** Parameters and types are parsed from function signatures.
4.  **Generator:** `scripts/generate_docs.py` parses the code and outputs Markdown to `docs/commands/`.

## 🛠️ Generating Docs

To update the documentation after changing the CLI:

```bash
./scripts/generate-docs.sh
```

## 📝 Writing Good Docstrings

When adding a new command, follow this format in `src/phantom/cli.py`:

```python
@app.command("my-command")
def my_command(
    arg1: str = typer.Argument(..., help="Description of arg1"),
    opt1: bool = typer.Option(False, help="Description of opt1")
):
    """
    Short summary of what the command does.

    More detailed explanation if necessary.
    """
    ...
```

The generator will automatically pick up:
*   Command name (`cerebro my-command`)
*   Description ("Short summary...")
*   Parameters (`arg1`, `opt1`) with types and defaults.

## 🚫 Do Not Edit Manually

Files in `docs/commands/*.md` are overwritten by the generator.
**Do not edit them manually.** Edit the Python code instead.
