"""Report MO2 (setiap 6 jam): Campaign -> Ad set -> Ad, dengan 6 tempoh:
6 jam terkini · 6 jam sebelumnya · Hari ini · Semalam · 7 hari (tidak termasuk hari ini) · Bulan ini.
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

    lead_xlsx = sys.argv[sys.argv.index("--lead-xlsx") + 1] if "--lead-xlsx" in sys.argv else None
    borang = None
    if lead_xlsx:
        from lead_monitor_report import period_keyword_counts, group_counts, group_of
        kw_counts = period_keyword_counts(lead_xlsx, now.replace(tzinfo=None))
        borang = group_counts(kw_counts)  # {window: {'FIZIKAL':n,'PCS':n,'TOTAL':n}}

    UNRELIABLE_BORANG_WINDOWS = {"last_7d", "this_month"}  # tracking gsheet baru reliable dari semalam

    def borang_val(window, key):
        if window in UNRELIABLE_BORANG_WINDOWS:
            return "—"
        return str(borang[window][key])

    def campaign_group(name):
        # Padankan nama campaign dengan kumpulan keyword borang (FIZIKAL / PCS).
        u = name.upper()
        if "FIZIKAL" in u:
            return "FIZIKAL"
        if "PCS" in u:
            return "PCS"
        return None
    # data ikut tempoh (peringkat ad)
    D = {}
    for p, _ in PRESETS:
        D[p] = get_all(f"{acc}/insights", {"level": "ad", "date_preset": p, "fields": FIELDS, "limit": "500"})
    # data per jam hari ini (peringkat campaign) untuk 3 jam terkini & 3 jam sebelumnya
    hourly = get_all(f"{acc}/insights", {"level": "campaign", "date_preset": "today", "limit": "500",
                                          "breakdowns": "hourly_stats_aggregated_by_advertiser_time_zone",
                                          "fields": "campaign_name,spend,impressions,inline_link_clicks,actions,video_thruplay_watched_actions"})
    hours = sorted({int(r["hourly_stats_aggregated_by_advertiser_time_zone"][:2]) for r in hourly})
    last = hours[-6:] if hours else []
    prev = [h for h in hours if h < (last[0] if last else 0)][-6:]
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
    WIN = [("h3", f"6 jam terkini ({hlabel(last)})"), ("h3p", f"6 jam sebelumnya ({hlabel(prev)})")] + PRESETS

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
    lb_col = " Lead borang (gsheet) |" if borang else ""
    L += ["## Ringkasan (campaign lead-gen, tanpa Awareness)",
          f"| Tempoh | Spend | Lead | CPL | CPM | CTR |{lb_col}", f"|---|---|---|---|---|---|{'---|' if borang else ''}"]
    for w, lab in WIN:
        t = total(w, True); cpm, ctr, _, cpl = met(t)
        lb = f" {borang_val(w, 'TOTAL')} |" if borang else ""
        L.append(f"| {lab} | {rm(t['spend'])} | {t['lead']} | {rm(cpl)} | {rm(cpm)} | {pc(ctr)} |{lb}")
    td = total("today", False)
    L.append(f"\nSpend semua iklan hari ini (termasuk Awareness): **{rm(td['spend'])}**.\n")

    # 1. Campaign
    L.append("## 1. Ikut campaign")
    for c in sorted(camp, key=lambda c: -camp[c]["today"]["spend"]):
        if camp[c]["today"]["spend"] <= 0 and camp[c]["yesterday"]["spend"] <= 0:
            continue  # campaign tak aktif (cth TESTING 2 lama)
        aw = aware(c)
        grp = None if aw else campaign_group(c)
        lb_col = " Lead borang (gsheet) |" if (borang and grp) else ""
        L += [f"\n**{light(camp[c]['today'], aw)} {c}**", "",
              f"| Tempoh | Spend | Impr. | CPM | Klik | CTR | CPC | {'ThruPlay' if aw else 'Lead'} | {'—' if aw else 'CPL'} |{lb_col}",
              f"|---|---|---|---|---|---|---|---|---|{'---|' if lb_col else ''}"]
        for w, lab in WIN:
            x = camp[c][w]; cpm, ctr, cpc, cpl = met(x)
            r_ = "— (tiada data per jam)" if aw and w in ("h3", "h3p") else res(x, aw)
            lb = f" {borang_val(w, grp)} |" if (borang and grp) else ""
            L.append(f"| {lab} | {rm(x['spend'])} | {x['imp']:,} | {rm(cpm)} | {x['clk']:,} | {pc(ctr)} | {rm(cpc)} | "
                     f"{r_} | {'—' if aw else rm(cpl)} |{lb}")

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
    def today_detail(title, data, key_fmt, match_borang=False):
        lb_col = " Lead borang (gsheet) |" if (borang and match_borang) else ""
        out = [f"\n## {title}", f"| | Nama | Spend | Impr. | CPM | Klik | CTR | CPC | Lead | CPL |{lb_col}",
               f"|---|---|---|---|---|---|---|---|---|---|{'---|' if lb_col else ''}"]
        for k in sorted(data, key=lambda k: (k[0], -data[k]["today"]["spend"])):
            t = data[k]["today"]
            if t["spend"] <= 0:
                continue
            aw = aware(k[0]); cpm, ctr, cpc, cpl = met(t)
            lb = ""
            if lb_col:
                from lead_monitor_report import match_adset_keyword
                n = match_adset_keyword(k[1], kw_counts["today"])
                lb = f" {n if n is not None else '—'} |"
            out.append(f"| {light(t, aw)} | {key_fmt(k)} | {rm(t['spend'])} | {t['imp']:,} | {rm(cpm)} | {t['clk']:,} | {pc(ctr)} | "
                       f"{rm(cpc)} | {res(t, aw)} | {'—' if aw else rm(cpl)} |{lb}")
        return out
    L += today_detail("2. Ad set — Hari ini (detail)", aset, lambda k: f"{k[1]}<br><sub>{k[0][:30]}</sub>", match_borang=True)
    L += block("3. Ad set — banding tempoh", aset, lambda k: f"{k[1]}<br><sub>{k[0][:30]}</sub>")
    L += today_detail("4. Ad — Hari ini (detail)", ad, lambda k: f"{k[2]}<br><sub>{k[1][:40]}</sub>")
    L += block("5. Ad — banding tempoh", ad, lambda k: f"{k[2]}<br><sub>{k[1][:40]}</sub>")

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
    L += ["\n## Amaran"] + (warn or ["- Tiada amaran setakat ini."])
    L.append("\n_🟢 CPL ≤ RM15 · 🟡 < RM30 · 🔴 ≥ RM30 atau 0 lead dgn spend ≥ RM30 · ⚪ Awareness / data belum cukup. "
             "Report sahaja — tiada perubahan dibuat di Meta._")

    if "--lead-xlsx" in sys.argv:
        from lead_monitor_report import build_section
        L.append("\n" + build_section(sys.argv[sys.argv.index("--lead-xlsx") + 1], now.replace(tzinfo=None)))

    md = "\n".join(L)
    if "--md" in sys.argv:
        open(sys.argv[sys.argv.index("--md") + 1], "w").write(md)

    if "--live-json" in sys.argv:
        import json
        td = total("today", True)
        cpm, ctr, _, cpl = met(td)
        wf_today = web_today = 0
        for r in D["today"]:
            if aware(r["campaign_name"]):
                continue
            w = f = 0
            for a in r.get("actions") or []:
                v = int(float(a["value"]))
                if a["action_type"] in LEAD:
                    w = max(w, v)
                elif a["action_type"] == FORM:
                    f = v
            wf_today += f
            web_today += w
        live = {
            "ok": True,
            "spend_today": round(td["spend"], 2),
            "leads_today": td["lead"],
            "leads_today_whatsform": wf_today,
            "leads_today_website": web_today,
            "cpl_today": round(cpl, 2) if cpl is not None else None,
            "cpm_today": round(cpm, 2) if cpm is not None else None,
            "ctr_today": round(ctr, 2) if ctr is not None else None,
            "leads_borang_today": borang["today"]["TOTAL"] if borang else None,
            "updated_at": now.isoformat(),
        }
        open(sys.argv[sys.argv.index("--live-json") + 1], "w").write(json.dumps(live))

    print(md)


if __name__ == "__main__":
    main()
