import csv
from pathlib import Path

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


@app.command("report")
def report_command(
    address: str = typer.Argument(..., help="Wallet address to investigate."),
    chain: str = typer.Option(
        "auto",
        "--chain",
        "-c",
        help="Blockchain: auto (detect), eth (Ethereum), btc (Bitcoin).",
    ),
    outdir: Path = typer.Option(
        Path("./reports"),
        "--outdir",
        "-d",
        help="Directory where all report files will be saved.",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="Base name for output files (default: derived from address).",
    ),
):
    """
    Generate a full OSINT report for an address:

    - Text summary (.txt)
    - HTML report (.html)
    - Transactions CSV (.csv)
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

    # Select client
    if chain_l == "eth":
        client = EthereumClient(cfg)
        chain_name = "Ethereum"
    elif chain_l == "btc":
        client = BitcoinClient(cfg)
        chain_name = "Bitcoin"
    else:
        console.print(f"[red]Unsupported chain: {chain_l}[/red]")
        raise typer.Exit(code=1)

    console.log(f"Generating full report for [bold]{address}[/bold] on [bold]{chain_name}[/bold]...")

    try:
        profile = client.get_address_profile(address)
        txs = client.get_recent_transactions(address, limit=100)
    except Exception as exc:
        console.print(f"[red]Error during lookup:[/red] {exc}")
        raise typer.Exit(code=1)

    risk = basic_risk_scoring(profile, txs)
    text_report = render_text_report(profile, risk)
    html_report = render_html_report(profile, risk, txs)

    # Prepare output directory and filenames
    outdir.mkdir(parents=True, exist_ok=True)

    if name:
        base = name.strip()
    else:
        # Derive a simple safe base from address (first 10 chars, no special symbols)
        base = address.replace(":", "_").replace("/", "_")[:16] or "report"

    txt_path = outdir / f"{base}.txt"
    html_path = outdir / f"{base}.html"
    csv_path = outdir / f"{base}_txs.csv"

    # Write TXT
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text_report)

    # Write HTML
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_report)

    # Write CSV (if we have txs)
    if txs:
        fieldnames = ["hash", "from", "to", "value", "timeStamp"]
        try:
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
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
        except Exception as exc:
            console.print(f"[red]Failed to write CSV:[/red] {exc}")
            csv_path = None
    else:
        csv_path = None
        console.print(
            "[yellow]No transactions available to export to CSV "
            "(or tx export not yet implemented for this chain).[/yellow]"
        )

    console.print(
        Panel(
            "\n".join(
                [
                    "Report files generated:",
                    f"- [bold]TXT[/bold] : {txt_path}",
                    f"- [bold]HTML[/bold]: {html_path}",
                    f"- [bold]CSV[/bold] : {csv_path if csv_path else 'N/A'}",
                ]
            ),
            title="CryptoHound – Report Generated",
            expand=True,
        )
    )



if __name__ == "__main__":
    app()
