from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AddressProfile:
    address: str
    chain: str
    balance: float
    tx_count: int
    first_seen: str | None
    last_seen: str | None
    tags: list[str]
    notes: list[str]


class ChainClient(ABC):
    chain_name: str

    @abstractmethod
    def get_address_profile(self, address: str) -> AddressProfile:
        ...

    @abstractmethod
    def get_recent_transactions(
        self, address: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        ...
