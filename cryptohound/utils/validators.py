import re

# Very simple pattern check for Ethereum-style addresses: 0x + 40 hex chars
ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

# Basic pattern check for legacy & P2SH/P2PKH BTC addresses starting with 1 or 3.
# This does NOT fully validate checksums.
BTC_LEGACY_RE = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")

# Basic pattern check for Bech32 (bc1...) Bitcoin addresses.
BTC_BECH32_RE = re.compile(r"^bc1[ac-hj-np-z02-9]{11,71}$", re.IGNORECASE)


def is_valid_eth_address(addr: str) -> bool:
    """
    Basic Ethereum-style address format check.
    This pattern is also valid for EVM chains like BSC, Polygon, etc.
    """
    return bool(ETH_ADDRESS_RE.match(addr))


def is_valid_btc_address(addr: str) -> bool:
    """
    Basic Bitcoin address format check.

    NOTE:
    - This does not fully validate checksums.
    - It supports common legacy (1..., 3...) and Bech32 (bc1...) formats.
    """
    if BTC_LEGACY_RE.match(addr):
        return True
    if BTC_BECH32_RE.match(addr):
        return True
    return False


def detect_chain_from_address(addr: str) -> str | None:
    """
    Very simple chain detection based on address format.

    Returns:
        "btc"  -> if address looks like Bitcoin
        "eth"  -> if address looks like Ethereum-style (0x...)
        None   -> if cannot detect confidently
    """
    # Normalize just in case
    addr = addr.strip()

    if is_valid_btc_address(addr):
        return "btc"

    if is_valid_eth_address(addr):
        # Could be Ethereum or another EVM chain; for now we default to "eth".
        return "eth"

    return None
