"""Tukar report Markdown (jadual, tajuk, bold) kepada HTML email ringkas dengan gaya inline (selamat untuk Gmail)."""
import html
import re
import sys

TABLE = 'style="border-collapse:collapse;font-size:12px;margin:6px 0 14px;width:100%"'
TH = 'style="background:#1f2937;color:#fff;padding:5px 7px;border:1px solid #d1d5db;text-align:left;white-space:nowrap"'
TD = 'style="padding:5px 7px;border:1px solid #d1d5db;vertical-align:top"'


def inline(s):
    s = html.escape(s, quote=False).replace("&lt;br&gt;", "<br>").replace("&lt;sub&gt;", '<span style="color:#6b7280;font-size:11px">').replace("&lt;/sub&gt;", "</span>")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", s)


def convert(md):
    out, rows = [], []
    def flush():
        if not rows:
            return
        head, body = rows[0], [r for r in rows[2:]]
        out.append(f"<table {TABLE}><tr>" + "".join(f"<th {TH}>{inline(c)}</th>" for c in head) + "</tr>")
        for i, r in enumerate(body):
            bg = ' background:#f9fafb;' if i % 2 else ''
            out.append("<tr>" + "".join(f"<td {TD.replace('vertical-align:top', 'vertical-align:top;' + bg)}>{inline(c)}</td>" for c in r) + "</tr>")
        out.append("</table>"); rows.clear()
    for line in md.splitlines():
        if line.startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")]); continue
        flush()
        if line.startswith("# "):
            out.append(f'<h2 style="font-family:Arial;color:#111827;margin:0 0 4px">{inline(line[2:])}</h2>')
        elif line.startswith("## "):
            out.append(f'<h3 style="font-family:Arial;color:#1d4ed8;margin:18px 0 4px">{inline(line[3:])}</h3>')
        elif line.startswith("- "):
            out.append(f'<div style="margin:2px 0">• {inline(line[2:])}</div>')
        elif line.strip():
            out.append(f'<p style="margin:4px 0">{inline(line)}</p>')
    flush()
    return '<div style="font-family:Arial,sans-serif;font-size:13px;color:#111827;max-width:1100px">' + "\n".join(out) + "</div>"


if __name__ == "__main__":
    print(convert(open(sys.argv[1]).read()))
