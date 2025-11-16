from typing import Any
import httpx

from .base import ChainClient, AddressProfile
from ..config import APIConfig
from ..utils.validators import is_valid_btc_address


class BitcoinClient(ChainClient):
    """
    Bitcoin OSINT client using the Blockstream public explorer API.

    NOTE:
    - Read-only. We only fetch public blockchain data (OSINT).
    - No private keys. No signing. No wallet functionality.
    """

    chain_name = "bitcoin"

    def __init__(self, api_cfg: APIConfig) -> None:
        # api_cfg currently unused, but kept for consistency with other clients.
        self.base_url = "https://blockstream.info/api"

    def _request(self, path: str) -> Any:
        """
        Generic GET request wrapper. Returns parsed JSON.
        """
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    def get_address_profile(self, address: str) -> AddressProfile:
        if not is_valid_btc_address(address):
            raise ValueError(f"Invalid Bitcoin address format: {address}")

        # GET /address/{address}
        data = self._request(f"/address/{address}")
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected response type for address profile")

        chain_stats = data.get("chain_stats", {}) or {}
        funded = chain_stats.get("funded_txo_sum", 0) or 0
        spent = chain_stats.get("spent_txo_sum", 0) or 0
        tx_count = chain_stats.get("tx_count", 0) or 0

        try:
            balance_btc = (int(funded) - int(spent)) / 10**8
        except (TypeError, ValueError):
            balance_btc = 0.0

        # We could fetch txs here to derive first/last seen, but we keep it simple for now.
        return AddressProfile(
            address=address,
            chain=self.chain_name,
            balance=balance_btc,
            tx_count=tx_count,
            first_seen=None,
            last_seen=None,
            tags=[],
            notes=[],
        )

    def get_recent_transactions(
        self, address: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Return a normalized list of recent transactions for the address.

        We map Blockstream's tx format into a simplified, Etherscan-like schema:
        {
          "hash": txid,
          "from": first_input_address,
          "to": first_output_address,
          "value": value_in_satoshis (as string),
          "timeStamp": block_time (unix timestamp) or ""
        }

        NOTE:
        - For multi-input/multi-output transactions, this is a simplification.
        - This is meant for OSINT & overview, not exact accounting.
        """
        if not is_valid_btc_address(address):
            raise ValueError(f"Invalid Bitcoin address format: {address}")

        data = self._request(f"/address/{address}/txs")
        if not isinstance(data, list):
            return []

        txs = data[:limit]
        normalized: list[dict[str, Any]] = []

        for tx in txs:
            txid = tx.get("txid", "")
            status = tx.get("status", {}) or {}
            block_time = status.get("block_time")

            vin = tx.get("vin", []) or []
            vout = tx.get("vout", []) or []

            from_addr = ""
            if vin:
                prevout = vin[0].get("prevout") or {}
                from_addr = prevout.get("scriptpubkey_address", "") or ""

            to_addr = ""
            value_sats = 0
            if vout:
                vout0 = vout[0] or {}
                to_addr = vout0.get("scriptpubkey_address", "") or ""
                value_sats = vout0.get("value", 0) or 0

            normalized.append(
                {
                    "hash": txid,
                    "from": from_addr,
                    "to": to_addr,
                    "value": str(value_sats),          # satoshis as string
                    "timeStamp": str(block_time or ""), # unix timestamp or ""
                }
            )

        return normalized
