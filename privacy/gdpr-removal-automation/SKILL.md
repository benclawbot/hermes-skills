---
name: gdpr-removal-automation
description: Find personal data across data brokers and file GDPR/removal requests automatically. Uses web search + HTTP to discover and request removal from broker sites.
---

# GDPR Removal Automation

## Overview

Automated pipeline to:
1. Search for an individual's data across known data broker sites
2. Discover opt-out URLs for each broker
3. Submit removal requests (GDPR article 17, CCPA, etc.)
4. Track and report status

## Architecture

```
person_search.py     — Discover data broker listings via web search
optout_discovery.py  — Find opt-out URL for each discovered broker
removal_request.py   — Submit removal request (form POST, email, etc.)
run_pipeline.py      — Orchestrate the full pipeline
```

## Key Data Brokers (EU/US)

| Broker | URL | Opt-out method |
|--------|-----|----------------|
| Intelius | intelius.com | Form |
| BeenVerified | beenverified.com | Form |
| Spokeo | spokeo.com | Form |
| WhitePages | whitepages.com | Form |
| Pipl | pipl.com | Email |
| Radaris | radaris.com | Form |
| Instant Check Mate | instantcheckmate.com | Form |
| PeopleFinder | peoplefinder.com | Form |
| PublicRecordsNow | publicrecordsnow.com | Form |
| USSearch | ussearch.com | Form |
| ThatsThem | thatsthem.com | Form |
| FamilyTreeNow | familytreeNow.com | Form |
| FastBackgroundCheck | fastbackgroundcheck.com | Form |
| AdvancedBackgroundChecks | advancedbackgroundchecks.com | Form |
| Truecaller | truecaller.com | App/Form |
| Zabasearch | zabasearch.com | Form |

## Search Strategy

For each identifier (name, email, phone, address):
```bash
python3 person_search.py --name "Thomas Schmoele" --search-engines brave --output brokers_found.csv
```

## Opt-out Discovery

```bash
python3 optout_discovery.py --input brokers_found.csv --output optout_urls.csv
```

## Removal Request

```bash
python3 removal_request.py --input optout_urls.csv --method gdpr --output removal_log.csv
```

## Pipeline Run

```bash
python3 run_pipeline.py --person "Thomas Schmoele" --email t@email.com --phone +49XXX --output ./gdpr_results/
```

## Broker discovery: hard limits of free automation

- Direct HTTP checks (`--method direct`) work for some brokers (USSearch returned a hit in testing), but most block with CAPTCHAs, JS challenges, or rate limits
- Web search discovery (`--method web`) requires a Brave/Exa/Serper API key — without it, only direct checks run and coverage is ~5-10% of brokers
- **Cannot be fully automated for free**: Truecaller requires in-app delisting, Pipl requires email verification that can't be scripted, many US brokers use reCAPTCHA
- The 4-script pipeline (person_search → optout_discovery → removal_request → run_pipeline) is the right architecture, but needs API credentials to be effective
- BROKERS list in person_search.py is 2-tuples but check_brokers_direct unpacks 3 — keep tuple length consistent (3 elements: name, url, None)

## Legal Notes

- GDPR Article 17: Right to erasure ("right to be forgotten")
- CCPA: California residents can request deletion
- ePrivacy Directive: Marketing data opt-out
- Track all requests with timestamps for legal compliance
- Some brokers require identity verification before removal