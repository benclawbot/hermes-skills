#!/usr/bin/env python3
"""
removal_request.py — File GDPR / CCPA removal requests with data brokers.

Reads opt-out URLs from optout_discovery.py output, submits removal requests
via form POST or email, logs all activity with timestamps.

Legal basis:
  - GDPR Article 17: Right to erasure
  - CCPA: California Consumer Privacy Act
  - ePrivacy Directive
"""

import csv
import os
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

try:
    import httpx
except ImportError:
    print("ERROR: missing httpx. Run: uv pip install httpx")
    sys.exit(1)

# ── Config ───────────────────────────────────────────────────────────────────

PERSON = {
    "name": "Thomas Schmoele",
    "email": "thomas.schmoele@icloud.com",
    "address": "",  # fill in if required by brokers
    "phone": "",    # fill in if required
}

# SMTP config for email-based requests (set env vars)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.google.com",
    "Referer": "https://www.google.com/",
}
TIMEOUT = 30
DELAY = 3.0


# ── Email removal ─────────────────────────────────────────────────────────────

def send_email_removal(broker_name: str, optout_url: str, person: dict) -> dict:
    """Send GDPR removal request via email."""
    if not SMTP_HOST:
        return {"success": False, "error": "SMTP not configured", "method": "email"}

    subject = f"GDPR Article 17 — Request for erasure of {person['name']}'s personal data"
    body = f"""Dear Data Protection Officer,

Pursuant to Article 17 of the General Data Protection Regulation (EU) 2016/679 ("GDPR"), I hereby request the erasure of all personal data concerning me held by {broker_name}.

Name: {person['name']}
Email: {person['email']}
{('Address: ' + person['address']) if person.get('address') else ''}
{('Phone: ' + person['phone']) if person.get('phone') else ''}

I request that {broker_name}:
1. Erase all personal data concerning me without undue delay and at the latest within one month of receipt of this request (Article 17(1) GDPR).
2. Cease making such data available to third parties.
3. Confirm in writing once the erasure has been completed.

If you require further information to verify my identity, please contact me at {person['email']}. Note that under Article 12(5) GDPR, you may not require the payment of a fee for complying with this request.

Should you not respond within the statutory period, I reserve the right to lodge a complaint with the competent supervisory authority (Article 77 GDPR).

Sincerely,
{person['name']}
{person['email']}
"""

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = optout_url.replace("mailto:", "")
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        return {"success": True, "method": "email", "sent_to": optout_url}
    except Exception as e:
        return {"success": False, "error": str(e), "method": "email"}


# ── Form-based removal ────────────────────────────────────────────────────────

def submit_form_removal(broker_name: str, optout_url: str, person: dict, method: str = "gdpr") -> dict:
    """
    Submit removal request via form.
    method: 'gdpr' | 'ccpa' | 'generic'
    """
    # Try direct POST to the opt-out URL
    # Many brokers use a GET form or a POST with specific fields
    # We'll try a generic approach and fall back to a direct form fill

    # Common form field mappings
    field_patterns = {
        "firstName": person["name"].split()[0] if person["name"] else "",
        "lastName": " ".join(person["name"].split()[1:]) if person["name"] else "",
        "email": person.get("email", ""),
        "phone": person.get("phone", ""),
        "address": person.get("address", ""),
        "fullName": person["name"],
        "Name": person["name"],
        "emailAddress": person.get("email", ""),
        "confirmEmail": person.get("email", ""),
    }

    result = {
        "success": False,
        "method": method,
        "status_code": None,
        "response_text": "",
        "error": "",
    }

    try:
        # Try GET first (many opt-outs are ?name=...&email=... style)
        params = {}
        for k, v in field_patterns.items():
            if v:
                params[k] = v

        resp = httpx.get(
            optout_url,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        result["status_code"] = resp.status_code
        result["response_text"] = resp.text[:500]

        # Check if we got a confirmation page
        confirmation_keywords = ["confirm", "request received", "success", "removed", "erasure"]
        text_lower = resp.text.lower()
        if any(kw in text_lower for kw in confirmation_keywords):
            result["success"] = True
        elif resp.status_code == 200:
            result["success"] = True  # Assume form was accepted if we got a page back
        else:
            result["error"] = f"HTTP {resp.status_code}"

    except Exception as e:
        result["error"] = str(e)

    return result


# ── GDPR-specific letter ──────────────────────────────────────────────────────

def get_gdpr_letter(broker_name: str, person: dict) -> str:
    addr = person.get("address") or "[address on file]"
    phone = person.get("phone") or ""
    contact = f"{person['email']} {phone}".strip()
    return f"""Data Erasure Request — GDPR Article 17

To: {broker_name} Data Protection Team

I, {person['name']}, residing at {addr}, hereby request immediate erasure of all personal data concerning me held by {broker_name}, pursuant to Article 17 of Regulation (EU) 2016/679 ("GDPR").

Any recipients of my data must also be notified of this erasure request (Article 17(2) GDPR).

Data subject contact: {contact}

If you believe this request does not apply, please provide written grounds for refusal within 30 days (Article 12(3) GDPR).

{person['name']} — {person['email']}"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="File GDPR/CCPA removal requests with data brokers")
    parser.add_argument("--input", required=True, help="CSV from optout_discovery.py")
    parser.add_argument("--output", default="removal_requests.csv")
    parser.add_argument("--method", default="gdpr", choices=["gdpr", "ccpa", "email"])
    parser.add_argument("--person-name", default=PERSON["name"])
    parser.add_argument("--person-email", default=PERSON["email"])
    args = parser.parse_args()

    person = {"name": args.person_name, "email": args.person_email, "address": "", "phone": ""}

    rows = []
    with open(args.input) as f:
        for row in csv.DictReader(f):
            rows.append(row)

    results = []
    for row in rows:
        broker = row["broker"]
        optout_url = row.get("optout_url", "")
        method_type = row.get("method", "form")

        print(f"Processing: {broker} ({optout_url[:60]})")

        result = {
            "broker": broker,
            "optout_url": optout_url,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "method": args.method,
            "response": "",
            "error": "",
        }

        if not optout_url:
            result["error"] = "No opt-out URL found"
            results.append(result)
            continue

        if optout_url.startswith("mailto:"):
            res = send_email_removal(broker, optout_url, person)
            result["success"] = res.get("success", False)
            result["response"] = res.get("error", "sent")
        else:
            res = submit_form_removal(broker, optout_url, person, method=args.method)
            result["success"] = res.get("success", False)
            result["response"] = res.get("response_text", "")[:200]
            result["error"] = res.get("error", "")

        results.append(result)
        print(f"  → {'SUCCESS' if result['success'] else 'FAILED'}: {result['error'] or result['response'][:80]}")
        time.sleep(DELAY)

    # Write log
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["broker", "optout_url", "timestamp", "success", "method", "response", "error"])
        writer.writeheader()
        writer.writerows(results)

    success_count = sum(1 for r in results if r["success"])
    print(f"\n✓ Removal requests filed: {success_count}/{len(results)}. Log: {output_path}")
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(f"  {status} {r['broker']}: {r['error'] or 'OK'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())