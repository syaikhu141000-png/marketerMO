#!/usr/bin/env python3
"""Ringkasan lead borang dalaman (Google Sheet 'FORM LEADS', tab 'lead monitor')
ikut keyword, untuk banding dengan lead yang Meta Ads report.

Tempoh sama macam section Meta lain: 3 jam terkini, 3 jam sebelumnya, Hari ini, Semalam, 7 hari, Bulan ini.

Input: fail .xlsx penuh sheet tu (download terus, bukan sample).
Timestamp dalam sheet adalah waktu Malaysia (Asia/Kuala_Lumpur), bukan UTC.

Guna standalone: python3 lead_monitor_report.py <path_ke_xlsx> [--md output.md]
Guna sebagai modul: from lead_monitor_report import build_section, period_keyword_counts, group_of
"""
import argparse
import datetime as dt
import re

import openpyxl

# Kumpulan keyword -> campaign, ikut naming pattern ad set/ad sedia ada.
# FWR*, WFM*, FMO* -> campaign "FIZIKAL / WHATSFORM". Selainnya (PCS26, WPCS1, WPCS2, DIRECT WHATSFORM) -> "PCS 26".
def group_of(keyword):
    k = keyword.upper().replace(" ", "")
    if k.startswith("FWR") or k.startswith("WFM") or k.startswith("FMO"):
        return "FIZIKAL"
    return "PCS"


def _load_rows(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if "lead monitor" not in wb.sheetnames:
        return None
    ws = wb["lead monitor"]
    rows = [r for r in ws.iter_rows(values_only=True) if r and r[0] is not None]
    if not rows or rows[0][0] == "TIME":
        rows = rows[1:]
    return rows


def period_keyword_counts(xlsx_path, now=None):
    """Pulangkan {period: {keyword: count}} untuk period dalam
    ('h3','h3p','today','yesterday','last_7d','this_month'), keyword dah UPPER-case."""
    rows = _load_rows(xlsx_path)
    periods = {"h3": {}, "h3p": {}, "today": {}, "yesterday": {}, "last_7d": {}, "this_month": {}}
    if rows is None:
        return periods

    now = now or dt.datetime.now()
    today = now.date()
    yesterday = today - dt.timedelta(days=1)
    h3_from = now - dt.timedelta(hours=3)
    h3p_from = now - dt.timedelta(hours=6)
    seven_d_ago = today - dt.timedelta(days=7)
    month_start = today.replace(day=1)

    for r in rows:
        t = r[0]
        if not isinstance(t, dt.datetime):
            continue
        kw = str(r[1]).strip().upper() if len(r) > 1 and r[1] else "(TIADA KEYWORD)"
        d = t.date()
        if h3_from <= t <= now:
            periods["h3"][kw] = periods["h3"].get(kw, 0) + 1
        elif h3p_from <= t < h3_from:
            periods["h3p"][kw] = periods["h3p"].get(kw, 0) + 1
        if d == today:
            periods["today"][kw] = periods["today"].get(kw, 0) + 1
        if d == yesterday:
            periods["yesterday"][kw] = periods["yesterday"].get(kw, 0) + 1
        if seven_d_ago <= d <= today:
            periods["last_7d"][kw] = periods["last_7d"].get(kw, 0) + 1
        if month_start <= d <= today:
            periods["this_month"][kw] = periods["this_month"].get(kw, 0) + 1
    return periods


_ADSET_TOKEN = re.compile(r"(FWR|WFM|FMO)\s*0*(\d+)")


def match_adset_keyword(adset_name, kwmap):
    """Cari keyword (FWR N / WFM N / FMO N) yang padan dengan nama ad set, pulangkan count atau None
    kalau tiada padanan tepat (cth ad set PCS zon/poster yang tak ada keyword unik per-adset)."""
    m = _ADSET_TOKEN.search(adset_name.upper())
    if not m:
        return None
    token = m.group(1) + m.group(2)
    for kw, n in kwmap.items():
        if kw.replace(" ", "").upper() == token:
            return n
    return None


def group_counts(period_counts):
    """{period: {keyword: n}} -> {period: {'FIZIKAL': n, 'PCS': n, 'TOTAL': n}}"""
    out = {}
    for p, kwmap in period_counts.items():
        g = {"FIZIKAL": 0, "PCS": 0}
        for kw, n in kwmap.items():
            g[group_of(kw)] += n
        g["TOTAL"] = g["FIZIKAL"] + g["PCS"]
        out[p] = g
    return out


def build_section(xlsx_path, now=None):
    """Pulangkan serpihan markdown "## Lead Monitor ..." (overview + pecahan ikut keyword penuh)."""
    counts = period_keyword_counts(xlsx_path, now)
    if all(not v for v in counts.values()):
        rows = _load_rows(xlsx_path)
        if rows is None:
            return "## Lead Monitor (borang dalaman — Google Sheet)\n- ERROR: tab 'lead monitor' tak wujud dalam sheet ni.\n"

    kw_today, kw_y, kw_7d, kw_month = counts["today"], counts["yesterday"], counts["last_7d"], counts["this_month"]
    all_kw = sorted(set(kw_today) | set(kw_y) | set(kw_7d) | set(kw_month), key=lambda k: -kw_month.get(k, 0))

    def s(p):
        return sum(counts[p].values())

    L = []
    L.append("## Lead Monitor (borang dalaman — Google Sheet)")
    L.append(
        "Sumber: tab \"lead monitor\" (Google Sheet FORM LEADS). Ini lead yang benar-benar masuk borang "
        "(WhatsForm/website), *bukan* angka lead Meta Ads Manager — guna untuk trace sama ada dashboard Meta "
        "padan dengan borang sebenar."
    )
    L.append("")
    L.append("| Tempoh | Jumlah lead borang |")
    L.append("|---|---|")
    L.append(f"| 3 jam terkini | {s('h3')} |")
    L.append(f"| Hari ini | {s('today')} |")
    L.append(f"| Semalam | {s('yesterday')} |")
    L.append(f"| 7 hari | {s('last_7d')} |")
    L.append(f"| Bulan ini | {s('this_month')} |")
    L.append("")
    L.append("### Pecahan ikut keyword")
    if all_kw:
        L.append("| Keyword | Hari ini | Semalam | 7 hari | Bulan ini |")
        L.append("|---|---|---|---|---|")
        for kw in all_kw:
            L.append(f"| {kw} | {kw_today.get(kw, 0)} | {kw_y.get(kw, 0)} | {kw_7d.get(kw, 0)} | {kw_month.get(kw, 0)} |")
    else:
        L.append("- Tiada lead borang dalam tempoh ni.")

    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx_path")
    ap.add_argument("--md", default=None)
    ap.add_argument("--now", default=None, help="Override 'sekarang' (ISO, waktu Malaysia) - untuk testing")
    args = ap.parse_args()

    now = dt.datetime.fromisoformat(args.now) if args.now else None
    out = build_section(args.xlsx_path, now)
    if args.md:
        with open(args.md, "w") as f:
            f.write(out)
    else:
        print(out)


if __name__ == "__main__":
    main()
