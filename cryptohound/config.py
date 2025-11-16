import os
from dataclasses import dataclass


@dataclass
class APIConfig:
    etherscan_api_key: str | None = None


def load_config() -> APIConfig:
    """
    Load configuration from environment variables.
    No secrets are stored in code or git.
    """
    return APIConfig(
        etherscan_api_key=os.getenv("CRYPTOHOUND_ETHERSCAN_API_KEY"),
    )
