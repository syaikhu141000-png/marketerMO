"""Report level ad. Guna: python3 scripts/report.py [last_7d|last_14d|last_30d|yesterday]
Hasil = lead (form/onsite) + chat WhatsApp dimulakan. Booking/enrollment TIADA dalam Meta; sambung dari Sheet."""
import sys
from meta_api import cfg, get_all

preset = sys.argv[1] if len(sys.argv) > 1 else "last_7d"
RESULT_TYPES = {
    "lead": "Lead",
    "onsite_conversion.lead_grouped": "Lead",
    "offsite_conversion.fb_pixel_lead": "Lead",
    "onsite_conversion.messaging_conversation_started_7d": "Chat",
}

rows = get_all(f"{cfg()['META_AD_ACCOUNT_ID']}/insights", {
    "level": "ad", "date_preset": preset, "limit": 200,
    "fields": "ad_name,campaign_name,spend,impressions,cpm,ctr,actions",
})

out = []
for r in rows:
    spend = float(r.get("spend", 0))
    # elak kira dua kali: lead & lead_grouped & pixel_lead ialah lead yang sama -> ambil maksimum kumpulan Lead
    got = {"Lead": 0, "Chat": 0}
    for a in r.get("actions", []):
        kind = RESULT_TYPES.get(a["action_type"])
        if kind:
            got[kind] = max(got[kind], int(float(a["value"])))
    res = got["Lead"] + got["Chat"]
    out.append((r["ad_name"], spend, float(r.get("ctr", 0)), float(r.get("cpm", 0)),
                got["Lead"], got["Chat"], spend / res if res else None))

out.sort(key=lambda x: (x[6] is None, x[6] or 0))
print(f"Report {preset}  ({len(out)} ad)\n")
print(f"{'Ad':38}{'Spend':>10}{'CTR%':>7}{'CPM':>8}{'Lead':>6}{'Chat':>6}{'RM/hasil':>10}")
for n, s, ctr, cpm, l, c, cpr in out:
    print(f"{n[:37]:38}{s:>10.2f}{ctr:>7.2f}{cpm:>8.2f}{l:>6}{c:>6}{(f'{cpr:.2f}' if cpr else '-'):>10}")
print(f"\nJumlah spend: RM {sum(o[1] for o in out):,.2f}")
print("Nota: CPL rendah bukan jaminan lead berkualiti. Banding dengan booking/enrollment sebelum pause/scale.")
