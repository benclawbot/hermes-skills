#!/usr/bin/env python3
"""
optout_discovery.py — Find opt-out URLs for data brokers.

Reads broker list from person_search.py output, discovers opt-out pages,
outputs CSV with broker,optout_url,method,verified.
"""

import csv
import json
import re
import sys
import time
from pathlib import Path

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: missing deps. Run: uv pip install beautifulsoup4 httpx")
    sys.exit(1)


# ── Known opt-out URL patterns (maintained list) ──────────────────────────
# Format: (broker_name, optout_url_pattern, method, requires_identity)
OPT_OUT_URLS = {
    "Intelius": ("https://www.intelius.com/opt-out/", "form", True),
    "BeenVerified": ("https://www.beenverified.com/privacy/opt-out", "form", True),
    "Spokeo": ("https://www.spokeo.com/opt-out", "form", True),
    "WhitePages": ("https://www.whitepages.com/privacy", "form", True),
    "Pipl": ("mailto:privacy@pipl.com", "email", False),
    "Radaris": ("https://radaris.com/privacy", "form", True),
    "Instant Check Mate": ("https://www.instantcheckmate.com/opt-out/", "form", True),
    "PeopleFinder": ("https://www.peoplefinder.com/optout.php", "form", True),
    "PublicRecordsNow": ("https://www.publicrecordsnow.com/opt-out/", "form", True),
    "USSearch": ("https://www.ussearch.com/optout", "form", True),
    "ThatsThem": ("https://thatsthem.com/optout", "form", True),
    "FamilyTreeNow": ("https://www.familytreenow.com/optout", "form", True),
    "FastBackgroundCheck": ("https://www.fastbackgroundcheck.com/optout", "form", True),
    "Truecaller": ("https://www.truecaller.com/unlisting", "form", True),
    "Zabasearch": ("https://www.zabasearch.com/removal/", "form", True),
    "PeekYou": ("https://www.peekyou.com/optout/", "form", True),
    "USPhoneBook": ("https://www.usphonebook.com/opt-out/", "form", True),
    "FindPeopleSearch": ("https://www.findpeoplesearch.com/opt-out/", "form", True),
    "CallFinder": ("https://www.callfinder.com/opt-out.php", "form", True),
    "ReversePhoneCheck": ("https://www.reversephonecheck.com/optout/", "form", True),
}

BROKER_HOME_PAGES = {
    "Intelius": "https://www.intelius.com/privacy",
    "BeenVerified": "https://www.beenverified.com/privacy",
    "Spokeo": "https://www.spokeo.com/privacy",
    "WhitePages": "https://www.whitepages.com/privacy",
    "Pipl": "https://pipl.com/privacy",
    "Radaris": "https://radaris.com/privacy",
    "Instant Check Mate": "https://www.instantcheckmate.com/privacy",
    "PeopleFinder": "https://www.peoplefinder.com/privacy",
    "PublicRecordsNow": "https://www.publicrecordsnow.com/privacy",
    "USSearch": "https://www.ussearch.com/privacy",
    "ThatsThem": "https://thatsthem.com/privacy",
    "FamilyTreeNow": "https://www.familytreenow.com/privacy",
    "FastBackgroundCheck": "https://www.fastbackgroundcheck.com/privacy",
    "Truecaller": "https://www.truecaller.com/privacy",
    "Zabasearch": "https://www.zabasearch.com/about/",
    "PeekYou": "https://www.peekyou.com/privacy",
    "USPhoneBook": "https://www.usphonebook.com/privacy",
    "FindPeopleSearch": "https://www.findpeoplesearch.com/privacy",
    "CallFinder": "https://www.callfinder.com/privacy",
    "ReversePhoneCheck": "https://www.reversephonecheck.com/privacy",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
TIMEOUT = 15
DELAY = 2.0


def discover_optout_via_search(broker_name: str) -> str | None:
    """Use web search to find opt-out URL for a broker."""
    import os
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY") or os.environ.get("SERPER_API_KEY")
    if not api_key:
        return None

    try:
        query = f"{broker_name} opt out remove my data"
        if os.environ.get("SEARCH_ENGINE") == "serper":
            resp = httpx.post(
                "https://google.serper.dev/search",
                json={"q": query},
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                timeout=TIMEOUT,
            )
            items = resp.json().get("knowledgeGraph", []) + resp.json().get("organic", [])
            for item in items:
                url = item.get("link", "")
                if "opt" in url.lower() or "remove" in url.lower() or "delete" in url.lower():
                    return url
        else:
            resp = httpx.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": 5},
                headers={"Accept": "application/json", "X-Subscription-Token": api_key},
                timeout=TIMEOUT,
            )
            for r in resp.json().get("web", {}).get("results", []):
                url = r.get("url", "")
                if "opt" in url.lower() or "remove" in url.lower() or "privacy" in url.lower():
                    return url
    except Exception:
        pass
    return None


def discover_from_privacy_page(broker_home: str) -> str | None:
    """Scrape broker's privacy page for opt-out link."""
    try:
        resp = httpx.get(broker_home, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")
        # Look for opt-out related links
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            text = a.get_text().lower()
            if any(kw in href or kw in text for kw in ["opt-out", "optout", "remove", "delete", "do-not-sell"]):
                # Resolve relative URLs
                from urllib.parse import urljoin
                return urljoin(str(resp.url), a["href"])
    except Exception:
        pass
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Discover opt-out URLs for data brokers")
    parser.add_argument("--input", required=True, help="CSV from person_search.py")
    parser.add_argument("--output", default="optout_urls.csv")
    args = parser.parse_args()

    # Read input
    brokers_found = []
    with open(args.input) as f:
        for row in csv.DictReader(f):
            brokers_found.append(row)

    results = []
    for row in brokers_found:
        broker = row["broker"]
        print(f"Finding opt-out for: {broker}")

        optout_url = None
        method = "unknown"
        requires_id = False
        verified = False

        # 1. Check known list
        if broker in OPT_OUT_URLS:
            optout_url, method, requires_id = OPT_OUT_URLS[broker]
            verified = True

        # 2. Try privacy page scrape
        if not optout_url and broker in BROKER_HOME_PAGES:
            discovered = discover_from_privacy_page(BROKER_HOME_PAGES[broker])
            if discovered:
                optout_url = discovered
                method = "form"
                verified = False

        # 3. Try web search
        if not optout_url:
            discovered = discover_optout_via_search(broker)
            if discovered:
                optout_url = discovered
                method = "search"
                verified = False

        results.append({
            "broker": broker,
            "found_url": row.get("url", ""),
            "optout_url": optout_url or "",
            "method": method,
            "requires_identity": str(requires_id),
            "verified": str(verified),
        })
        time.sleep(DELAY)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["broker", "found_url", "optout_url", "method", "requires_identity", "verified"])
        writer.writeheader()
        writer.writerows(results)

    found = sum(1 for r in results if r["optout_url"])
    print(f"\n✓ Found opt-out URLs for {found}/{len(results)} brokers. Saved to {output_path}")
    for r in results:
        status = "✓" if r["optout_url"] else "✗"
        print(f"  {status} {r['broker']}: {r['optout_url'] or 'NOT FOUND'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())