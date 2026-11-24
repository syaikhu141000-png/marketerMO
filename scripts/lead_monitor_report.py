#!/usr/bin/env python3
"""Ringkasan lead borang dalaman (Google Sheet 'FORM LEADS', tab 'lead monitor')
ikut keyword, untuk banding dengan lead yang Meta Ads report.

Tempoh sama macam section Meta lain: 3 jam terkini, Hari ini, Semalam, 7 hari, Bulan ini.

Input: fail .xlsx penuh sheet tu (download terus, bukan sample).
Timestamp dalam sheet adalah waktu Malaysia (Asia/Kuala_Lumpur), bukan UTC.

Guna standalone: python3 lead_monitor_report.py <path_ke_xlsx> [--md output.md]
Guna sebagai modul: from lead_monitor_report import build_section
"""
import argparse
import datetime as dt
import sys

import openpyxl


def build_section(xlsx_path, now=None):
    """Pulangkan serpihan markdown "## Lead Monitor ..." dari fail .xlsx sheet FORM LEADS."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if "lead monitor" not in wb.sheetnames:
        return "## Lead Monitor (borang dalaman — Google Sheet)\n- ERROR: tab 'lead monitor' tak wujud dalam sheet ni.\n"
    ws = wb["lead monitor"]
    rows = [r for r in ws.iter_rows(values_only=True) if r and r[0] is not None]
    if not rows or rows[0][0] == "TIME":
        rows = rows[1:]

    now = now or dt.datetime.now()
    today = now.date()
    yesterday = today - dt.timedelta(days=1)
    three_h_ago = now - dt.timedelta(hours=3)
    seven_d_ago = today - dt.timedelta(days=7)
    month_start = today.replace(day=1)

    def in_today(t):
        return t.date() == today

    def in_yesterday(t):
        return t.date() == yesterday

    def in_last_3h(t):
        return three_h_ago <= t <= now

    def in_last_7d(t):
        return seven_d_ago <= t.date() <= today

    def in_this_month(t):
        return month_start <= t.date() <= today

    today_rows, y_rows, h3_rows, d7_rows, month_rows = [], [], [], [], []
    bad = 0
    for r in rows:
        t = r[0]
        if not isinstance(t, dt.datetime):
            bad += 1
            continue
        kw = str(r[1]).strip().upper() if len(r) > 1 and r[1] else "(TIADA KEYWORD)"
        if in_today(t):
            today_rows.append(kw)
        if in_yesterday(t):
            y_rows.append(kw)
        if in_last_3h(t):
            h3_rows.append(kw)
        if in_last_7d(t):
            d7_rows.append(kw)
        if in_this_month(t):
            month_rows.append(kw)

    def by_keyword(lst):
        d = {}
        for kw in lst:
            d[kw] = d.get(kw, 0) + 1
        return d

    kw_today, kw_y, kw_7d, kw_month = (by_keyword(x) for x in (today_rows, y_rows, d7_rows, month_rows))
    all_kw = sorted(set(kw_today) | set(kw_y) | set(kw_7d) | set(kw_month), key=lambda k: -kw_month.get(k, 0))

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
    L.append(f"| 3 jam terkini | {len(h3_rows)} |")
    L.append(f"| Hari ini | {len(today_rows)} |")
    L.append(f"| Semalam | {len(y_rows)} |")
    L.append(f"| 7 hari | {len(d7_rows)} |")
    L.append(f"| Bulan ini | {len(month_rows)} |")
    L.append("")
    L.append("### Pecahan ikut keyword")
    if all_kw:
        L.append("| Keyword | Hari ini | Semalam | 7 hari | Bulan ini |")
        L.append("|---|---|---|---|---|")
        for kw in all_kw:
            L.append(f"| {kw} | {kw_today.get(kw, 0)} | {kw_y.get(kw, 0)} | {kw_7d.get(kw, 0)} | {kw_month.get(kw, 0)} |")
    else:
        L.append("- Tiada lead borang dalam tempoh ni.")
    if bad:
        L.append("")
        L.append(f"_Nota: {bad} baris diabaikan sebab format masa tak sah._")

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
