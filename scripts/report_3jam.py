"""Report MO2 untuk hari ini (setakat masa run): Campaign -> Ad set -> Ad.
Metrik: Spend, Impressions, Reach, CPM, Link click, CTR, CPC, Lead, CPL (+ ThruPlay untuk Awareness).
Lead = WhatsFormSubmit + Website lead (chat WhatsApp tidak dikira).
Guna: python3 scripts/report_3jam.py [--html fail.html] [--md fail.md]
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from meta_api import cfg, get_all

LEAD = {"lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead", "onsite_web_lead"}
FORM = "offsite_conversion.fb_pixel_custom"
BUDGET_CAP = 300  # had harian semua iklan (keputusan consultant)


def leads(actions):
    w = f = 0
    for a in actions or []:
        v = int(float(a["value"]))
        if a["action_type"] in LEAD:
            w = max(w, v)
        elif a["action_type"] == FORM:
            f = v
    return f + w


def row(r):
    sp = float(r.get("spend") or 0)
    im = int(r.get("impressions") or 0)
    ck = int(r.get("inline_link_clicks") or 0)
    tp = int(float((r.get("video_thruplay_watched_actions") or [{"value": 0}])[0]["value"]))
    return {"spend": sp, "imp": im, "reach": int(r.get("reach") or 0), "clk": ck, "lead": leads(r.get("actions")), "tp": tp}


def add(a, b):
    for k in ("spend", "imp", "clk", "lead", "tp"):
        a[k] = a.get(k, 0) + b[k]
    a["reach"] = a.get("reach", 0) + b["reach"]  # anggaran (reach tak boleh dijumlah tepat)
    return a


def m(x):
    cpm = x["spend"] / x["imp"] * 1000 if x["imp"] else None
    ctr = x["clk"] / x["imp"] * 100 if x["imp"] else None
    cpc = x["spend"] / x["clk"] if x["clk"] else None
    cpl = x["spend"] / x["lead"] if x["lead"] else None
    return cpm, ctr, cpc, cpl


def f2(v, pre="RM"):
    return "—" if v is None else f"{pre}{v:,.2f}"


def light(cpl, spend, aware):
    if aware:
        return "⚪"
    if cpl is None:
        return "🔴" if spend >= 30 else "⚪"
    return "🟢" if cpl <= 15 else ("🟡" if cpl < 30 else "🔴")


def main():
    acc = cfg()["META_AD_ACCOUNT_ID"]
    myt = datetime.now(timezone(timedelta(hours=8)))
    rows = get_all(f"{acc}/insights", {
        "level": "ad", "date_preset": "today", "limit": "500",
        "fields": "campaign_name,adset_name,ad_name,spend,impressions,reach,inline_link_clicks,actions,video_thruplay_watched_actions"})
    tree = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if float(r.get("spend") or 0) <= 0 and not leads(r.get("actions")):
            continue
        tree[r["campaign_name"]][r["adset_name"]].append((r["ad_name"], row(r)))

    total = {}
    lead_total = {}
    camps = []
    for c, sets in tree.items():
        aware = "AWARENESS" in c.upper()
        ct = {}
        sl = []
        for s, ads in sets.items():
            st = {}
            for _, x in ads:
                add(st, x)
            sl.append((s, st, sorted(ads, key=lambda a: -a[1]["spend"])))
            add(ct, st)
        add(total, ct)
        if not aware:
            add(lead_total, ct)
        camps.append((c, aware, ct, sorted(sl, key=lambda s: -s[1]["spend"])))
    camps.sort(key=lambda c: -c[2]["spend"])

    L = []
    L.append(f"# Report Iklan MO2 — {myt:%d %b %Y}, setakat {myt:%I:%M %p}")
    L.append("Data hari ini (Meta belum muktamad). Lead = WhatsFormSubmit + Website lead (chat tidak dikira).\n")
    if total:
        cpm, ctr, cpc, cpl = m(lead_total) if lead_total else (None,) * 4
        L.append("## Ringkasan")
        L.append("| Spend semua | Spend lead-gen | Lead | CPL | CPM | CTR | Had harian |")
        L.append("|---|---|---|---|---|---|---|")
        L.append(f"| {f2(total['spend'])} | {f2(lead_total.get('spend', 0))} | {lead_total.get('lead', 0)} | {f2(cpl)} | {f2(cpm)} | "
                 f"{'—' if ctr is None else f'{ctr:.2f}%'} | RM{BUDGET_CAP} ({total['spend'] / BUDGET_CAP * 100:.0f}% digunakan) |\n")

    L.append("## 1. Ikut campaign")
    L.append("| | Campaign | Spend | Impr. | CPM | Klik | CTR | CPC | Lead | CPL |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for c, aware, x, _ in camps:
        cpm, ctr, cpc, cpl = m(x)
        res = f"{x['tp']} ThruPlay" if aware else str(x["lead"])
        L.append(f"| {light(cpl, x['spend'], aware)} | {c} | {f2(x['spend'])} | {x['imp']:,} | {f2(cpm)} | {x['clk']} | "
                 f"{'—' if ctr is None else f'{ctr:.2f}%'} | {f2(cpc)} | {res} | {'—' if aware else f2(cpl)} |")

    L.append("\n## 2. Ikut ad set")
    L.append("| | Campaign | Ad set | Spend | CPM | CTR | Lead | CPL |")
    L.append("|---|---|---|---|---|---|---|---|")
    for c, aware, _, sl in camps:
        for s, x, _ in sl:
            cpm, ctr, cpc, cpl = m(x)
            res = f"{x['tp']} TP" if aware else str(x["lead"])
            L.append(f"| {light(cpl, x['spend'], aware)} | {c[:22]} | {s} | {f2(x['spend'])} | {f2(cpm)} | "
                     f"{'—' if ctr is None else f'{ctr:.2f}%'} | {res} | {'—' if aware else f2(cpl)} |")

    L.append("\n## 3. Ikut ad")
    L.append("| | Ad set | Ad | Spend | CPM | CTR | Lead | CPL |")
    L.append("|---|---|---|---|---|---|---|---|")
    for c, aware, _, sl in camps:
        for s, _, ads in sl:
            for a, x in ads:
                cpm, ctr, cpc, cpl = m(x)
                res = f"{x['tp']} TP" if aware else str(x["lead"])
                L.append(f"| {light(cpl, x['spend'], aware)} | {s[:30]} | {a} | {f2(x['spend'])} | {f2(cpm)} | "
                         f"{'—' if ctr is None else f'{ctr:.2f}%'} | {res} | {'—' if aware else f2(cpl)} |")

    # amaran
    warn = []
    for c, aware, _, sl in camps:
        if aware:
            continue
        for s, _, ads in sl:
            for a, x in ads:
                cpl = m(x)[3]
                if x["lead"] == 0 and x["spend"] >= 30:
                    warn.append(f"- 🔴 **{a}** — spend {f2(x['spend'])}, **0 lead** hari ini")
                elif cpl and cpl >= 30 and x["spend"] >= 30:
                    warn.append(f"- 🟡 **{a}** — CPL {f2(cpl)} (≥ RM30)")
    if total and total["spend"] > BUDGET_CAP:
        warn.append(f"- 🔴 Jumlah spend {f2(total['spend'])} melebihi had RM{BUDGET_CAP}")
    L.append("\n## Amaran")
    L.extend(warn or ["- Tiada amaran setakat ini."])
    L.append("\n_🟢 CPL ≤ RM15 · 🟡 < RM30 · 🔴 ≥ RM30 atau 0 lead dgn spend ≥ RM30 · ⚪ Awareness / data belum cukup. Report sahaja — tiada perubahan dibuat di Meta._")
    md = "\n".join(L)

    if "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w").write(md)
    print(md)


if __name__ == "__main__":
    main()
