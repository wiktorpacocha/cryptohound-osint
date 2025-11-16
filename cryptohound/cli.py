import typer
from rich.console import Console
from rich.panel import Panel
from .config import load_config
from .chains.ethereum import EthereumClient
from .analysis.risk_scoring import basic_risk_scoring
from .reports.text_report import render_text_report

console = Console()
app = typer.Typer(help="CryptoHound – Crypto Fraud OSINT Toolkit")


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context):
    """
    Default entrypoint for CryptoHound.

    If no subcommand is given (just: python -m cryptohound.cli),
    we show a welcome panel and a short hint.
    """
    if ctx.invoked_subcommand is None:
        console.print(
            Panel(
                "Welcome to CryptoHound – Crypto Fraud OSINT Toolkit (MVP).\n\n"
                "Use the commands below to start investigating.\n"
                "Example: python -m cryptohound.cli hello\n\n"
                "For a full list of commands, run:\n"
                "  python -m cryptohound.cli --help",
                title="CryptoHound",
                expand=True,
            )
        )
        raise typer.Exit()


@app.command()
def hello():
    """
    Simple test command to verify that the CLI works.
    """
    msg = "Welcome! CryptoHound is ready to hunt scammers (MVP)."
    console.print(Panel(msg, title="CryptoHound", expand=True))
@app.command("profile-address")
def profile_address(
    address: str = typer.Argument(..., help="Ethereum wallet address (0x...)"),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Optional path to save report as .txt"
    ),
):
    """
    Build a basic OSINT profile of an Ethereum address.
    """
    cfg = load_config()
    client = EthereumClient(cfg)

    console.log(f"Profiling [bold]{address}[/bold] on [bold]Ethereum[/bold]...")

    try:
        profile = client.get_address_profile(address)
        txs = client.get_recent_transactions(address, limit=50)
    except Exception as exc:
        console.print(f"[red]Error during lookup:[/red] {exc}")
        raise typer.Exit(code=1)

    risk = basic_risk_scoring(profile, txs)
    report_text = render_text_report(profile, risk)

    console.print(Panel(report_text, title="CryptoHound Report", expand=True))

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report_text)
        console.print(f"[green]Report saved to {output}[/green]")

if __name__ == "__main__":
    app()
