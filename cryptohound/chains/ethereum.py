from typing import Any
import httpx

from .base import ChainClient, AddressProfile
from ..config import APIConfig
from ..utils.validators import is_valid_eth_address


class EthereumClient(ChainClient):
    chain_name = "ethereum"

    def __init__(self, api_cfg: APIConfig) -> None:
        if not api_cfg.etherscan_api_key:
            raise ValueError("Missing CRYPTOHOUND_ETHERSCAN_API_KEY")
        self.api_key = api_cfg.etherscan_api_key
        self.base_url = "https://api.etherscan.io/api"

    def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        params["apikey"] = self.api_key
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(self.base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected response from Etherscan")
        return data

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

        # 2) Recent transactions (for basic stats)
        txs = self.get_recent_transactions(address, limit=20)
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
        if not is_valid_eth_address(address):
            raise ValueError(f"Invalid Ethereum address: {address}")

        tx_resp = self._request(
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
        result = tx_resp.get("result")
        if not isinstance(result, list):
            return []
        return result
