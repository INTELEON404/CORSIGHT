
# <div align="center">CORSIGHT — PROFESSIONAL EDITION v1.3</div>

<div align="center">
  <img src="https://github.com/INTELEON404/Template/blob/main/corsight.png" alt="CORSIGHT Logo" width="600px" />
</div>

```ascii                                            
 _____ _____ _____ _____ _____ _____ _____ _____ 
|     |     | __  |   __|     |   __|  |  |_   _|
|   --|  |  |    -|__   |-   -|  |  |     | | |  
|_____|_____|__|__|_____|_____|_____|__|__| |_|  
                                                 
```

**CORSIGHT v4.5** is a high‑performance, asynchronous CORS misconfiguration scanner built for the **2026 offensive security landscape**. It combines AI‑driven origin mutation with real browser validation to uncover exploitable flaws that traditional scanners miss.

> [!IMPORTANT]
> **Ethical Use Only:** This tool is for authorized security testing only. Unauthorized use may violate the Computer Fraud and Abuse Act (CFAA) and other applicable laws.

---

## ✨ What’s New in v1.3

- **🛡️ SameSite Contextual Testing** – Evaluates `SameSite=Lax` and `Strict` cookie attributes to determine real‑world exploitability.
- **🤖 AI Mutation 2.0** – Leverages local LLM patterns to generate sophisticated “look‑alike” origins (e.g., `target-api.com.attacker.sh`).
- **⚙️ CI/CD Integration** – New `--json-pipe` mode for seamless automation in GitHub Actions, Jenkins, and other pipelines.
- **🌐 Headless Playwright Pro** – Validates vulnerabilities in modern SPAs and React‑based authenticated states.
- **📡 Stealth Mode** – Adaptive request delays (`--adaptive-delay`) and randomized fingerprints to bypass rate limiting and WAFs.

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/INTELEON404/CORSIGHT.git
cd CORSIGHT
pip install -r requirements.txt
playwright install chromium    
```

### One‑Liner Auto‑Pilot Scan

```bash
python corsight.py -i targets.txt -t 250 --subdomain-brute --validate --poc --report -o 2026_recon
```

---

## ⚙️ Core CLI Options

| Option | Description |
|--------|-------------|
| `--subdomain-brute` | Discover hidden subdomains before scanning. |
| `--samesite-check` | Validate SameSite cookie protections. |
| `--validate` | Confirm vulnerabilities via a real browser “mock exploit”. |
| `--poc` | Generate a standalone `.html` proof‑of‑concept. |
| `--report` | Output a formatted `.md` report (Bugcrowd/HackerOne ready). |
| `--json-pipe` | Emit JSON for CI/CD integration. |

> **Advanced users:** Additional flags like `--stealth`, `--adaptive-delay`, and concurrency control (`-t`) are available – run `python corsight.py -h` for the full list.

---

## 📊 2026 Severity Matrix

| Severity | Attack Scenario |
|----------|------------------|
| **CRITICAL** | Sensitive data access (e.g., `/api/user/token`) with `Credentials: true` and browser validation. |
| **HIGH** | Reflection on subdomains leading to PII exposure. |
| **MEDIUM** | Origin reflection on low‑impact endpoints or paths without session cookies. |
| **LOW** | `null` origin misconfigurations on non‑sensitive public assets. |


---

## 👤 Author & Support

**INTELEON404** – Offensive Security Researcher

- GitHub: [@INTELEON404](https://github.com/INTELEON404)
- X (Twitter): [@INTELEON404](https://twitter.com/INTELEON404)

Distributed under the **MIT License**.

> *“Automate the recon, focus on the exploit.”*
