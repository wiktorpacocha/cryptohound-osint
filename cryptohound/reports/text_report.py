from datetime import datetime
from ..analysis.risk_scoring import RiskScore


def render_text_report(profile, risk: RiskScore) -> str:
    lines: list[str] = []
    lines.append("=== CryptoHound OSINT Report ===")
    lines.append(f"Generated: {datetime.utcnow().isoformat()}Z")
    lines.append(f"Chain   : {profile.chain}")
    lines.append(f"Address : {profile.address}")
    lines.append("")
    lines.append("---- Address Overview ----")
    lines.append(f"Balance  : {profile.balance:.8f} ETH")
    lines.append(f"Tx Count : {profile.tx_count}")
    lines.append(f"First Seen : {profile.first_seen}")
    lines.append(f"Last  Seen : {profile.last_seen}")
    lines.append("")
    lines.append("---- Risk Assessment ----")
    lines.append(f"Risk Score: {risk.score}/100")
    for flag in risk.flags:
        lines.append(f"- [{flag.code}] {flag.description} (weight {flag.weight})")
    lines.append("")
    lines.append("Disclaimer: OSINT & heuristic-based only. Not financial advice or formal forensics.")
    return "\n".join(lines)
