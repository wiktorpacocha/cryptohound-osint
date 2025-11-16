import csv
import typer
from rich.console import Console
from rich.panel import Panel

from .config import load_config
from .chains.ethereum import EthereumClient
from .chains.bitcoin import BitcoinClient
from .analysis.risk_scoring import basic_risk_scoring
from .reports.text_report import render_text_report
from .utils.validators import detect_chain_from_address
from .reports.html_report import render_html_report

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
                "Welcome to CryptoHound – Crypto Fraud OSINT Toolkit.\n\n"
                "Examples:\n"
                "  python -m cryptohound.cli hello\n"
                "  python -m cryptohound.cli profile-address 1BoatSLRHtKNngkdXEeobR76b53LETtpyT\n"
                "  python -m cryptohound.cli profile-address 0x00000000219ab540356cBB839Cbe05303d7705Fa\n\n"
                "Tip: Chain is detected automatically from the address format.\n"
                "You can still force it with: --chain eth or --chain btc",
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
    address: str = typer.Argument(..., help="Wallet address to profile."),
    chain: str = typer.Option(
        "auto",
        "--chain",
        "-c",
        help="Blockchain: auto (detect), eth (Ethereum), btc (Bitcoin).",
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Optional path to save text report as .txt"
    ),
    html_output: str | None = typer.Option(
        None, "--html", help="Optional path to save HTML report (e.g. report.html)"
    ),
    csv_output: str | None = typer.Option(
        None, "--csv", help="Optional path to save transactions as CSV (e.g. txs.csv)"
    ),
):


    """
    Build a basic OSINT profile of a crypto address on the selected or detected chain.
    """
    cfg = load_config()
    chain_l = chain.lower().strip()

    # Auto-detect chain if requested
    if chain_l == "auto":
        detected = detect_chain_from_address(address)
        if detected is None:
            console.print(
                "[red]Could not detect blockchain from this address format.[/red]\n"
                "Please specify the chain explicitly with --chain eth or --chain btc."
            )
            raise typer.Exit(code=1)
        chain_l = detected
        console.log(f"Auto-detected chain: [bold]{chain_l}[/bold]")

    # Select appropriate client
    if chain_l == "eth":
        client = EthereumClient(cfg)
        chain_name = "Ethereum"
    elif chain_l == "btc":
        client = BitcoinClient(cfg)
        chain_name = "Bitcoin"
    else:
        console.print(f"[red]Unsupported chain: {chain}[/red]")
        raise typer.Exit(code=1)

    console.log(f"Profiling [bold]{address}[/bold] on [bold]{chain_name}[/bold]...")

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
    if html_output:
        html = render_html_report(profile, risk, txs)
        with open(html_output, "w", encoding="utf-8") as f:
            f.write(html)
        console.print(f"[green]HTML report saved to {html_output}[/green]")
    if csv_output:
        if not txs:
            console.print(
                "[yellow]No transactions available to export to CSV "
                "(or tx export not yet implemented for this chain).[/yellow]"
            )
        else:
            fieldnames = ["hash", "from", "to", "value", "timeStamp"]
            try:
                with open(csv_output, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for tx in txs:
                        row = {
                            "hash": tx.get("hash", ""),
                            "from": tx.get("from", ""),
                            "to": tx.get("to", ""),
                            "value": tx.get("value", ""),
                            "timeStamp": tx.get("timeStamp", ""),
                        }
                        writer.writerow(row)
                console.print(f"[green]CSV transactions exported to {csv_output}[/green]")
            except Exception as exc:
                console.print(f"[red]Failed to write CSV:[/red] {exc}")


if __name__ == "__main__":
    app()
