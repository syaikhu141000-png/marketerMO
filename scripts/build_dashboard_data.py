"""Jana dashboard/data.json untuk Minda Optima 2 dari Meta Marketing API.
Guna: python3 scripts/build_dashboard_data.py
Hasil = Lead + WhatsFormSubmit. Chat WhatsApp TIDAK dikira. Booking/enrollment tiada dalam Meta."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from meta_api import ROOT, cfg, get, get_all

# kumpulan lead: ambil maksimum dalam kumpulan supaya tak kira dua kali (lead = lead_grouped = pixel_lead)
LEAD_TYPES = {"lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead", "onsite_web_lead"}
FORM_TYPE = "offsite_conversion.fb_pixel_custom"  # WhatsFormSubmit


def results(actions):
    lead = form = 0
    for a in actions or []:
        v = int(float(a["value"]))
        if a["action_type"] in LEAD_TYPES:
            lead = max(lead, v)
        elif a["action_type"] == FORM_TYPE:
            form = v
    return lead, form


def num(r, k):
    return float(r.get(k) or 0)


def row(r):
    lead, form = results(r.get("actions"))
    return {"spend": round(num(r, "spend"), 2), "impressions": int(num(r, "impressions")),
            "clicks": int(num(r, "clicks")), "lead": lead, "form": form, "results": lead + form}


acc = cfg()["META_AD_ACCOUNT_ID"]
info = get(acc, {"fields": "name,currency,timezone_name,account_status"})
F = "spend,impressions,clicks,actions"

daily = [{"date": r["date_start"], **row(r)} for r in
         get_all(f"{acc}/insights", {"date_preset": "last_30d", "time_increment": 1, "fields": F, "limit": 100})]

status = {c["id"]: c for c in get_all(f"{acc}/campaigns", {"fields": "id,name,effective_status,daily_budget,objective", "limit": 200})}
campaigns = []
for r in get_all(f"{acc}/insights", {"level": "campaign", "date_preset": "last_7d",
                                      "fields": "campaign_id,campaign_name," + F, "limit": 200}):
    s = status.get(r["campaign_id"], {})
    campaigns.append({"id": r["campaign_id"], "name": r["campaign_name"],
                      "status": s.get("effective_status", "?"), "objective": s.get("objective", ""),
                      "daily_budget": round(int(s["daily_budget"]) / 100, 2) if s.get("daily_budget") else None,
                      **row(r)})

ads = [{"name": r["ad_name"], "campaign": r["campaign_name"], **row(r)} for r in
       get_all(f"{acc}/insights", {"level": "ad", "date_preset": "last_7d",
                                   "fields": "ad_name,campaign_name," + F, "limit": 500})]

out = {
    "meta": {"generated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
             "account_name": info["name"], "currency": info["currency"], "timezone": info.get("timezone_name"),
             "api_version": cfg(need_account=False)["META_API_VERSION"],
             "note": "Hasil = Lead + WhatsFormSubmit. Chat WhatsApp tidak dikira. Data sehingga semalam."},
    "daily": daily, "campaigns": campaigns, "ads": ads,
}
dest = ROOT / "dashboard" / "data.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(f"OK {dest.relative_to(ROOT)}: {len(daily)} hari, {len(campaigns)} kempen, {len(ads)} ad")
