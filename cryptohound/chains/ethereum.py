from typing import Any
import httpx

from .base import ChainClient, AddressProfile
from ..config import APIConfig
from ..utils.validators import is_valid_eth_address


class EthereumClient(ChainClient):
    """
    Ethereum OSINT client using the Etherscan API V2.

    - Read-only OSINT (no private keys, no signing).
    - Fetches balance and recent transactions.
    - If normal tx list is empty, falls back to ERC-20 token transfers.
    """

    chain_name = "ethereum"

    def __init__(self, api_cfg: APIConfig) -> None:
        if not api_cfg.etherscan_api_key:
            raise ValueError("Missing CRYPTOHOUND_ETHERSCAN_API_KEY")
        self.api_key = api_cfg.etherscan_api_key
        # 🔁 V2 BASE URL
        self.base_url = "https://api.etherscan.io/v2/api"

    def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        # 🔁 V2 requires chainid
        params["apikey"] = self.api_key
        params.setdefault("chainid", 1)  # 1 = Ethereum mainnet

        with httpx.Client(timeout=10.0) as client:
            resp = client.get(self.base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected response from Etherscan")
        return data


    # -------------------------
    # Public API
    # -------------------------

    def get_address_profile(self, address: str) -> AddressProfile:
        if not is_valid_eth_address(address):
            raise ValueError(f"Invalid Ethereum address: {address}")

        # 1) Balance
        balance_resp = self._request(
            {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
            }
        )
        result = balance_resp.get("result")
        try:
            balance_eth = int(result) / 10**18 if result is not None else 0.0
        except (TypeError, ValueError):
            balance_eth = 0.0

        # 2) Transactions (normal or token transfers)
        txs = self.get_recent_transactions(address, limit=100)
        tx_count = len(txs)

        first_seen = txs[-1]["timeStamp"] if txs else None
        last_seen = txs[0]["timeStamp"] if txs else None

        return AddressProfile(
            address=address,
            chain=self.chain_name,
            balance=balance_eth,
            tx_count=tx_count,
            first_seen=first_seen,
            last_seen=last_seen,
            tags=[],
            notes=[],
        )

    def get_recent_transactions(
        self, address: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get recent transactions for an Ethereum address.

        1. Try normal transactions (txlist).
        2. If none found, try ERC-20 token transfers (tokentx).
        3. Normalise into a simple schema:
           { "hash", "from", "to", "value", "timeStamp" }
        """
        if not is_valid_eth_address(address):
            raise ValueError(f"Invalid Ethereum address: {address}")

        # ---- Try normal transactions first
        normal_txs = self._get_txlist(address, limit=limit)
        if normal_txs:
            return normal_txs

        # ---- Fall back to token transfers (many scam wallets are token-only)
        token_txs = self._get_tokentx(address, limit=limit)
        return token_txs

    # -------------------------
    # Internal helpers
    # -------------------------

    def _get_txlist(self, address: str, limit: int) -> list[dict[str, Any]]:
        resp = self._request(
            {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": limit,
                "sort": "desc",
            }
        )
        status = resp.get("status")
        message = resp.get("message")
        result = resp.get("result")

        # Etherscan returns status "1" + list on success.
        # On errors or no tx, status "0" and a string in result.
        if status != "1":
            raise RuntimeError(
                f"Etherscan txlist error (status={status}, message={message}, result={result})"
            )

        if not isinstance(result, list):
            raise RuntimeError(
                f"Etherscan txlist unexpected result type: {type(result).__name__}"
            )

        normalized: list[dict[str, Any]] = []
        for tx in result[:limit]:
            normalized.append(
                {
                    "hash": tx.get("hash", ""),
                    "from": tx.get("from", ""),
                    "to": tx.get("to", ""),
                    "value": tx.get("value", "0"),        # wei as string
                    "timeStamp": tx.get("timeStamp", ""),  # unix ts as string
                }
            )
        return normalized

    def _get_tokentx(self, address: str, limit: int) -> list[dict[str, Any]]:
        """
        Fallback to ERC-20 token transfers when there are no normal txs.

        NOTE:
        - value is in token units (not ETH), but for risk heuristics we only
          care that there *is* non-zero activity, not exact denomination.
        """
        resp = self._request(
            {
                "module": "account",
                "action": "tokentx",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": limit,
                "sort": "desc",
            }
        )
        status = resp.get("status")
        message = resp.get("message")
        result = resp.get("result")

        if status != "1":
            raise RuntimeError(
                f"Etherscan tokentx error (status={status}, message={message}, result={result})"
            )

        if not isinstance(result, list):
            raise RuntimeError(
                f"Etherscan tokentx unexpected result type: {type(result).__name__}"
            )

        normalized: list[dict[str, Any]] = []
        for tx in result[:limit]:
            normalized.append(
                {
                    "hash": tx.get("hash", ""),
                    "from": tx.get("from", ""),
                    "to": tx.get("to", ""),
                    "value": tx.get("value", "0"),
                    "timeStamp": tx.get("timeStamp", ""),
                }
            )
        return normalized
