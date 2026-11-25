"""Tulis snapshot ringkas (spend/lead/CPL hari ini) ke Cloudflare KV, untuk widget phone.
Murah — cuma 1 panggilan Meta (level ad, date_preset today), bukan full dashboard build.
Guna: python3 scripts/push_live.py
Env perlu: CLOUDFLARE_API_TOKEN, CF_ACCOUNT_ID, CF_KV_NAMESPACE_ID (sama macam run_build.mjs)
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
from meta_api import cfg, get_all

LEAD = {"lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead", "onsite_web_lead"}
FORM = "offsite_conversion.fb_pixel_custom"


def leads(actions):
    w = f = 0
    for a in actions or []:
        v = int(float(a["value"]))
        if a["action_type"] in LEAD:
            w = max(w, v)
        elif a["action_type"] == FORM:
            f = v
    return f + w


def aware(name):
    return "AWARENESS" in name.upper()


def main():
    acc = cfg()["META_AD_ACCOUNT_ID"]
    rows = get_all(f"{acc}/insights", {
        "level": "ad", "date_preset": "today",
        "fields": "campaign_name,spend,actions", "limit": "500"})
    spend = sum(float(r.get("spend") or 0) for r in rows if not aware(r["campaign_name"]))
    lead = sum(leads(r.get("actions")) for r in rows if not aware(r["campaign_name"]))
    cpl = round(spend / lead, 2) if lead else None
    now = datetime.now(timezone(timedelta(hours=8)))
    payload = {
        "ok": True,
        "spend_today": round(spend, 2),
        "leads_today": lead,
        "cpl_today": cpl,
        "updated_at": now.isoformat(),
    }
    body = json.dumps(payload, ensure_ascii=False)

    token = os.environ["CLOUDFLARE_API_TOKEN"]
    acct = os.environ["CF_ACCOUNT_ID"]
    ns = os.environ["CF_KV_NAMESPACE_ID"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/storage/kv/namespaces/{ns}/values/live"
    req = urllib.request.Request(url, data=body.encode(), method="PUT",
                                  headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("KV write:", r.status, payload)
    except urllib.error.HTTPError as e:
        print("GAGAL KV write:", e.code, e.read().decode()[:300])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
