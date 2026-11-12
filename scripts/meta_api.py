"""Klien Meta Marketing API ringan (stdlib sahaja). Token dibaca dari .env, tak pernah di-print."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env(path=ROOT / ".env"):
    if not path.exists():
        raise SystemExit(f"Fail {path} tak jumpa.")
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def cfg():
    load_env()
    c = {k: os.environ.get(k, "") for k in
         ("META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "META_PAGE_ID", "META_API_VERSION")}
    missing = [k for k in ("META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID") if not c[k] or c[k] == "act_"]
    if missing:
        raise SystemExit("Isi dulu dalam .env: " + ", ".join(missing))
    if not c["META_AD_ACCOUNT_ID"].startswith("act_"):
        c["META_AD_ACCOUNT_ID"] = "act_" + c["META_AD_ACCOUNT_ID"]
    c["META_API_VERSION"] = c["META_API_VERSION"] or "v23.0"
    return c


def get(path, params=None):
    c = cfg()
    p = dict(params or {})
    p["access_token"] = c["META_ACCESS_TOKEN"]
    url = f"https://graph.facebook.com/{c['META_API_VERSION']}/{path}?{urllib.parse.urlencode(p)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        err = json.load(e).get("error", {})
        raise SystemExit(f"Meta API ralat code {err.get('code')}: {err.get('message')}")


def get_all(path, params=None):
    """Ikut paging sampai habis."""
    out, data = [], get(path, params)
    while True:
        out += data.get("data", [])
        nxt = data.get("paging", {}).get("next")
        if not nxt:
            return out
        with urllib.request.urlopen(nxt, timeout=60) as r:
            data = json.load(r)
