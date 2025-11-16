# 🐺 CryptoHound OSINT  
### Open-Source Crypto Fraud Investigation Toolkit (ETH + BTC)

CryptoHound is a **lightweight, privacy-first blockchain OSINT toolkit** for investigators, analysts, and security professionals.  
It performs **risk scoring, address profiling, and transaction intelligence** across multiple chains — all **locally** and without tracking.

---

## 🚀 Features (v0.2.0)

### 🔍 **Cross-Chain Address Profiling**
- **Ethereum** (Etherscan API V2)
- **Bitcoin** (BlockCypher)

### 🧠 **Smart Risk Engine (0–100)**
Powered by multi-factor heuristics:
- High transaction volume
- Dusting & spam patterns  
- Burst activity analysis  
- Multiple senders & recipients  
- Suspicious flow patterns  
- Zero-activity anomaly detection  

### 📊 **Exportable Reports (3 Formats)**
- **TXT** – Summary report  
- **HTML** – Clean professional report  
- **CSV** – Transaction dataset  

### 🧠 **Auto Chain Detection**

Just pass the address — CryptoHound identifies the blockchain automatically.

### 🔐 **Local, Private, Secure**
No accounts.  
No cloud.  
No wallets.  
No tracking.  
Zero private key code.

---

## 📦 Installation

```bash
git clone https://github.com/wiktorpacocha/cryptohound-osint.git
cd cryptohound-osint
python -m venv .venv
.\.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

---

## 🐍 Usage

### Test CLI

```bash
python -m cryptohound.cli hello
```

### Generate a full OSINT report

```bash
python -m cryptohound.cli report ADDRESS_HERE \
  -d output_folder \
  -n report_name
```

**Example (BTC):**

```bash
python -m cryptohound.cli report 1Ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55 `
  -d examples/btc_scam `
  -n btc_scam
```

Generates:

- `btc_scam.txt`
- `btc_scam.html`
- `btc_scam_txs.csv`

---

## 📁 Example Reports (BTC + ETH)

CryptoHound includes real-world high-risk activity examples under `/examples`.

### **📌 BTC Scam Example**
`examples/btc_scam/btc_scam.html`

Highlights:
- 1000+ transactions  
- Dusting  
- Burst activity  
- High risk score  

### **📌 ETH High-Risk Example**
`examples/eth_scam/eth_scam.html`

Highlights:
- High balance  
- Multiple senders  
- Dusting  
- Burst activity  
- Risk score 48/100  

These verify that CryptoHound is fully operational.

---

## 🔒 Privacy & Security

CryptoHound:
- Runs entirely **locally**, except for API calls  
- Stores **no data or history**  
- Requires **no account**  
- Performs **read-only** chain queries  
- Includes **no private key logic**

Designed for OSINT professionals requiring operational security.

---

## 🗺️ Roadmap

Upcoming features:

- 🪓 Phishing / honeypot detection  
- 🧬 Behavioral ML scoring (Pro)  
- 🎛️ More chains (BSC, Polygon, LTC…)  
- 📈 Graph visualization (Pro)  
- 📎 PDF report generation  
- 🔗 Exchange / entity attribution  
- 🖥️ Desktop app (Pro)  

---

## ⚖️ License

CryptoHound OSINT is released under the **MIT License**.

---

## ⚠️ Disclaimer

CryptoHound uses **open-source intelligence (OSINT)** only.  
It does **not** guarantee accuracy or completeness.  
It is **not financial advice** or forensic-grade investigation.  
Use responsibly and at your own risk.

---

## 🤝 Contributing

Pull requests, ideas, and improvements are welcome.  
Open an issue if you spot a bug or want a new feature.

---

## ⭐ Support the Project

If you find value in CryptoHound:

- ⭐ Star the repo  
- 👥 Share with your community  
- 🐺 Follow updates — **Pro version coming soon**  
