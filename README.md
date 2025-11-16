# CryptoHound OSINT

CryptoHound is a local, open-source **crypto fraud OSINT toolkit**.

Current features (v0.1.0):

- Ethereum address profiling using public APIs (Etherscan-style)
- Simple risk heuristics (e.g. only-incoming wallets)
- Text report export for investigations (`report.txt`)

## Usage

```bash
python -m venv .venv
.\.venv\Scripts\activate        # on Windows

pip install -r requirements.txt

# Show welcome
python -m cryptohound.cli

# Test command
python -m cryptohound.cli hello

# Profile an Ethereum address
python -m cryptohound.cli profile-address 0xYOURADDRESS -o report.txt
```

## Disclaimer

CryptoHound uses **open-source intelligence (OSINT)** only.  
It does **not** guarantee completeness or accuracy.  
It is **not** financial advice or forensic analysis.  
Use at your own risk.
