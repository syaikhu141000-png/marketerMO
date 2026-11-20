"""Alert ringkas MO2 — jalan kerap (cth setiap 1 jam), HANYA output sesuatu bila ada isu.
Isu yang disemak:
  - Ad/ad set aktif, 0 lead, spend hari ini >= RM30 (merah)
  - CPL hari ini >= RM35 dengan spend >= RM30
  - Jumlah spend hari ini (semua iklan) hampir/melebihi had RM300
Guna: python3 scripts/alert_check.py
Keluaran: teks alert (ada isu) ATAU tiada apa-apa + exit code 0 (tiada isu, JANGAN hantar email).
"""
import sys
from collections import defaultdict
from meta_api import cfg, get_all

LEAD = {"lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead", "onsite_web_lead"}
FORM = "offsite_conversion.fb_pixel_custom"
BUDGET_CAP = 300
FIELDS = "campaign_name,adset_name,ad_name,spend,actions"


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
    rows = get_all(f"{acc}/insights", {"level": "ad", "date_preset": "today", "fields": FIELDS, "limit": "500"})

    total_spend = sum(float(r.get("spend") or 0) for r in rows)
    out = []

    for r in rows:
        if aware(r["campaign_name"]):
            continue
        spend = float(r.get("spend") or 0)
        lead = leads(r.get("actions"))
        if spend < 30:
            continue
        cpl = spend / lead if lead else None
        if lead == 0:
            out.append(f"🔴 {r['ad_name']} ({r['adset_name'][:40]}): spend RM{spend:.2f} hari ini, 0 LEAD")
        elif cpl and cpl >= 35:
            out.append(f"🟡 {r['ad_name']} ({r['adset_name'][:40]}): CPL RM{cpl:.2f} hari ini (spend RM{spend:.2f}, {lead} lead)")

    if total_spend >= BUDGET_CAP:
        out.append(f"🔴 Spend hari ini RM{total_spend:.2f} MELEBIHI had RM{BUDGET_CAP}")
    elif total_spend >= BUDGET_CAP * 0.9:
        out.append(f"🟡 Spend hari ini RM{total_spend:.2f} dah {total_spend/BUDGET_CAP*100:.0f}% drpd had RM{BUDGET_CAP}")

    if out:
        print("ADA ISU:")
        for line in out:
            print("-", line)
    else:
        print("TIADA ISU")


if __name__ == "__main__":
    main()
