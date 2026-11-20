"""Jalankan alert_check.py dan hantar notifikasi ke phone (ntfy.sh) HANYA bila ada isu.

Env yang perlu:
  NTFY_TOPIC   — nama topic ntfy kau (rahsia, jangan letak dalam kod)
  META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, META_API_VERSION — dari GitHub Secrets
Tiada Claude / tiada chat — script biasa, guna usage percuma GitHub Actions.
"""
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        sys.exit("NTFY_TOPIC tak diset")

    res = subprocess.run([sys.executable, str(HERE / "alert_check.py")],
                         capture_output=True, text=True, timeout=300)
    if res.returncode != 0:
        # Ralat teknikal (cth token tamat) — tetap bagi tahu kau
        msg = "Alert MO2 GAGAL jalan. Semak GitHub Actions log."
        body = (res.stderr or res.stdout).strip()[-500:]
        send(topic, "⚠️ Alert MO2 gagal", msg + "\n" + body, priority="high")
        sys.exit(1)

    out = res.stdout.strip()
    print(out)  # untuk log GitHub Actions
    if not out.startswith("ADA ISU"):
        return  # tiada isu — senyap, tak hantar apa-apa

    send(topic, "🚨 Alert Iklan MO2", out, priority="high")


def send(topic, title, message, priority="default"):
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": priority, "Tags": "warning"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


if __name__ == "__main__":
    main()
