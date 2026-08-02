import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

setup_app = typer.Typer(help="Interactive configuration and setup wizard", no_args_is_help=True)
console = Console()

ENV_PATH = Path(".env")

def write_env(key: str, value: str):
    """Write or update a key in the local .env file securely."""
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r") as f:
            lines = f.readlines()
    
    updated = False
    with open(ENV_PATH, "w") as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f"{key}={value}\n")
                updated = True
            else:
                f.write(line)
        if not updated:
            f.write(f"{key}={value}\n")


@setup_app.command("wizard")
def wizard():
    """
    Start the interactive Cerebro setup wizard!
    Configure your LLM provider, API keys, and environment dynamically.
    """
    console.print(Panel("[bold green]🧠 Welcome to the Cerebro Setup Wizard![/bold green]", border_style="green"))
    console.print("Let's configure your local environment specifically for your deployment needs.\n")

    # Provider Selection
    provider = Prompt.ask(
        "[cyan]Primary LLM Provider[/cyan]", 
        choices=["azure", "llamacpp", "vertex-ai", "gemini"], 
        default="azure"
    )
    
    write_env("CEREBRO_LLM_PROVIDER", provider)
    
    if provider == "azure":
        console.print("\n[bold blue]☁️  Azure OpenAI Configuration[/bold blue]")
        endpoint = Prompt.ask("Azure OpenAI Endpoint (e.g. https://my-resource.openai.azure.com/)")
        write_env("AZURE_OPENAI_ENDPOINT", endpoint)
        
        api_key = Prompt.ask("Azure OpenAI API Key", password=True)
        write_env("AZURE_OPENAI_API_KEY", api_key)
        
        chat_dep = Prompt.ask("Chat Deployment Name", default="gpt-4o")
        write_env("AZURE_OPENAI_CHAT_DEPLOYMENT", chat_dep)

        embed_dep = Prompt.ask("Embeddings Deployment Name", default="text-embedding-3-small")
        write_env("AZURE_OPENAI_EMBED_DEPLOYMENT", embed_dep)

    elif provider == "vertex-ai":
        console.print("\n[bold yellow]☁️  GCP Vertex AI Configuration[/bold yellow]")
        project_id = Prompt.ask("GCP Project ID")
        write_env("GCP_PROJECT_ID", project_id)

    elif provider == "llamacpp":
        console.print("\n[bold magenta]🦙 Llama.CPP Local Configuration[/bold magenta]")
        url = Prompt.ask("Local Inference Server URL", default="http://localhost:8081")
        write_env("LLAMA_CPP_URL", url)

    # Vector Store Strategy
    console.print("\n[bold cyan]📦 Vector Store Selection[/bold cyan]")
    vstore = Prompt.ask("Core Vector Database", choices=["chroma", "elasticsearch"], default="elasticsearch")
    
    if vstore == "elasticsearch":
        es_url = Prompt.ask("Elasticsearch URL", default="http://localhost:9200")
        write_env("ELASTICSEARCH_URL", es_url)
        if Confirm.ask("Require Authentication for Elasticsearch?", default=False):
            es_user = Prompt.ask("Elasticsearch User", default="elastic")
            es_pass = Prompt.ask("Elasticsearch Password", password=True)
            write_env("ELASTICSEARCH_USER", es_user)
            write_env("ELASTICSEARCH_PASSWORD", es_pass)

    console.print(f"\n[green]✅ Setup Complete! Variables written to {ENV_PATH.absolute()}[/green]")
    console.print("[dim]Hint: Exit the nix shell and re-enter, or run 'source .env' to apply these immediately.[/dim]")

@setup_app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        wizard()
