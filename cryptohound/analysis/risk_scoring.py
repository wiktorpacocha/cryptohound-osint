from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class RiskFlag:
    code: str
    description: str
    weight: int


@dataclass
class RiskScore:
    score: int
    flags: List[RiskFlag]


def basic_risk_scoring(profile, recent_txs: List[Dict[str, Any]]) -> RiskScore:
    score = 0
    flags: List[RiskFlag] = []

    # Example heuristic: only incoming txs (could be collection/drop wallet)
    if recent_txs and all(tx.get("to", "").lower() == profile.address.lower() for tx in recent_txs):
        flags.append(
            RiskFlag(
                code="ONLY_INCOMING",
                description="Only incoming transactions detected; could be a collection or drop wallet.",
                weight=15,
            )
        )
        score += 15

    # Here we can add more rules later (mixers, exchanges, etc.)

    score = max(0, min(score, 100))
    return RiskScore(score=score, flags=flags)
