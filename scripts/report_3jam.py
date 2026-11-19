"""Report MO2 (setiap 3 jam): Campaign -> Ad set -> Ad, dengan 6 tempoh:
3 jam terkini · 3 jam sebelumnya · Hari ini · Semalam · 7 hari (tidak termasuk hari ini) · Bulan ini.
Metrik: Spend, Impressions, CPM, Klik, CTR, CPC, Lead, CPL (Awareness: ThruPlay).
Lead = WhatsFormSubmit + Website lead (chat WhatsApp tidak dikira).
Guna: python3 scripts/report_3jam.py [--md fail.md]
"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from meta_api import cfg, get_all

LEAD = {"lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead", "onsite_web_lead"}
FORM = "offsite_conversion.fb_pixel_custom"
BUDGET_CAP = 300
FIELDS = "campaign_name,adset_name,ad_name,spend,impressions,inline_link_clicks,actions,video_thruplay_watched_actions"
PRESETS = [("today", "Hari ini"), ("yesterday", "Semalam"), ("last_7d", "7 hari"), ("this_month", "Bulan ini")]


def leads(actions):
    w = f = 0
    for a in actions or []:
        v = int(float(a["value"]))
        if a["action_type"] in LEAD:
            w = max(w, v)
        elif a["action_type"] == FORM:
            f = v
    return f + w


def z():
    return {"spend": 0.0, "imp": 0, "clk": 0, "lead": 0, "tp": 0}


def add(acc, r):
    acc["spend"] += float(r.get("spend") or 0)
    acc["imp"] += int(r.get("impressions") or 0)
    acc["clk"] += int(r.get("inline_link_clicks") or 0)
    acc["lead"] += leads(r.get("actions"))
    acc["tp"] += int(float((r.get("video_thruplay_watched_actions") or [{"value": 0}])[0]["value"]))


def met(x):
    return (x["spend"] / x["imp"] * 1000 if x["imp"] else None, x["clk"] / x["imp"] * 100 if x["imp"] else None,
            x["spend"] / x["clk"] if x["clk"] else None, x["spend"] / x["lead"] if x["lead"] else None)


rm = lambda v: "—" if v is None else f"RM{v:,.2f}"  # noqa: E731
pc = lambda v: "—" if v is None else f"{v:.2f}%"  # noqa: E731
aware = lambda name: "AWARENESS" in name.upper()  # noqa: E731


def light(x, aw):
    if aw:
        return "⚪"
    c = met(x)[3]
    if c is None:
        return "🔴" if x["spend"] >= 30 else "⚪"
    return "🟢" if c <= 15 else ("🟡" if c < 30 else "🔴")


def res(x, aw):
    return f"{x['tp']:,} TP" if aw else str(x["lead"])


def main():
    acc = cfg()["META_AD_ACCOUNT_ID"]
    now = datetime.now(timezone(timedelta(hours=8)))
    # data ikut tempoh (peringkat ad)
    D = {}
    for p, _ in PRESETS:
        D[p] = get_all(f"{acc}/insights", {"level": "ad", "date_preset": p, "fields": FIELDS, "limit": "500"})
    # data per jam hari ini (peringkat campaign) untuk 3 jam terkini & 3 jam sebelumnya
    hourly = get_all(f"{acc}/insights", {"level": "campaign", "date_preset": "today", "limit": "500",
                                          "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone",
                                          "fields": "campaign_name,spend,impressions,inline_link_clicks,actions,video_thruplay_watched_actions"})
    hours = sorted({int(r["hourly_stats_aggregated_by_advertiser_time_zone"][:2]) for r in hourly})
    last = hours[-3:] if hours else []
    prev = [h for h in hours if h < (last[0] if last else 0)][-3:]
    hlabel = lambda hs: f"{hs[0]:02d}:00–{hs[-1] + 1:02d}:00" if hs else "—"  # noqa: E731

    # agregat
    camp = defaultdict(lambda: defaultdict(z))      # camp[c][window]
    aset = defaultdict(lambda: defaultdict(z))      # aset[(c,s)][window]
    ad = defaultdict(lambda: defaultdict(z))        # ad[(c,s,a)][window]
    for p, _ in PRESETS:
        for r in D[p]:
            k = (r["campaign_name"], r["adset_name"], r["ad_name"])
            add(camp[k[0]][p], r); add(aset[k[:2]][p], r); add(ad[k][p], r)
    for r in hourly:
        h = int(r["hourly_stats_aggregated_by_advertiser_time_zone"][:2])
        if h in last:
            add(camp[r["campaign_name"]]["h3"], r)
        elif h in prev:
            add(camp[r["campaign_name"]]["h3p"], r)
    WIN = [("h3", f"3 jam terkini ({hlabel(last)})"), ("h3p", f"3 jam sebelumnya ({hlabel(prev)})")] + PRESETS

    def total(window, leadgen_only):
        t = z()
        for c, w in camp.items():
            if leadgen_only and aware(c):
                continue
            x = w[window]
            for k in t:
                t[k] += x[k]
        return t

    L = [f"# Report Iklan MO2 — {now:%d %b %Y}, {now:%I:%M %p}",
         "Data Meta (hari ini belum muktamad). Lead = WhatsFormSubmit + Website lead (chat tidak dikira). "
         "7 hari = 7 hari penuh sebelum hari ini. Bulan ini termasuk hari ini.\n"]

    # Ringkasan
    L += ["## Ringkasan (campaign lead-gen, tanpa Awareness)",
          "| Tempoh | Spend | Lead | CPL | CPM | CTR |", "|---|---|---|---|---|---|"]
    for w, lab in WIN:
        t = total(w, True); cpm, ctr, _, cpl = met(t)
        L.append(f"| {lab} | {rm(t['spend'])} | {t['lead']} | {rm(cpl)} | {rm(cpm)} | {pc(ctr)} |")
    td = total("today", False)
    L.append(f"\nSpend semua iklan hari ini (termasuk Awareness): **{rm(td['spend'])}** daripada had RM{BUDGET_CAP} "
             f"({td['spend'] / BUDGET_CAP * 100:.0f}%).\n")

    # 1. Campaign
    L.append("## 1. Ikut campaign")
    for c in sorted(camp, key=lambda c: -camp[c]["today"]["spend"]):
        if camp[c]["today"]["spend"] <= 0 and camp[c]["yesterday"]["spend"] <= 0:
            continue  # campaign tak aktif (cth TESTING 2 lama)
        aw = aware(c)
        L += [f"\n**{light(camp[c]['today'], aw)} {c}**", "",
              f"| Tempoh | Spend | Impr. | CPM | Klik | CTR | CPC | {'ThruPlay' if aw else 'Lead'} | {'—' if aw else 'CPL'} |",
              "|---|---|---|---|---|---|---|---|---|"]
        for w, lab in WIN:
            x = camp[c][w]; cpm, ctr, cpc, cpl = met(x)
            r_ = "— (tiada data per jam)" if aw and w in ("h3", "h3p") else res(x, aw)
            L.append(f"| {lab} | {rm(x['spend'])} | {x['imp']:,} | {rm(cpm)} | {x['clk']:,} | {pc(ctr)} | {rm(cpc)} | "
                     f"{r_} | {'—' if aw else rm(cpl)} |")

    # 2. Ad set & 3. Ad
    def block(title, data, key_fmt):
        out = [f"\n## {title}",
               "| | Nama | Hari ini: Spend · CPM · Lead · CPL | Semalam: Spend · Lead · CPL | 7 hari: Spend · Lead · CPL | Bulan ini: Lead · CPL |",
               "|---|---|---|---|---|---|"]
        for k in sorted(data, key=lambda k: (k[0], -data[k]["today"]["spend"], -data[k]["this_month"]["spend"])):
            w = data[k]
            if w["today"]["spend"] <= 0 and w["yesterday"]["spend"] <= 0:
                continue  # hanya yang jalan hari ini / semalam
            aw = aware(k[0]); t, y, s, m_ = w["today"], w["yesterday"], w["last_7d"], w["this_month"]
            out.append(f"| {light(t, aw)} | {key_fmt(k)} | {rm(t['spend'])} · {rm(met(t)[0])} · {res(t, aw)} · {'—' if aw else rm(met(t)[3])} | "
                       f"{rm(y['spend'])} · {res(y, aw)} · {'—' if aw else rm(met(y)[3])} | "
                       f"{rm(s['spend'])} · {res(s, aw)} · {'—' if aw else rm(met(s)[3])} | "
                       f"{res(m_, aw)} · {'—' if aw else rm(met(m_)[3])} |")
        return out
    L += block("2. Ikut ad set", aset, lambda k: f"{k[1]}<br><sub>{k[0][:30]}</sub>")
    L += block("3. Ikut ad", ad, lambda k: f"{k[2]}<br><sub>{k[1][:40]}</sub>")

    # Amaran
    warn = []
    for k, w in ad.items():
        if aware(k[0]):
            continue
        t = w["today"]; cpl = met(t)[3]
        if t["lead"] == 0 and t["spend"] >= 30:
            warn.append(f"- 🔴 **{k[2]}**: spend {rm(t['spend'])} hari ini, **0 lead**")
        elif cpl and cpl >= 30 and t["spend"] >= 30:
            warn.append(f"- 🟡 **{k[2]}**: CPL hari ini {rm(cpl)}")
    if td["spend"] > BUDGET_CAP:
        warn.append(f"- 🔴 Spend hari ini {rm(td['spend'])} melebihi had RM{BUDGET_CAP}")
    L += ["\n## Amaran"] + (warn or ["- Tiada amaran setakat ini."])
    L.append("\n_🟢 CPL ≤ RM15 · 🟡 < RM30 · 🔴 ≥ RM30 atau 0 lead dgn spend ≥ RM30 · ⚪ Awareness / data belum cukup. "
             "Report sahaja — tiada perubahan dibuat di Meta._")
    md = "\n".join(L)
    if "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w").write(md)
    print(md)


if __name__ == "__main__":
    main()
