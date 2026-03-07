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
DEFAULT_USER_AGENT = "CORSIGHT/1.4 (Professional Edition)"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=20, connect=5)
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
|   --|  |  |    -|__   |-   -|  |  |     | | |   CORSIGHT v1.4 
|_____|_____|__|__|_____|_____|_____|__|__| |_|  
    """, "cyan", attrs=["bold"]))
    print(colored("              PROFESSIONAL CORS AUDIT ENGINE", "magenta", attrs=["bold"]))
    print(colored("               Maintainer: INTELEON404", "white"))
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
    random_sub = ''.join(random.choices(string.ascii_lowercase, k=15)) + "." + domain
    loop = asyncio.get_running_loop()
    try:
        await loop.getaddrinfo(random_sub, None)
        return True
    except:
        return False

def get_severity(url: str, is_exploitable: bool, credentials_allowed: bool) -> str:
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

# ---------- AI Mutation Engine ----------
def generate_origins(domain: str, include_null: bool = True) -> List[str]:
    mutations = set()
    def rand_sub(): return ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(5, 10)))
    
    mutations.add(f"https://{domain}.evil.com")
    mutations.add(f"https://{domain}.attacker.com")
    mutations.add(f"https://evil{domain}.com")
    mutations.add(f"https://{domain}-evil.com")
    mutations.add(f"https://{domain}.local")
    
    for attacker in ATTACKER_DOMAINS:
        mutations.add(f"https://{domain}.com.{attacker}")
        mutations.add(f"https://{attacker}/{domain}")
        mutations.add(f"https://{attacker}?{domain}")
        mutations.add(f"https://{attacker}@{domain}.com")
        mutations.add(f"https://{domain}%00.{attacker}")
        mutations.add(f"https://{domain}.{attacker}.{rand_sub()}.com")
    
    mutations.add(f"https://{rand_sub()}{domain}.com")
    
    for _ in range(2):
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

# ---------- Core Logic ----------
async def fetch_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    origin: Optional[str] = None,
    method: str = "GET",
    preflight: bool = False,
    insecure: bool = False,
) -> Optional[Tuple[int, Dict[str, str], bytes]]:
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    if origin:
        headers["Origin"] = origin
    
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
        except Exception as e:
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_BACKOFF * (attempt + 1))
    return None

def is_vulnerable_response(status: int, headers: Dict[str, str], body: bytes, origin: str, baseline_headers: Optional[Dict[str, str]] = None, preflight: bool = False) -> Tuple[bool, str]:
    if status not in REQUIRED_STATUS_CODES and status != 204: 
        return False, f"status {status}"

    acao = headers.get("access-control-allow-origin", "").strip()
    acac = headers.get("access-control-allow-credentials", "").lower()

    if baseline_headers:
        b_acao = baseline_headers.get("access-control-allow-origin", "").strip()
        b_acac = baseline_headers.get("access-control-allow-credentials", "").lower()
        if b_acao == acao and b_acac == acac and acao != origin:
            return False, "Static CORS policy"

    if acao == "*" and acac == "true":
        return False, "Wildcard credentials blocked by browser"
    
    if acao != origin:
        return False, "Reflection mismatch"

    if acac != "true":
        return False, "Credentials forbidden"

    if preflight:
        acam = headers.get("access-control-allow-methods", "").upper()
        if "GET" not in acam and "*" not in acam:
            return False, "Preflight method failure"

    if is_trivial_body(body) and status != 204:
        return False, "Empty content"

    return True, "Exploitable"

async def browser_validate(url: str, origin: str) -> bool:
    if not PLAYWRIGHT_AVAILABLE:
        return True 

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

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
            
            start_wait = time.time()
            result = False
            while time.time() - start_wait < 5.0:
                result = await page.evaluate("window.readSuccess")
                if result: break
                await asyncio.sleep(0.5)
                
            await browser.close()
            return bool(result)
    except Exception:
        return False

# ---------- UI & Presentation ----------
class Spinner:
    def __init__(self, stats):
        self.stats = stats
        self.chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.idx = 0
        self.active = False
        self._task = None

    async def spin(self):
        while self.active:
            char = colored(self.chars[self.idx % len(self.chars)], "cyan")
            findings_val = str(self.stats['findings_count'])
            findings_color = "red" if self.stats['findings_count'] > 0 else "white"
            
            line = (
                f"\r{colored('➜', 'blue')} {colored('Audit Phase:', 'white')} {char} "
                f"[{colored('Requests:', 'grey')} {self.stats['requests_sent']} | "
                f"{colored('Healthy:', 'grey')} {self.stats['requests_success']} | "
                f"{colored('Findings:', 'grey')} {colored(findings_val, findings_color, attrs=['bold'])}]"
            )
            
            sys.stdout.write(line)
            sys.stdout.flush()
            self.idx += 1
            await asyncio.sleep(0.1)

    def start(self):
        self.active = True
        self._task = asyncio.create_task(self.spin())

    async def stop(self):
        self.active = False
        if self._task:
            try: await self._task
            except asyncio.CancelledError: pass
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.flush()

    def clear(self):
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.flush()

# ---------- Worker Logic ----------
class ScanWorker:
    def __init__(self, session, global_sem, domain_sems, stats, findings, args, spinner):
        self.session = session
        self.global_sem = global_sem
        self.domain_sems = domain_sems
        self.stats = stats
        self.findings = findings
        self.args = args
        self.spinner = spinner
        self.queue = asyncio.Queue(maxsize=max(args.threads * 200, 5000)) 
        self.stats_lock = asyncio.Lock()
        self.findings_lock = asyncio.Lock()
        self.seen_findings = set()
        self.baselines = {}

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
        domain_sem = self.domain_sems.get(domain, asyncio.Semaphore(DEFAULT_PER_DOMAIN_CONCURRENCY))
        self.domain_sems[domain] = domain_sem

        if url not in self.baselines:
            async with self.global_sem, domain_sem:
                res = await fetch_with_retry(self.session, url, origin=None, method=method, preflight=False, insecure=self.args.insecure)
                if res: self.baselines[url] = res

        baseline = self.baselines.get(url)
        baseline_headers = baseline[1] if baseline else None

        async with self.global_sem, domain_sem:
            await asyncio.sleep(self.args.delay)
            result = await fetch_with_retry(self.session, url, origin, method, preflight, self.args.insecure)

        async with self.stats_lock:
            self.stats["requests_sent"] += 1
            if result is None:
                self.stats["requests_failed"] += 1
                return
            self.stats["requests_success"] += 1

        status, headers, body = result
        is_vuln, reason = is_vulnerable_response(status, headers, body, origin, baseline_headers, preflight)
        if not is_vuln: return

        browser_ok = False
        if self.args.validate:
            browser_ok = await browser_validate(url, origin)
            if not browser_ok: return

        finding_key = (url, origin, method, preflight)
        async with self.findings_lock:
            if finding_key not in self.seen_findings:
                self.seen_findings.add(finding_key)
                
                acao = headers.get("access-control-allow-origin", "None")
                acac = headers.get("access-control-allow-credentials", "False")
                sev_label = get_severity(url, browser_ok or not self.args.validate, acac.lower() == "true")
                is_readable = "Yes" if not is_trivial_body(body) else "No"

                self.spinner.clear()
                label_color = "red" if sev_label in ["CRITICAL", "HIGH"] else "yellow"
                cprint(f"\n[!] FINDING: {sev_label} VULNERABILITY", label_color, attrs=["bold"])
                print(f" {'Target URL':<12}: {url}")
                print(f" {'Method':<12}: {method}")
                print(f" {'Origin':<12}: {origin}")
                print(f" {'ACAO':<12}: {acao}")
                print(f" {'ACAC':<12}: {acac}")
                print(f" {'Evidence':<12}: {truncate_body_preview(body)}")
                print("-" * 50)

                self.findings.append({
                    "url": url, "origin": origin, "method": method, "preflight": preflight,
                    "status": status, "acao": acao, "acac": acac,
                    "body_preview": truncate_body_preview(body), "severity": sev_label,
                    "is_readable": is_readable, 
                    "timestamp": datetime.now().isoformat()
                })
                self.stats["findings_count"] = len(self.findings)
                if self.args.beep and sev_label in ["CRITICAL", "HIGH"]: beep()

# ---------- Main Controller ----------
async def run_scanner(targets, paths, args):
    stats = {"requests_sent": 0, "requests_failed": 0, "requests_success": 0, "findings_count": 0}
    findings = []
    global_sem = asyncio.Semaphore(args.threads)
    domain_sems = {}

    headers_dict = {}
    if args.headers:
        for h in args.headers.split(","):
            if ":" in h:
                k, v = h.split(":", 1)
                headers_dict[k.strip()] = v.strip()

    connector = aiohttp.TCPConnector(limit=args.threads, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector, headers=headers_dict) as session:
        spinner = Spinner(stats)
        spinner.start()
        
        worker = ScanWorker(session, global_sem, domain_sems, stats, findings, args, spinner)
        num_workers = min(args.threads, 40)
        workers = [asyncio.create_task(worker.worker_loop()) for _ in range(num_workers)]

        for target in targets:
            if not target.startswith("http"): target = "https://" + target
            domain = normalize_domain(target)
            origins = generate_origins(domain, include_null=not args.no_null_origin)
            if args.max_origins: origins = origins[:args.max_origins]
            
            for path in paths:
                url = urljoin(target, path.lstrip("/"))
                for origin in origins:
                    await worker.queue.put((url, origin, "GET", False))
                    await worker.queue.put((url, origin, "GET", True))

        await worker.queue.join()
        for _ in range(num_workers): await worker.queue.put(None)
        await asyncio.gather(*workers)
        await spinner.stop()

    return findings, stats

async def main() -> None:
    parser = argparse.ArgumentParser(description="CORSIGHT Professional v4.5")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", help="Target URL")
    group.add_argument("-i", "--input", help="Target list")
    parser.add_argument("-p", "--paths", default="/,/api,/v1,/userinfo,/account", help="Audit paths")
    parser.add_argument("-t", "--threads", type=int, default=50)
    parser.add_argument("-d", "--delay", type=float, default=0.0)
    parser.add_argument("-H", "--headers", help="Custom headers (Key:Value,Key:Value)")
    parser.add_argument("--cookies", help="Auth cookies")
    parser.add_argument("--max-origins", type=int)
    parser.add_argument("--insecure", action="store_true")
    parser.add_argument("--no-null-origin", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--beep", action="store_true")
    parser.add_argument("--output", help="Output dir")
    args = parser.parse_args()

    show_banner()
    if args.url: targets = [args.url]
    else:
        try:
            with open(args.input) as f: targets = [l.strip() for l in f if l.strip()]
        except: return print(colored("[!] Target file error", "red"))

    paths = [p.strip() for p in args.paths.split(",")]
    start_time = time.time()
    findings, stats = await run_scanner(targets, paths, args)
    
    # Final Summary Table
    duration = time.time() - start_time
    print(colored("\n" + "="*30 + " AUDIT SUMMARY " + "="*30, "cyan"))
    print(f" {'Metric':<25} | {'Value':<10}")
    print("-" * 40)
    print(f" {'Audit Duration':<25} | {duration:.2f}s")
    print(f" {'Total Requests':<25} | {stats['requests_sent']}")
    print(f" {'Vulnerabilities':<25} | {len(findings)}")
    print("-" * 40)
    
    if findings:
        out_dir = args.output or f"results_{datetime.now().strftime('%m%d_%H%M')}"
        os.makedirs(out_dir, exist_ok=True)
        if args.json:
            with open(os.path.join(out_dir, "report.json"), "w") as f: json.dump(findings, f, indent=4)
        cprint(f"[+] Detailed findings exported to: {out_dir}", "green")

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: cprint("\n[!] Audit interrupted.", "yellow")
