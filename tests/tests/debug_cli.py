import typer

app = typer.Typer()

@app.command()
def test(name: str = typer.Option("World")):
    print(f"Hello {name}")

if __name__ == "__main__":
    app()