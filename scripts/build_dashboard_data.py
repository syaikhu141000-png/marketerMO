"""Jana docs/data.json untuk dashboard MO2 (format sama dengan Dashboard-MO-v3, 10 seksyen) terus dari Meta Marketing API.

Guna: python3 scripts/build_dashboard_data.py
Lead = WhatsFormSubmit + Website leads. Chat WhatsApp TIDAK dikira. Kempen AWARENESS dikecualikan dari CPL.
Traffic light ikut peraturan dashboard lama:
  OLD (umur >= 14 hari): CPL 7D (fallback 14D)  🟢 <=15 · 🟡 <30 · 🔴 >=30
  NEW (umur < 14 hari) : CPL kalau ada lead, kalau 0 lead ikut spend  🟢 <=30 · 🟡 <=55 · 🔴 >55
"""
import json
import re
from calendar import monthrange
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from meta_api import ROOT, cfg, get, get_all

DEST = ROOT / "docs" / "data.json"
TZ = ZoneInfo("Asia/Kuala_Lumpur")
LEAD_TYPES = {"lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead", "onsite_web_lead"}
FORM_TYPE = "offsite_conversion.fb_pixel_custom"  # WhatsFormSubmit
GUARDRAIL_MIN, GUARDRAIL_MAX = 20, 2700  # had akaun, sama seperti dashboard lama
NEW_DAYS = 14
WINS = ["yesterday", "3D", "7D", "14D", "30D"]


# ---------------- helper ----------------
def r2(x):
    return None if x is None else round(x, 2)


def leads_of(actions):
    web = form = 0
    for a in actions or []:
        v = int(float(a["value"]))
        if a["action_type"] in LEAD_TYPES:
            web = max(web, v)
        elif a["action_type"] == FORM_TYPE:
            form = v
    return form, web


def stat(r):
    form, web = leads_of(r.get("actions"))
    return {"spend": float(r.get("spend") or 0), "impressions": int(float(r.get("impressions") or 0)),
            "reach": int(float(r.get("reach") or 0)), "frequency": float(r.get("frequency") or 0),
            "link_click": int(float(r.get("inline_link_clicks") or 0)), "form": form, "web": web, "leads": form + web}


def cpl(spend, leads):
    return r2(spend / leads) if leads else None


def pct(new, old):
    return None if not old or new is None else (new - old) / old * 100


def arrow(new, old, unit="%"):
    p = pct(new, old)
    if p is None:
        return "—"
    if abs(p) < 1:
        return f"≈ stabil ({p:+.1f}{unit})"
    return f"{'▲' if p > 0 else '▼'} {p:+.1f}{unit}"


def tl_old(c, spend):
    if c is None:
        return "🔴 RED" if spend >= 30 else "🟢 GREEN"
    return "🟢 GREEN" if c <= 15 else ("🟡 YELLOW" if c < 30 else "🔴 RED")


def tl_new(v):
    return "🟢 GREEN" if v <= 30 else ("🟡 YELLOW" if v <= 55 else "🔴 RED")


def classify(age, spend7, spend14, leads7, leads14, cpl7, cpl14):
    """Pulangkan (class, traffic_light, basis)."""
    if age is not None and age < NEW_DAYS:
        c = cpl7 if cpl7 is not None else cpl14
        if c is not None:
            return "NEW", tl_new(c), f"CPL-based (RM{c:.2f})"
        s = spend7 if spend7 else spend14
        return "NEW", tl_new(s), f"Spend-based (RM{s:.2f}, 0 leads)"
    c = cpl7 if cpl7 is not None else cpl14
    s = spend7 if spend7 else spend14
    if c is not None:
        return "OLD", tl_old(c, s), f"CPL-based (RM{c:.2f})"
    return "OLD", tl_old(None, s), f"Spend-based (RM{s:.2f}, 0 leads)"


def tlc(t):
    return "red" if "🔴" in t else "yellow" if "🟡" in t else "green" if "🟢" in t else "na"


def age_days(created, today):
    if not created:
        return None
    d = datetime.strptime(created[:10], "%Y-%m-%d").date()
    return (today - d).days


def is_awareness(name, objective=""):
    return bool(re.search(r"AWARENESS|BRAND", name or "", re.I)) or objective == "OUTCOME_AWARENESS"


def action_for(tl, cls, status, c7):
    t = tlc(tl)
    if "PAUSED" in status:
        return "H", "Kekal PAUSED - sahkan dgn owner sama ada nak archive atau re-test dgn creative baru."
    if t == "red":
        if cls == "NEW":
            return "R", "Review spend vs CPL - testing baru, jangan tambah budget sebelum cukup data leads."
        return "R", "Semak/refresh adset & ad lama berprestasi rendah; jangan naikkan budget sebelum CPL turun."
    if t == "yellow":
        return "M", "Monitor - hold budget, pantau trend CPL 7D/14D."
    if c7 is not None and c7 <= 15:
        return "S", "Pertimbang scale budget +20% (perlu approval) - CPL dalam sasaran."
    return "M", "Maintain - teruskan pantau."


# ---------------- tarik data ----------------
c = cfg()
acc = c["META_AD_ACCOUNT_ID"]
info = get(acc, {"fields": "name,currency,timezone_name,business{name}"})
now = datetime.now(TZ)
today = now.date()
Y = today - timedelta(days=1)
m_start = Y.replace(day=1)
lm_end = m_start - timedelta(days=1)
lm_start = lm_end.replace(day=1)
ranges = {
    "yesterday": (Y, Y), "3D": (Y - timedelta(days=2), Y), "7D": (Y - timedelta(days=6), Y),
    "14D": (Y - timedelta(days=13), Y), "30D": (Y - timedelta(days=29), Y),
    "this_month": (m_start, Y), "last_month": (lm_start, lm_end),
}
ytd = (date(Y.year, 1, 1), Y)


def tr(a, b):
    return json.dumps({"since": a.isoformat(), "until": b.isoformat()})


INS = "spend,impressions,reach,frequency,inline_link_clicks,actions"

campaigns = {x["id"]: x for x in get_all(f"{acc}/campaigns", {
    "fields": "id,name,effective_status,objective,created_time,daily_budget", "limit": 200})}
adsets = {x["id"]: x for x in get_all(f"{acc}/adsets", {
    "fields": "id,name,campaign_id,effective_status,daily_budget,created_time", "limit": 500})}
ads = {x["id"]: x for x in get_all(f"{acc}/ads", {
    "fields": "id,name,adset_id,campaign_id,effective_status,created_time", "limit": 500})}
aware_ids = [k for k, v in campaigns.items() if is_awareness(v["name"], v.get("objective"))]


def insights(level, rng, extra=None):
    p = {"level": level, "time_range": tr(*rng), "fields": INS + ("," + extra if extra else ""), "limit": 500}
    if aware_ids and level == "account":
        p["filtering"] = json.dumps([{"field": "campaign.id", "operator": "NOT_IN", "value": aware_ids}])
    return get_all(f"{acc}/insights", p)


# akaun (excl. AWARENESS) per window
acct = {}
for k, rng in ranges.items():
    rows = insights("account", rng)
    acct[k] = stat(rows[0]) if rows else stat({})

# campaign per window
camp_w = {k: {r["campaign_id"]: stat(r) for r in insights("campaign", ranges[k], "campaign_id")} for k in WINS}
adset_w = {k: {r["adset_id"]: stat(r) for r in insights("adset", ranges[k], "adset_id")} for k in ["3D", "7D", "14D"]}
ad_w = {k: {r["ad_id"]: stat(r) for r in insights("ad", ranges[k], "ad_id")} for k in ["7D", "14D"]}

# tahun ini
ytd_acct_rows = get_all(f"{acc}/insights", {"level": "account", "time_range": tr(*ytd), "fields": INS})
ytd_acct = stat(ytd_acct_rows[0]) if ytd_acct_rows else stat({})
ytd_camp = {r["campaign_id"]: stat(r) for r in insights("campaign", ytd, "campaign_id")}

# run sebelum ni (untuk "BARU / Kekal / resolved / status change")
prev = {}
try:
    old = json.loads(DEST.read_text())
    prev = old.get("accounts", {}).get("mo2", {})
except Exception:
    pass
prev_flags = {f["entity"]: f for f in prev.get("section_2_red_flags", {}).get("flags", [])}
prev_camp = {x["campaign"]: x for x in prev.get("section_5_campaign_summary", {}).get("campaigns", [])}


def s0(d, i):
    return d.get(i) or stat({})


# ---------------- Section 5: campaign ----------------
camp_rows = []
for cid, cm in campaigns.items():
    if cid in aware_ids:
        continue
    w = {k: s0(camp_w[k], cid) for k in WINS}
    if w["30D"]["spend"] <= 0 and cm["effective_status"] != "ACTIVE":
        continue
    sp = {k: r2(w[k]["spend"]) for k in WINS}
    ld = {k: w[k]["leads"] for k in WINS}
    cp = {k: cpl(w[k]["spend"], w[k]["leads"]) for k in WINS}
    age = age_days(cm.get("created_time"), today)
    cls, tl, basis = classify(age, sp["7D"], sp["14D"], ld["7D"], ld["14D"], cp["7D"], cp["14D"])
    form30, web30 = w["30D"]["form"], w["30D"]["web"]
    conv = "Website leads" if web30 > form30 or cm.get("objective") == "OUTCOME_LEADS" else "WhatsFormSubmit"
    code, act = action_for(tl, cls, cm["effective_status"], cp["7D"])
    trend = arrow(cp["7D"], cp["14D"]) if cp["7D"] is not None and cp["14D"] is not None else basis
    camp_rows.append({
        "campaign": cm["name"], "status": cm["effective_status"], "class": cls, "age_days": age,
        "spend": sp, "leads": ld, "whatsform_leads": ld, "cpl": cp, "traffic_light": tl,
        "trend": ("CPL 7D vs 14D " + trend) if trend != basis else basis, "basis": basis, "conv_type": conv,
        "frequency_14D": r2(w["14D"]["frequency"]) or None, "action": act, "action_code": code,
    })
camp_rows.sort(key=lambda x: -(x["spend"]["14D"] or 0))

# ---------------- Section 6: adset ----------------
adset_rows = []
for aid, a in adsets.items():
    if a["campaign_id"] in aware_ids:
        continue
    w = {k: s0(adset_w[k], aid) for k in ["3D", "7D", "14D"]}
    if a["effective_status"] != "ACTIVE" and w["14D"]["spend"] <= 0:
        continue
    sp = {k: r2(w[k]["spend"]) for k in w}
    ld = {k: w[k]["leads"] for k in w}
    cp = {k: cpl(w[k]["spend"], w[k]["leads"]) for k in w}
    age = age_days(a.get("created_time"), today)
    cls, tl, basis = classify(age, sp["7D"], sp["14D"], ld["7D"], ld["14D"], cp["7D"], cp["14D"])
    code, act = action_for(tl, cls, a["effective_status"], cp["7D"])
    db = a.get("daily_budget")
    adset_rows.append({
        "adset": a["name"], "campaign": campaigns.get(a["campaign_id"], {}).get("name", ""),
        "status": a["effective_status"], "class": cls, "age_days": age,
        "daily_budget": round(int(db) / 100, 2) if db else None,
        "spend": sp, "leads": ld, "whatsform_leads": ld, "cpl": cp, "traffic_light": tl,
        "trend": arrow(cp["7D"], cp["14D"]) if cp["7D"] is not None and cp["14D"] is not None else basis,
        "frequency_14D": r2(w["14D"]["frequency"]) or None, "action": act, "action_code": code,
    })

# ---------------- Section 7: ads ----------------
def ad_row(adid, s, win_spend7, win_spend14, l7, l14):
    a = ads.get(adid, {})
    age = age_days(a.get("created_time"), today)
    c7, c14 = cpl(win_spend7, l7), cpl(win_spend14, l14)
    cls, tl, basis = classify(age, win_spend7, win_spend14, l7, l14, c7, c14)
    row = {"ad": a.get("name", adid), "adset": adsets.get(a.get("adset_id"), {}).get("name", ""),
           "campaign": campaigns.get(a.get("campaign_id"), {}).get("name", ""),
           "status": a.get("effective_status", "?"), "spend": r2(s["spend"]), "whatsform_leads": s["leads"],
           "cpl": cpl(s["spend"], s["leads"]), "frequency": r2(s["frequency"]) or None,
           "class": cls, "traffic_light": tl, "basis": basis}
    if s["leads"] == 0 and s["spend"] >= 90:
        row["flag"] = f"0 lead dgn spend RM{s['spend']:.2f} - cadang semak/OFF (perlu approval)"
    return row


ads14 = []
for adid, s in ad_w["14D"].items():
    if adid in ads and ads[adid].get("campaign_id") in aware_ids:
        continue
    if s["spend"] >= 20:
        s7 = s0(ad_w["7D"], adid)
        ads14.append(ad_row(adid, s, s7["spend"], s["spend"], s7["leads"], s["leads"]))
ads7 = []
for adid, s in sorted(ad_w["7D"].items(), key=lambda kv: -kv[1]["spend"]):
    if adid in ads and ads[adid].get("campaign_id") in aware_ids:
        continue
    if s["spend"] > 0 and len(ads7) < 40:
        s14 = s0(ad_w["14D"], adid)
        ads7.append(ad_row(adid, s, s["spend"], s14["spend"], s["leads"], s14["leads"]))
ads14.sort(key=lambda x: -x["spend"])

# ---------------- Section 3: overview ----------------
def mrow(s):
    return {"spend": r2(s["spend"]), "leads": s["leads"], "whatsform_leads": s["form"], "website_leads": s["web"],
            "cpl": cpl(s["spend"], s["leads"]), "impressions": s["impressions"], "reach": s["reach"],
            "frequency": round(s["frequency"], 4) if s["frequency"] else None, "link_click": s["link_click"],
            "ctr_pct": r2(s["link_click"] / s["impressions"] * 100) if s["impressions"] else None,
            "cpm": r2(s["spend"] / s["impressions"] * 1000) if s["impressions"] else None}


metrics = {k: mrow(acct[k]) for k in ranges}
m7, m14, m30 = metrics["7D"], metrics["14D"], metrics["30D"]
cpc = lambda m: (m["spend"] / m["link_click"]) if m["link_click"] else None  # noqa: E731

types = {"whatsform": ["WhatsFormSubmit", "conversions:offsite_conversion.fb_pixel_custom.WhatsFormSubmit", 0, 0.0],
         "website_leads": ["Website leads", "actions:offsite_conversion.fb_pixel_lead", 0, 0.0]}
aware_spend_ytd = 0.0
for cid, s in ytd_camp.items():
    if cid in aware_ids:
        aware_spend_ytd += s["spend"]
        continue
    if not s["leads"]:
        continue
    key = "website_leads" if s["web"] > s["form"] else "whatsform"
    types["whatsform"][2] += s["form"]
    types["website_leads"][2] += s["web"]
    types[key][3] += s["spend"]
conv_types = [{"key": k, "label": v[0], "indicator": v[1], "results": v[2], "spend": r2(v[3]), "cpl": cpl(v[3], v[2])}
              for k, v in types.items()]
comb_res = sum(t["results"] for t in conv_types)
comb_sp = sum(t["spend"] or 0 for t in conv_types)
acct_tl = tl_old(m7["cpl"], m7["spend"] or 0)
sec3 = {
    "metrics": metrics,
    "total_this_year": {
        "period": f"{ytd[0]}..{ytd[1]}",
        "note": "Spend/impressions/reach/frequency = semua campaign (termasuk awareness), terus dari API. "
                "Lead = WhatsFormSubmit + Website leads sahaja (chat WhatsApp tidak dikira).",
        "spend": r2(ytd_acct["spend"]), "impressions": ytd_acct["impressions"], "reach": ytd_acct["reach"],
        "frequency": r2(ytd_acct["frequency"]), "conversion_types": conv_types,
        "combined": {"results": comb_res, "spend": r2(comb_sp), "cpl": cpl(comb_sp, comb_res)},
        "excluded_note": f"Dikecualikan dari combined: kempen AWARENESS RM{aware_spend_ytd:,.2f}.",
    },
    "cpl_basis": "CPL gabungan WhatsFormSubmit + Website leads, semua campaign lead-gen (excl. AWARENESS). Chat tidak dikira.",
    "traffic_light_account_cpl": acct_tl,
    "trend_7D_vs_14D": {
        "cpl": arrow(m7["cpl"], m14["cpl"]), "ctr": arrow(m7["ctr_pct"], m14["ctr_pct"]),
        "cpc": arrow(cpc(m7), cpc(m14)), "cpm": arrow(m7["cpm"], m14["cpm"]),
        "cpl_vs_30D": arrow(m7["cpl"], m30["cpl"]),
    },
    "purpose": "Prestasi akaun mengikut window masa (excl. AWARENESS).",
}

# ---------------- Section 4: trend ----------------
series = {k: {"spend": metrics[k]["spend"], "leads": metrics[k]["leads"], "cpl": metrics[k]["cpl"]} for k in WINS}
days = {"yesterday": 1, "3D": 3, "7D": 7, "14D": 14, "30D": 30}
lpd = {k: r2(metrics[k]["leads"] / days[k]) for k in WINS}
slope = r2(m7["cpl"] - m14["cpl"]) if m7["cpl"] is not None and m14["cpl"] is not None else None
obs = (f"CPL 7D {'lebih tinggi' if (slope or 0) > 0 else 'lebih rendah'} drpd 14D, slope RM{slope:+.2f}. " if slope is not None else "") + \
      f"Leads/hari: semalam={lpd['yesterday']}, 7D={lpd['7D']}, 14D={lpd['14D']}, 30D={lpd['30D']}."
sec4 = {"series": series, "cpl_slope_7D_vs_14D": slope, "leads_per_day_3D": lpd["3D"], "leads_per_day_7D": lpd["7D"],
        "leads_per_day_14D": lpd["14D"], "leads_per_day_30D": lpd["30D"], "observation": obs,
        "note": "Window dikira hingga semalam (hari penuh terakhir, waktu Malaysia).",
        "purpose": "Trend spend, leads & CPL merentas window masa."}

# ---------------- Section 2: red flags ----------------
flags = []
active_lead = [x for x in camp_rows if x["status"] == "ACTIVE"]
if not active_lead:
    flags.append({"priority": "P1", "level": "HIGH", "entity": "Akaun " + info["name"], "traffic_light": "🔴 RED",
                  "issue": "Tiada campaign lead-gen ACTIVE - lead baru tak masuk dari akaun ni.",
                  "evidence": {"spend_yesterday": metrics["yesterday"]["spend"] or 0, "leads_yesterday": metrics["yesterday"]["leads"]},
                  "suggested_action": "Sahkan dgn owner sama ada pause ni sengaja. Kalau tak, hidupkan semula campaign terbaik (perlu approval)."})
for x in camp_rows:
    t = tlc(x["traffic_light"])
    if t not in ("red", "yellow") or (x["spend"]["7D"] or 0) <= 0:
        continue
    act = x["status"] == "ACTIVE"
    pr = "P1" if t == "red" and act else "P2" if t == "red" else "P3" if act else "P4"
    was = prev_flags.get(x["campaign"])
    tag = "Kekal" if was and was.get("traffic_light") == x["traffic_light"] else ("BARU" if not was else "Berubah")
    flags.append({"priority": pr, "level": "HIGH" if t == "red" else "LOW", "entity": x["campaign"],
                  "traffic_light": x["traffic_light"],
                  "issue": f"{tag} {tlc(x['traffic_light']).upper()} - {x['basis']} ({x['status']}, {x['age_days']} hari).",
                  "evidence": {"cpl_7D": x["cpl"]["7D"], "cpl_14D": x["cpl"]["14D"], "spend_14D": x["spend"]["14D"]},
                  "suggested_action": x["action"]})
for x in sorted(adset_rows, key=lambda a: -(a["spend"]["7D"] or 0)):
    if tlc(x["traffic_light"]) == "red" and (x["spend"]["7D"] or 0) >= 100 and len(flags) < 12:
        flags.append({"priority": "P2", "level": "HIGH", "entity": x["adset"], "traffic_light": x["traffic_light"],
                      "issue": f"Ad set RED - {x['trend']} (ACTIVE, {x['age_days']} hari).",
                      "evidence": {"cpl_7D": x["cpl"]["7D"], "cpl_14D": x["cpl"]["14D"], "spend_7D": x["spend"]["7D"]},
                      "suggested_action": x["action"]})
order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
flags.sort(key=lambda f: order.get(f["priority"], 9))
for f in flags:  # evidence tanpa None
    f["evidence"] = {k: v for k, v in f["evidence"].items() if v is not None}
cur = {f["entity"]: f for f in flags}
resolved = [{"entity": e, "previous_traffic_light": f.get("traffic_light"),
             "current_traffic_light": (next((c["traffic_light"] for c in camp_rows if c["campaign"] == e), "⚪ tiada data")),
             "note": "Tiada lagi dalam senarai flag run ni."} for e, f in prev_flags.items() if e not in cur]
status_changes = [{"entity": x["campaign"], "from": prev_camp[x["campaign"]]["status"], "to": x["status"]}
                  for x in camp_rows if x["campaign"] in prev_camp and prev_camp[x["campaign"]]["status"] != x["status"]]
sec2 = {"flags": flags, "resolved_since_last_run": resolved, "status_changes_since_last_run": status_changes,
        "note": f"{len(resolved)} resolved, {len(status_changes)} perubahan status berbanding run lepas." if prev else "Run pertama - tiada perbandingan.",
        "purpose": "Senarai campaign/adset bermasalah (RED/YELLOW) + apa yang berubah berbanding run sebelum ni."}

# ---------------- Section 1: budget ----------------
budget = sum(a["daily_budget"] or 0 for a in adset_rows if a["status"] == "ACTIVE")
budget += sum(int(cm["daily_budget"]) / 100 for cid, cm in campaigns.items()
              if cm.get("daily_budget") and cm["effective_status"] == "ACTIVE" and cid not in aware_ids)
sy = metrics["yesterday"]["spend"] or 0
rr = {"avg_daily_spend_3D": r2((metrics["3D"]["spend"] or 0) / 3), "avg_daily_spend_7D": r2((m7["spend"] or 0) / 7),
      "avg_daily_spend_14D": r2((m14["spend"] or 0) / 14)}
if not budget:
    pace = "⚪ Tiada budget lead-gen ACTIVE"
elif rr["avg_daily_spend_7D"] > GUARDRAIL_MAX:
    pace = "🔴 Melebihi guardrail"
elif sy < budget * 0.5:
    pace = "🟡 Underspend (spend semalam < 50% budget)"
else:
    pace = "🟢 Dalam guardrail"
sec1 = {"daily_budget_total_active_ABO": r2(budget), "spend_yesterday": r2(sy),
        "run_rate_vs_budget_pct": r2(sy / budget * 100) if budget else None,
        "guardrail_min": GUARDRAIL_MIN, "guardrail_max": GUARDRAIL_MAX, "recent_daily_run_rate": rr, "pace_status": pace,
        "purpose": "Ringkasan bajet harian akaun: spend semalam, jumlah budget aktif, run-rate vs budget, guardrail, dan trend run-rate 3D/7D/14D.",
        "spend_yesterday_note": f"Spend lead-gen semalam RM{sy:,.2f}" + (f", {sy / budget * 100:.1f}% drpd budget aktif RM{budget:,.2f}." if budget else "."),
        "daily_budget_note": f"Total daily_budget {sum(1 for a in adset_rows if a['status']=='ACTIVE')} adset ACTIVE (excl. AWARENESS) = RM{budget:,.2f}.",
        "run_rate_vs_budget_note": f"Purata spend harian: 3D RM{rr['avg_daily_spend_3D']}, 7D RM{rr['avg_daily_spend_7D']}, 14D RM{rr['avg_daily_spend_14D']}."}

# ---------------- Section 8 & 9 ----------------
lvl = {"P1": "P1 · High", "P2": "P2 · Med", "P3": "P3 · Low", "P4": "P4 · Low"}
items = [{"n": i + 1, "level": f["level"], "priority": lvl.get(f["priority"], f["priority"]), "needs_approval": True,
          "entity": f["entity"], "diagnosis": f["traffic_light"] + " - " + f["issue"],
          "evidence": ", ".join(f"{k} {('RM%.2f' % v) if isinstance(v, float) or k.startswith(('cpl', 'spend')) else v}" for k, v in f["evidence"].items()),
          "action": f["suggested_action"],
          "expected_impact": "Jika action diambil, CPL dijangka stabil/turun dlm 2-5 hari (anggaran, bukan jaminan)."}
         for i, f in enumerate(flags[:6])]
code_of = lambda f: "O" if "Akaun" in f["entity"] else ("H" if "PAUSED" in f["issue"] else ("R" if f["level"] == "HIGH" else "M"))  # noqa: E731
checklist = [{"action": f["suggested_action"], "entity": f["entity"][:40], "reason": f["issue"], "code": code_of(f),
              "status": "PENDING - perlu approval" if f["level"] == "HIGH" else "PENDING - pantau"} for f in flags[:10]]
for x in camp_rows:
    if x["action_code"] == "S" and len(checklist) < 12:
        checklist.append({"action": x["action"], "entity": x["campaign"][:40], "reason": f"CPL 7D RM{x['cpl']['7D']} (GREEN).",
                          "code": "S", "status": "PENDING - perlu approval"})
sec8 = {"items": items, "purpose": "Diagnosis + cadangan tindakan bagi item flag teratas. Semua perlu approval - tiada perubahan automatik di Meta."}
sec9 = {"codes": {"M": "Monitor", "S": "Scale", "R": "Review/Optimize", "H": "Hold/Pause-watch",
                  "O": "Owner confirm needed", "C": "Consider kill/archive"}, "checklist": checklist,
        "purpose": "Senarai tindakan untuk ditanda bila selesai."}

# ---------------- Section 10 ----------------
lm, tm = metrics["last_month"], metrics["this_month"]
dim = monthrange(Y.year, Y.month)[1]
elapsed = (Y - m_start).days + 1
proj_leads = round(tm["leads"] / elapsed * dim) if elapsed else 0
proj_spend = r2((tm["spend"] or 0) / elapsed * dim) if elapsed else None
d_abs = r2(tm["cpl"] - lm["cpl"]) if tm["cpl"] is not None and lm["cpl"] is not None else None
d_pct = r2(pct(tm["cpl"], lm["cpl"])) if d_abs is not None else None
sec10 = {
    "metrics": {"last_month_full": {"cpl": lm["cpl"], "whatsform_leads": lm["leads"], "spend_whatsform_campaigns": lm["spend"]},
                "this_month_MTD": {"cpl": tm["cpl"], "whatsform_leads": tm["leads"], "spend_whatsform_campaigns": tm["spend"]},
                "this_month_projected_full": {"whatsform_leads_proj": proj_leads, "spend_total_proj": proj_spend, "cpl_proj": tm["cpl"]}},
    "delta": {"cpl_abs": d_abs, "cpl_pct": d_pct,
              "verdict": "⚪ Tiada data" if d_abs is None else ("🟢 CPL turun/membaik" if d_abs <= 0 else "🔴 CPL naik/memburuk"),
              "context": f"CPL MTD ({elapsed} hari) RM{tm['cpl']} vs bulan lepas penuh RM{lm['cpl']}. Unjuran bulan ni: ~{proj_leads} leads, spend ~RM{proj_spend}.",
              "recommendation": "Pantau trend beberapa hari lagi sebelum buat keputusan besar." if elapsed < 10 else
                                ("CPL bulan ni lebih tinggi - semak campaign RED di Section 2/3." if (d_abs or 0) > 0 else "CPL bulan ni lebih baik - kekalkan struktur, pertimbang scale yang GREEN.")},
    "purpose": "Banding CPL bulan ini (MTD) vs bulan lepas penuh + unjuran akhir bulan.",
}

# ---------------- _meta & tulis ----------------
notes = []
if not active_lead:
    notes.append("PERHATIAN: Tiada campaign lead-gen ACTIVE dalam akaun ni pada masa data ditarik.")
new_red = [f["entity"] for f in flags if f["issue"].startswith("BARU") and f["level"] == "HIGH"]
if new_red:
    notes.append("RED flag BARU: " + "; ".join(new_red[:3]) + ".")
if status_changes:
    notes.append("Perubahan status: " + "; ".join(f"{s['entity']} {s['from']}->{s['to']}" for s in status_changes[:3]) + ".")
notes.append("Data terus dari Meta Marketing API. Lead = WhatsFormSubmit + Website leads (chat tidak dikira). AWARENESS dikecualikan dari CPL.")

meta = {"dashboard": "Minda Optima — Pantas Baca Daily Monitoring (Minda Optima 2)",
        "account_id": acc.replace("act_", ""), "account_name": info["name"],
        "business_name": (info.get("business") or {}).get("name", ""), "product": "Pantas Baca",
        "currency": info["currency"], "tracking": "WhatsFormSubmit, Website leads",
        "generated_at": now.isoformat(timespec="seconds"),
        "data_source": f"Meta Marketing API {c['META_API_VERSION']} (scripts/build_dashboard_data.py) - time_range tetap, zon Asia/Kuala_Lumpur",
        "date_windows": {k: (f"{a}" if a == b else f"{a}..{b}") for k, (a, b) in ranges.items()},
        "IMPORTANT_NOTES": notes}
out = {"_meta": {"dashboard": "Minda Optima — Pantas Baca Daily Monitoring", "generated_at": meta["generated_at"], "accounts_order": ["mo2"]},
       "accounts": {"mo2": {"_meta": meta, "section_1_budget_card": sec1, "section_2_red_flags": sec2,
                            "section_3_account_overview": sec3, "section_4_performance_trend": sec4,
                            "section_5_campaign_summary": {"campaigns": camp_rows, "purpose": "Ringkasan performance per-campaign (excl. AWARENESS)."},
                            "section_6_adset_summary": {"adsets": adset_rows,
                                                        "purpose": "Ringkasan prestasi adset ACTIVE + adset yang ada spend 14D (excl. AWARENESS) - window 3D/7D/14D.",
                                                        "note": "Traffic light: OLD (>=14 hari) ikut CPL 7D (fallback 14D); NEW ikut CPL kalau ada lead, kalau tiada ikut spend."},
                            "section_7_ads_performance": {"ads_14D": ads14, "ads_7D_top": ads7,
                                                          "purpose": "Ad dgn spend >= RM20 (14D) dan top 40 spender (7D)."},
                            "section_8_diagnostic_recommendation": sec8, "section_9_action_checklist": sec9,
                            "section_10_historical_comparison": sec10}}}
DEST.write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(f"OK {DEST.relative_to(ROOT)}: {len(camp_rows)} campaign, {len(adset_rows)} adset ACTIVE, {len(ads14)} ad 14D, {len(flags)} flag")
