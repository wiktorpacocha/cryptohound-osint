from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class RiskFlag:
    code: str
    description: str
    weight: int


@dataclass
class RiskScore:
    score: int
    flags: List[RiskFlag] = field(default_factory=list)


def basic_risk_scoring(profile: Any, txs: list[dict[str, Any]]) -> RiskScore:
    """
    Heuristic 0–100 risk engine.

    IMPORTANT:
    - This is OSINT-only, best-effort scoring.
    - It does NOT prove that an address is criminal.
    - Use as a triage / prioritisation tool only.
    """

    flags: list[RiskFlag] = []
    total_weight = 0

    def add_flag(code: str, desc: str, weight: int) -> None:
        nonlocal total_weight
        flags.append(RiskFlag(code=code, description=desc, weight=weight))
        total_weight += weight

    addr = (profile.address or "").strip()
    chain = (profile.chain or "").lower().strip()

    # -----------------------------
    # Basic activity stats
    # -----------------------------
    incoming = 0
    outgoing = 0
    unique_senders: set[str] = set()
    unique_receivers: set[str] = set()

    for tx in txs:
        frm = str(tx.get("from", "")).strip()
        to = str(tx.get("to", "")).strip()

        if addr and frm == addr:
            outgoing += 1
            if to:
                unique_receivers.add(to)
        if addr and to == addr:
            incoming += 1
            if frm:
                unique_senders.add(frm)

    # -----------------------------
    # Heuristic 1: Incoming-only funnel
    # -----------------------------
    if incoming > 0 and outgoing == 0 and getattr(profile, "balance", 0) > 0:
        add_flag(
            "INCOMING_ONLY",
            "Address only receives funds and never sends them out (possible deposit or collector).",
            25,
        )

    # -----------------------------
    # Heuristic 2: Outgoing-only burner / mule
    # -----------------------------
    if outgoing > 0 and incoming == 0:
        add_flag(
            "OUTGOING_ONLY",
            "Address only sends funds and never receives (possible relay, mule, or change-only wallet).",
            20,
        )

    # -----------------------------
    # Heuristic 3: High transaction volume
    # -----------------------------
    tx_count = getattr(profile, "tx_count", len(txs) or 0)

    if tx_count >= 100:
        add_flag(
            "HIGH_VOLUME",
            f"High on-chain activity (tx count ≈ {tx_count}).",
            15,
        )
    elif tx_count >= 30:
        add_flag(
            "ELEVATED_VOLUME",
            f"Moderately high on-chain activity (tx count ≈ {tx_count}).",
            8,
        )

    # -----------------------------
    # Heuristic 4: Many unique peers (fan-in / fan-out)
    # -----------------------------
    if len(unique_senders) >= 20:
        add_flag(
            "MANY_SENDERS",
            f"Receives from many unique addresses ({len(unique_senders)}+).",
            15,
        )
    elif len(unique_senders) >= 10:
        add_flag(
            "MULTIPLE_SENDERS",
            f"Receives from several different addresses ({len(unique_senders)}+).",
            8,
        )

    if len(unique_receivers) >= 20:
        add_flag(
            "MANY_RECIPIENTS",
            f"Sends to many unique addresses ({len(unique_receivers)}+).",
            15,
        )
    elif len(unique_receivers) >= 10:
        add_flag(
            "MULTIPLE_RECIPIENTS",
            f"Sends to several different addresses ({len(unique_receivers)}+).",
            8,
        )

    # -----------------------------
    # Heuristic 5: Value-based signals (big transfers / dusting)
    # -----------------------------
    big_in_threshold_eth = 1 * 10**18        # 1 ETH in wei
    dust_threshold_eth = 1 * 10**15          # 0.001 ETH in wei

    big_in_threshold_btc_sats = int(0.1 * 10**8)   # 0.1 BTC
    dust_threshold_btc_sats = int(0.0001 * 10**8)  # 0.0001 BTC

    small_incoming = 0
    big_incoming = 0

    for tx in txs:
        to = str(tx.get("to", "")).strip()
        if addr and to != addr:
            continue

        raw_val = tx.get("value", "0")

        try:
            v_int = int(raw_val)
        except (TypeError, ValueError):
            continue

        if chain in ("ethereum", "eth", "bsc", "bnb", "binance smart chain"):
            # Treat value as wei (EVM-style)
            if v_int >= big_in_threshold_eth:
                big_incoming += 1
            if v_int <= dust_threshold_eth:
                small_incoming += 1
        elif chain == "bitcoin":
            # Treat value as satoshis
            if v_int >= big_in_threshold_btc_sats:
                big_incoming += 1
            if v_int <= dust_threshold_btc_sats:
                small_incoming += 1

    if big_incoming >= 1:
        add_flag(
            "LARGE_INCOMING",
            "Address has at least one large incoming transfer.",
            20,
        )

    if small_incoming >= 5:
        add_flag(
            "DUSTING_PATTERN",
            "Address receives many very small incoming amounts (possible dust / spam / mixer-style behaviour).",
            15,
        )

    # -----------------------------
    # Heuristic 6: Time-based burst
    # -----------------------------
    # We expect timeStamp as unix seconds (string or int). If not present, we skip.
    timestamps: list[int] = []
    for tx in txs:
        ts = tx.get("timeStamp")
        try:
            ts_int = int(ts)
        except (TypeError, ValueError):
            continue
        timestamps.append(ts_int)

    timestamps.sort()
    if len(timestamps) >= 5:
        # Sliding window: 5+ txs in 10 minutes
        window = 600  # seconds
        i = 0
        for j in range(len(timestamps)):
            while timestamps[j] - timestamps[i] > window:
                i += 1
            if j - i + 1 >= 5:
                add_flag(
                    "BURST_ACTIVITY",
                    "Detected a burst of transactions in a short time window.",
                    10,
                )
                break

    # -----------------------------
    # Heuristic 7: Self-shuffling / loop behaviour
    # -----------------------------
    self_like = 0
    for tx in txs:
        frm = str(tx.get("from", "")).strip()
        to = str(tx.get("to", "")).strip()
        if addr and (frm == addr and to == addr):
            self_like += 1

    if self_like >= 1:
        add_flag(
            "SELF_SHUFFLING",
            "Address appears on both sides of its own transactions (self-transfer / consolidation).",
            10,
        )

    # -----------------------------
    # Heuristic 8: Tags from upstream analysis
    # (Future-proofing – if you later add labels like 'scam', 'mixer', etc.)
    # -----------------------------
    try:
        tags = [str(t).lower() for t in getattr(profile, "tags", [])]
    except Exception:
        tags = []

    if any("scam" in t for t in tags):
        add_flag(
            "TAG_SCAM",
            "Address is tagged as scam / fraud in upstream OSINT data.",
            40,
        )

    if any("mixer" in t or "tornado" in t for t in tags):
        add_flag(
            "TAG_MIXER",
            "Address is tagged as mixer / obfuscation service.",
            30,
        )

    # -----------------------------
    # Final score (cap at 100)
    # -----------------------------
    score = max(0, min(total_weight, 100))
    return RiskScore(score=score, flags=flags)
