#!/usr/bin/env python3
"""                                            
 _____ _____ _____ _____ _____ _____ _____ _____ 
|     |     | __  |   __|     |   __|  |  |_   _|
|   --|  |  |    -|__   |-   -|  |  |     | | |  
|_____|_____|__|__|_____|_____|_____|__|__| |_|  
                                                 
              CORSIGHT • v1.2 • CORS SCANNER
"""

import argparse
import asyncio
import json
import os
import random
import string
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse

# Ultra-safe install
def install(p):
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", p], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Force install only what we need
try:
    import aiohttp
    from termcolor import colored, cprint
    from tqdm import tqdm
except ImportError:
    print(colored("Installing aiohttp + termcolor + tqdm...", "yellow"))
    install("aiohttp termcolor tqdm")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ==================== BANNER ====================
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(colored(r"""
   █▀▀ █▀█ █▀▄ █▀▀ ▀█▀ █▀▀ █ █ ▀█▀   
   █░░ █░█ █▀▄ ▀▀█ ░█░ █░█ █▀█ ░█░   
   ▀▀▀ ▀▀▀ ▀░▀ ▀▀▀ ▀▀▀ ▀▀▀ ▀ ▀ ░▀░
               
            CORSIGHT v1.2 
    """, "cyan", attrs=["bold"]))
    print(colored("              BE HUNT • CLAIM BOUNTY ", "magenta", attrs=["bold"]))
    print(colored("                   by INTELEON404\n", "white"))
    print(colored("="*88, "grey"))

# ==================== SOUND ====================
def beep():
    print('\a', end='', flush=True)
    if os.name == 'nt':
        import winsound
        try: winsound.Beep(3000, 400)
        except: pass

# ==================== ORIGINS ====================
def gen_origins(domain):
    origins = ["https://evil.com", "null", "https://attacker.com", "http://localhost"]
    for _ in range(8):
        r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        origins.append(f"https://{r}.{domain}")
    return origins

# ==================== PRETTY ====================
def jackpot(finding):
    url = finding["url"]
    origin = finding["origin"]
    acao = finding["acao"]
    acac = finding["acac"]
    sev = finding["severity"]

    badge = "HIGH → EXPLOITABLE!" if sev == "HIGH" else "MEDIUM → DANGEROUS"
    color = "red" if sev == "HIGH" else "yellow"

    print(colored("\nJACKPOT! CORS VULN!", "white", "on_red", attrs=["bold"]))
    print(colored(f"  url    → {url}", "cyan"))
    print(colored(f"  origin → {origin}", "yellow"))
    print(colored(f"  ACAO   → {acao}", "green"))
    print(colored(f"  ACAC   → {acac}", "red" if acac == "true" else "white"))
    print(colored(f"  {badge}", color, attrs=["bold"]))
    beep()

# ==================== TEST URL ====================
async def test(session, url, origin):
    headers = {"Origin": origin, "User-Agent": "CORSIGHT/6.0"}
    try:
        async with session.get(url, headers=headers, ssl=False, timeout=8) as r:
            acao = r.headers.get("Access-Control-Allow-Origin", "").strip()
            acac = r.headers.get("Access-Control-Allow-Credentials", "").lower()

            if (acao == origin and acac == "true") or (acao == "*" and acac == "true"):
                return {"url": url, "origin": origin, "acao": acao, "acac": acac, "severity": "HIGH"}
            elif acao == origin:
                return {"url": url, "origin": origin, "acao": acao, "acac": acac, "severity": "MEDIUM"}
    except:
        pass
    return None

# ==================== SCAN ONE TARGET ====================
async def scan_target(target, paths):
    target = target.strip()
    if not target.startswith("http"):
        target = "https://" + target
    target = target.rstrip("/") + "/"

    domain = urlparse(target).netloc.split(":")[0]
    origins = gen_origins(domain)

    timeout = aiohttp.ClientTimeout(total=10)
    results = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []
        for path in paths:
            url = urljoin(target, path.lstrip("/"))
            for origin in origins:
                tasks.append(test(session, url, origin))

        # FIXED: Use regular loop + manual tqdm
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                results.append(result)
                jackpot(result)
    return results

# ==================== MAIN ====================
async def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", "--url", help="Single URL")
    group.add_argument("-i", "--input", help="File with URLs")
    parser.add_argument("-p", "--paths", default="/,/api,/v1,/graphql")
    parser.add_argument("-t", "--threads", type=int, default=200)
    parser.add_argument("-o", "--output", help="Output prefix")

    args = parser.parse_args()
    banner()

    # Load targets
    if args.url:
        targets = [args.url]
    else:
        if not os.path.exists(args.input):
            cprint("File not found!", "red")
            return
        with open(args.input) as f:
            targets = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    paths = [p.strip() for p in args.paths.split(",")]
    cprint(f"Loaded {len(targets)} targets → Starting lightning scan...", "green")

    all_results = []
    semaphore = asyncio.Semaphore(args.threads)

    async def bounded_scan(t):
        async with semaphore:
            return await scan_target(t, paths)

    # FINAL FIX: Manual progress bar
    tasks = [bounded_scan(t) for t in targets]
    for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), colour="cyan", desc="HUNTING"):
        result = await future
        all_results.extend(result)

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = args.output or f"CORSIGHT_{ts}"
    with open(f"{name}.json", "w") as f:
        json.dump(all_results, f, indent=2)
    cprint(f"\nSAVED → {name}.json", "green", attrs=["bold"])

    high = len([r for r in all_results if r["severity"] == "HIGH"])
    if high:
        cprint(f"\nJACKPOT! {high} EXPLOITABLE CORS → $10K+ BOUNTY!", "red", attrs=["bold", "blink"])
    else:
        cprint("\nNo critical CORS found.", "yellow")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        cprint("\nStopped.", "yellow")