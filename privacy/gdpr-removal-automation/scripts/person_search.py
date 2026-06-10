#!/usr/bin/env python3
"""
person_search.py — Discover which data brokers hold a person's data.

Uses web search (Brave/Exa/Serper) to find the individual on broker sites.
Outputs CSV: broker_name, url, found_identifier, search_query
"""

import csv
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: missing deps. Run: uv pip install beautifulsoup4 httpx")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────────────────────────

PERSON = {
    "name": "Thomas Schmoele",
    "email": "thomas.schmoele@icloud.com",
    "phone": "+49 176 12345678",  # mask/replace before sharing
    "city": "Munich",
    "country": "DE",
}

# Data brokers to check (name, search_url_pattern, found_pattern)
BROKERS = [
    ("Intelius", "https://www.intelius.com/people-search/{name}/", None),
    ("BeenVerified", "https://www.beenverified.com/people/{name}/", None),
    ("Spokeo", "https://www.spokeo.com/search?q={name}&layer=phone_claims", None),
    ("WhitePages", "https://www.whitepages.com/name/{name}/", None),
    ("Pipl", "https://pipl.com/search/?q={name}", None),
    ("Radaris", "https://radaris.com/p/people/{name}/", None),
    ("Instant Check Mate", "https://www.instantcheckmate.com/people/{name}/", None),
    ("PeopleFinder", "https://www.peoplefinder.com/search.php?name={name}", None),
    ("PublicRecordsNow", "https://www.publicrecordsnow.com/search?people={name}", None),
    ("USSearch", "https://www.ussearch.com/search/#person:{name}", None),
    ("ThatsThem", "https://thatsthem.com/name/{name}/", None),
    ("FamilyTreeNow", "https://www.familytreenow.com/search?search={name}", None),
    ("FastBackgroundCheck", "https://www.fastbackgroundcheck.com/search?q={name}", None),
    ("Truecaller", "https://www.truecaller.com/search/{name}/", None),
    ("Zabasearch", "https://www.zabasearch.com/people/{name}/", None),
    ("PeekYou", "https://www.peekyou.com/{name}/", None),
    ("USPhoneBook", "https://www.usphonebook.com/{name}/", None),
    ("FindPeopleSearch", "https://www.findpeoplesearch.com/{name}/", None),
    ("CallFinder", "https://www.callfinder.com/search?search={name}", None),
    ("ReversePhoneCheck", "https://www.reversephonecheck.com/phone/{phone}/", None),
]

SEARCH_ENGINE = os.environ.get("SEARCH_ENGINE", "brave")  # brave | exa | serper
SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY") or os.environ.get("EXA_API_KEY") or os.environ.get("SERPER_API_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

TIMEOUT = 10  # seconds per request
DELAY = 2.0   # seconds between requests (polite)


# ── Web Search (discover brokers listing the person) ─────────────────────────

def web_search(query: str) -> list[dict]:
    """Search the web and return list of result dicts with title, url, snippet."""
    if not SEARCH_API_KEY:
        print(f"  [WARN] No search API key set. Skipping web search for: {query}")
        return []

    try:
        if SEARCH_ENGINE == "brave":
            resp = httpx.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": 10},
                headers={"Accept": "application/json", "X-Subscription-Token": SEARCH_API_KEY},
                timeout=TIMEOUT,
            )
            results = resp.json().get("web", {}).get("results", [])
            return [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("description", "")} for r in results]
        elif SEARCH_ENGINE == "exa":
            resp = httpx.post(
                "https://api.exa.ai/search",
                json={"query": query, "numResults": 10},
                headers={"Authorization": f"Bearer {SEARCH_API_KEY}", "Content-Type": "application/json"},
                timeout=TIMEOUT,
            )
            results = resp.json().get("results", [])
            return [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("snippet", "")} for r in results]
        elif SEARCH_ENGINE == "serper":
            resp = httpx.post(
                "https://google.serper.dev/search",
                json={"q": query},
                headers={"X-API-KEY": SEARCH_API_KEY, "Content-Type": "application/json"},
                timeout=TIMEOUT,
            )
            items = resp.json().get("organic", [])
            return [{"title": i.get("title", ""), "url": i.get("link", ""), "snippet": i.get("snippet", "")} for i in items]
    except Exception as e:
        print(f"  [ERROR] Search failed: {e}")
    return []


def check_broker_page(broker_name: str, search_url: str, person: dict) -> dict | None:
    """
    Fetch broker search page and check if person's data appears.
    Returns result dict or None if not found.
    """
    name = person["name"]
    # Replace placeholders in URL
    url = search_url.replace("{name}", name.replace(" ", "-")).replace("{phone}", person.get("phone", ""))

    try:
        resp = httpx.get(url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text().lower()
        name_lower = name.lower()

        # Check if name appears in page (with some tolerance for variations)
        if name_lower.split()[0] in text or name_lower.split()[-1] in text:
            return {
                "broker": broker_name,
                "url": str(resp.url),
                "status_code": resp.status_code,
                "found": True,
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"  [ERROR] {broker_name}: {e}")
    return None


def search_brokers_web(person: dict) -> list[dict]:
    """Use web search to find which brokers list this person."""
    results = []
    name = person["name"]
    email = person.get("email", "")

    queries = [
        f'"{name}" data broker',
        f'"{name}" background check',
        f'"{name}" people search',
        f'"{email}" site:intelius.com OR site:spokeo.com OR site:whitepages.com',
        f'"{name}" site:radaris.com OR site:pipl.com',
    ]

    seen_urls = set()
    for query in queries:
        print(f"  Searching: {query}")
        hits = web_search(query)
        for hit in hits:
            url = hit["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            # Identify which broker this belongs to
            for broker_entry in BROKERS:
                broker_name = broker_entry[0]
                if broker_name.lower().replace(" ", "") in url.lower().replace(" ", ""):
                    results.append({
                        "broker": broker_name,
                        "url": url,
                        "title": hit.get("title", ""),
                        "snippet": hit.get("snippet", ""),
                        "found": True,
                        "timestamp": datetime.now().isoformat(),
                    })
                    break
        time.sleep(DELAY)

    return results


def check_brokers_direct(person: dict) -> list[dict]:
    """Directly check known broker search pages."""
    results = []
    for broker_name, search_url, _ in BROKERS:
        print(f"  Checking {broker_name}...")
        result = check_broker_page(broker_name, search_url, person)
        if result:
            results.append(result)
        time.sleep(DELAY)
    return results


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Find which data brokers hold a person's data")
    parser.add_argument("--name", default=PERSON["name"])
    parser.add_argument("--email", default=PERSON["email"])
    parser.add_argument("--phone", default=PERSON["phone"])
    parser.add_argument("--output", default="brokers_found.csv")
    parser.add_argument("--method", default="web", choices=["web", "direct", "both"])
    args = parser.parse_args()

    person = {"name": args.name, "email": args.email, "phone": args.phone}

    results = []
    if args.method in ("web", "both"):
        print("\n[1/2] Web search discovery...")
        results += search_brokers_web(person)

    if args.method in ("direct", "both"):
        print("\n[2/2] Direct broker checks...")
        results += check_brokers_direct(person)

    # Write CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["broker", "url", "title", "snippet", "found", "status_code", "timestamp"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✓ Found {len(results)} broker(s). Results saved to {output_path}")
    for r in results:
        print(f"  - {r['broker']}: {r['url']}")

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())