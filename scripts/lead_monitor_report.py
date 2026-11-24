#!/usr/bin/env python3
"""Ringkasan lead borang dalaman (Google Sheet 'FORM LEADS', tab 'lead monitor')
ikut keyword, untuk banding dengan lead yang Meta Ads report.

Input: fail .xlsx penuh sheet tu (download terus, bukan sample).
Timestamp dalam sheet adalah waktu Malaysia (Asia/Kuala_Lumpur), bukan UTC.

Guna: python3 lead_monitor_report.py <path_ke_xlsx> [--md output.md]
"""
import argparse
import datetime as dt
import sys

import openpyxl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx_path")
    ap.add_argument("--md", default=None)
    ap.add_argument("--now", default=None, help="Override 'sekarang' (ISO, waktu Malaysia) - untuk testing")
    args = ap.parse_args()

    wb = openpyxl.load_workbook(args.xlsx_path, read_only=True, data_only=True)
    if "lead monitor" not in wb.sheetnames:
        print("ERROR: tab 'lead monitor' tak wujud dalam sheet ni.", file=sys.stderr)
        sys.exit(1)
    ws = wb["lead monitor"]
    rows = [r for r in ws.iter_rows(values_only=True) if r and r[0] is not None]
    if not rows or rows[0][0] == "TIME":
        rows = rows[1:]

    now = dt.datetime.fromisoformat(args.now) if args.now else dt.datetime.now()
    today = now.date()
    yesterday = today - dt.timedelta(days=1)
    three_h_ago = now - dt.timedelta(hours=3)
    seven_d_ago = today - dt.timedelta(days=7)

    def in_today(t):
        return t.date() == today

    def in_yesterday(t):
        return t.date() == yesterday

    def in_last_3h(t):
        return three_h_ago <= t <= now

    def in_last_7d(t):
        return seven_d_ago <= t.date() <= today

    today_rows, y_rows, h3_rows, d7_rows = [], [], [], []
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

    def by_keyword(lst):
        d = {}
        for kw in lst:
            d[kw] = d.get(kw, 0) + 1
        return d

    kw_today = by_keyword(today_rows)
    kw_3h = by_keyword(h3_rows)

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
    L.append("")
    L.append("### Pecahan ikut keyword — Hari ini")
    if kw_today:
        L.append("| Keyword | Lead borang (hari ini) | Lead borang (3 jam terkini) |")
        L.append("|---|---|---|")
        for kw in sorted(kw_today, key=lambda k: -kw_today[k]):
            L.append(f"| {kw} | {kw_today[kw]} | {kw_3h.get(kw, 0)} |")
    else:
        L.append("- Tiada lead borang hari ini setakat ini.")
    if bad:
        L.append("")
        L.append(f"_Nota: {bad} baris diabaikan sebab format masa tak sah._")

    out = "\n".join(L) + "\n"
    if args.md:
        with open(args.md, "w") as f:
            f.write(out)
    else:
        print(out)


if __name__ == "__main__":
    main()
