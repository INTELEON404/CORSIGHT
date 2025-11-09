# CORSIGHT v1.0 — HUNTER EDITION

```ascii
█▀▀ █▀█ █▀▄ █▀▀ ▀█▀ █▀▀ █ █ ▀█▀  
█░░ █░█ █▀▄ ▀▀█ ░█░ █░█ █▀█ ░█░
▀▀▀ ▀▀▀ ▀░▀ ▀▀▀ ▀▀▀ ▀▀▀ ▀ ▀ ░▀░
```

---

### One Command. Focused Recon.

```bash
python3 corsight.py -i targets.txt -t 500 -o konghq_hunt
```

**That's it.**

---

### Summary

CORSIGHT is a high-performance CORS misconfiguration scanner built for pentesters and security researchers. It probes Access-Control headers across many origins and paths, scores findings, and saves machine-friendly reports. Use only on targets you have explicit permission to test.

---

### Features (CLI MODE)

* Fast, asynchronous scanning optimized for high concurrency
* Smart origin generation (including subdomain-origin permutations)
* Severity scoring (INFO / LOW / MEDIUM / HIGH)
* Real-time progress bar and summary output
* JSON + clean TXT export
* Options tuned for Kali, Termux, Linux, macOS
* Configurable concurrency (use responsibly)

> **Security & ethics:** Always have written authorization before scanning third-party domains. Scanning at very high concurrency can affect target availability and may be detected by defensive systems.

---

### Install & Run

```bash
git clone https://github.com/INTELEON404/CORSIGHT.git && cd CORSIGHT
python3 corsight.py -i targets.txt
```

**Or (one-liner):**

```bash
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/INTELEON404/CORSIGHT/main/corsight.py)" -i targets.txt -t 1000
```

> Note: using extreme concurrency (≥500) may require tuning system limits (ulimit) and network capacity. Lower the thread count if you see errors or network issues.

---

### CLI Options

```
-i, --input     targets file (required)
-u, --url       single target (example: https://example.com)
-p, --paths     comma-separated paths to test (default: /,/api,/v1,/graphql,/admin)
-t, --threads   concurrency (default: 200, max: 1000)
-o, --output    output prefix (e.g. -o kong -> kong.json + kong.txt)
--origins       custom comma-separated origins to test (overrides defaults)
--timeout       request timeout seconds (default: 15)
--preflight     include OPTIONS preflight checks (optional)
```

---

### Examples

```bash
# Normal hunt
python3 corsight.py -i domains.txt

# Higher concurrency
python3 corsight.py -i biglist.txt -t 400

# Kong HQ special
python3 corsight.py -i konghq.txt -t 600 -o KONGHQ_JACKPOT_2025
```

---

### Output Example

```yaml
JACKPOT! CORS VULN!
  url     → https://2293a63582c1.us.portal.konghq.tech/api
  origin  → https://abc123xyz.konghq.tech
  ACAO    → https://abc123xyz.konghq.tech
  ACAC    → true
  HIGH    → EXPLOITABLE!
```

Files created:

```
KONGHQ_JACKPOT_2025.json
KONGHQ_JACKPOT_2025.txt
```

---

### Pro Tips

```bash
# Aggregate lists then scan
find . -name "*.txt" -exec cat {} + | sort -u > all.txt
python3 corsight.py -i all.txt -t 350 -o FULL_HUNT

# Auto-recon + scan
subfinder -dL domains.txt -all -o subs.txt
python3 corsight.py -i subs.txt -t 300
```

* Start with moderate concurrency (50–200) and scale up gradually.
* If you get many network errors, reduce threads or increase timeout.
* Consider adding `--preflight` to test server responses to OPTIONS when relevant.

---

### Changelog (v1.0)

* Initial public release: async scanner, scoring, JSON/TXT export, progress bar.
* Hunter Edition tweaks: smarter origin generation and speed optimizations.

---

### License

MIT — see LICENSE file in repo.

---

### Author

**INTELEON404** — THE PENTESTER • BUG HUNTER

> "Real hackers don't click. They type."

**GitHub:** github.com/INTELEON404
**X:** @INTELEON404

---

### Responsible Use

This tool is for authorized security testing and research. Do not use CORSIGHT to target systems without permission. The author and distributors are not responsible for misuse.
