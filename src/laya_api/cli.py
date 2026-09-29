"""Command Line Interface for Laya API."""

import os
import platform
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from laya_api import __version__
from laya_api.server import create_app
from laya_api.engine import create_engine

app = typer.Typer(
    name="laya-api",
    help="Ultra-Fast OpenAI & Anthropic-Compatible Inference Server for Laya Models"
)
console = Console()


@app.command()
def version():
    """Display the Laya API version."""
    console.print(f"[bold green]Laya API[/bold green] version [cyan]{__version__}[/cyan]")


@app.command()
def doctor():
    """Run diagnostics to inspect hardware acceleration and platform capabilities."""
    table = Table(title="Laya API - System & Hardware Diagnostic")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")

    table.add_row("Platform", platform.platform(), "✅ OK")
    table.add_row("Python Version", sys.version.split()[0], "✅ OK")
    table.add_row("Architecture", platform.machine(), "✅ OK")

    # Check MLX (Apple Silicon)
    mlx_status = "❌ Not Installed"
    if sys.platform == "darwin":
        try:
            import mlx.core as mx  # type: ignore
            mlx_status = "✅ Available (Metal Acceleration)"
        except ImportError:
            mlx_status = "⚠️ Not installed (`pip install mlx`)"
    table.add_row("Apple MLX / Metal", mlx_status, "")

    # Check PyTorch / CUDA
    torch_status = "❌ Not Installed"
    try:
        import torch  # type: ignore
        if torch.cuda.is_available():
            torch_status = f"✅ CUDA Available ({torch.cuda.get_device_name(0)})"
        else:
            torch_status = "✅ Available (CPU / Metal MPS)"
    except ImportError:
        torch_status = "⚠️ Not installed"
    table.add_row("PyTorch / CUDA", torch_status, "")

    # Detected default backend
    engine = create_engine(backend="auto")
    table.add_row("Detected Backend", engine.backend_name, "🚀 Ready")

    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host IP to bind TCP listener"),
    port: int = typer.Option(8000, help="Port for HTTP/2 and WebSocket server"),
    model: str = typer.Option("nandhakishorm/laya-base", help="Model name, HuggingFace ID, or weights path"),
    backend: str = typer.Option("auto", help="Inference backend: auto, mlx, torch, cuda, cpu, mock"),
    socket: Optional[str] = typer.Option(None, help="Path to Unix Domain Socket (UDS)"),
    max_context: int = typer.Option(1024, help="Maximum token limit for context window validation"),
):
    """Start the Laya API inference server."""
    import uvicorn

    console.print(f"[bold green]Starting Laya API Server...[/bold green]")
    console.print(f" • [cyan]Model:[/cyan] {model}")
    console.print(f" • [cyan]Backend:[/cyan] {backend}")
    console.print(f" • [cyan]Max Context:[/cyan] {max_context} tokens")

    engine = create_engine(model_name=model, backend=backend)
    console.print(f" • [cyan]Loaded Engine:[/cyan] [bold yellow]{engine.backend_name}[/bold yellow]")

    api_app = create_app(engine=engine, max_context=max_context, model_name=model, backend=backend)

    if socket:
        console.print(f" • [cyan]Unix Domain Socket:[/cyan] [green]{socket}[/green]")
        uvicorn.run(api_app, uds=socket)
    else:
        console.print(f" • [cyan]TCP Listening:[/cyan] [green]http://{host}:{port}[/green]")
        uvicorn.run(api_app, host=host, port=port)


if __name__ == "__main__":
    app()
