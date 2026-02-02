\
from __future__ import annotations
import argparse
import csv
import os
import time
import random
from typing import Dict, Any, List

from dotenv import load_dotenv

from email_patterns import generate_candidates
from verifier import verify_email
from utils import utc_now_iso, safe_json_dumps, log

DEFAULT_HEADER = [
    "created_at",
    "updated_at",
    "first_name",
    "last_name",
    "title",
    "company",
    "domain",
    "linkedin_url",
    "email_best",
    "email_candidates",
    "verification_status",
    "confidence_score",
    "source",
    "catch_all",
    "mx_found",
    "opt_out",
    "notes",
]

def read_leads_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        out = []
        for row in reader:
            out.append({k: (v or "").strip() for k, v in row.items()})
        return out

def process_lead(lead: Dict[str, str]) -> Dict[str, Any]:
    first = lead.get("first_name", "")
    last = lead.get("last_name", "")
    company = lead.get("company", "")
    domain = lead.get("domain", "")
    linkedin_url = lead.get("linkedin_url", "")
    title = lead.get("title", "")

    candidates = generate_candidates(first, last, domain, max_candidates=15)

    best = ""
    best_res = None

    for cand in candidates:
        res = verify_email(cand)
        # Pick best by confidence, tie-breaker prefer valid over risky over unknown over invalid
        rank = {"valid": 3, "risky": 2, "unknown": 1, "invalid": 0}
        if best_res is None:
            best_res = res
            best = cand
        else:
            if (res.confidence_score, rank.get(res.status, 0)) > (best_res.confidence_score, rank.get(best_res.status, 0)):
                best_res = res
                best = cand

        # Small delay to avoid hammering MX/SMTP
        time.sleep(random.uniform(0.4, 1.2))

    now = utc_now_iso()

    row = {
        "created_at": now,        # If upsert updates, Sheets layer can keep created_at if you want; MVP writes now.
        "updated_at": now,
        "first_name": first,
        "last_name": last,
        "title": title,
        "company": company,
        "domain": domain,
        "linkedin_url": linkedin_url,
        "email_best": best or "",
        "email_candidates": safe_json_dumps(candidates),
        "verification_status": best_res.status if best_res else "unknown",
        "confidence_score": best_res.confidence_score if best_res else 0,
        "source": "inferred+verified",
        "catch_all": str(best_res.catch_all) if best_res else "False",
        "mx_found": str(best_res.mx_found) if best_res else "False",
        "opt_out": "FALSE",
        "notes": best_res.reason if best_res else "",
    }
    return row

def main():
    load_dotenv()

    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to leads CSV")
    ap.add_argument("--dry_run", action="store_true", help="Do not write to Google Sheets")
    ap.add_argument("--sheet_id", default="", help="Google Sheet ID (required unless --dry_run)")
    ap.add_argument("--worksheet", default="leads", help="Worksheet/tab name (default: leads)")
    ap.add_argument("--service_account_file", default=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "secrets/service_account.json"))
    args = ap.parse_args()

    leads = read_leads_csv(args.input)
    log(f"Loaded {len(leads)} leads from {args.input}")

    rows = []
    for i, lead in enumerate(leads, start=1):
        log(f"\n[{i}/{len(leads)}] Processing: {lead.get('first_name')} {lead.get('last_name')} @ {lead.get('domain')}")
        row = process_lead(lead)
        rows.append(row)
        log(f"  -> best: {row['email_best']} ({row['verification_status']} score={row['confidence_score']})")

    if args.dry_run:
        log("\nDry run enabled: not writing to Google Sheets.")
        return

    if not args.sheet_id:
        raise SystemExit("Missing --sheet_id (required unless --dry_run)")

    from sheets import get_sheets_service, ensure_header, upsert_row

    svc = get_sheets_service(args.service_account_file)
    ensure_header(svc, args.sheet_id, args.worksheet, DEFAULT_HEADER)

    for row in rows:
        action, idx = upsert_row(svc, args.sheet_id, args.worksheet, DEFAULT_HEADER, row, key_field="linkedin_url")
        log(f"Sheets: {action} ({row['linkedin_url']})")

if __name__ == "__main__":
    main()
