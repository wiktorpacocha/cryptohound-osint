import re

# Very simple pattern check for Ethereum addresses: 0x + 40 hex chars
ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def is_valid_eth_address(addr: str) -> bool:
    return bool(ETH_ADDRESS_RE.match(addr))
