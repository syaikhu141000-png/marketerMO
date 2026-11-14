"""Deploy Worker dashboard MO2 ke Cloudflare melalui API (tanpa wrangler).

Guna:
  CLOUDFLARE_API_TOKEN=<token> python3 worker/deploy.py [--seed fail.json]
Dalam sesi Claude, token disuntik oleh proxy (nilai env "proxy-injected").
Langkah: KV namespace -> upload script (modul) -> workers.dev -> (tiada cron) -> secret REFRESH_KEY (sekali) -> seed data (pilihan).
"""
import json
import os
import secrets
import ssl
import sys
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "mo2-dashboard"
CRON = None  # tiada cron di Worker: enjin harian jalan di GitHub Actions (percuma, tiada had CPU 10ms)
VARS = {"META_AD_ACCOUNT_ID": "act_863467445706037", "META_API_VERSION": "v23.0"}
API = "https://api.cloudflare.com/client/v4"
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "proxy-injected")
CTX = ssl.create_default_context(cafile=os.environ.get("CF_CA_BUNDLE")) if os.environ.get("CF_CA_BUNDLE") else ssl.create_default_context()


def call(method, path, body=None, ctype="application/json", raw=False):
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode()
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
            out = r.read()
    except urllib.error.HTTPError as e:
        out = e.read()
    if raw:
        return out
    j = json.loads(out)
    if not j.get("success", False):
        raise SystemExit(f"{method} {path} gagal: {j.get('errors')}")
    return j.get("result")


def multipart(parts):
    b = "----mo2" + uuid.uuid4().hex
    out = b""
    for name, filename, ctype, content in parts:
        out += f"--{b}\r\nContent-Disposition: form-data; name=\"{name}\"" .encode()
        if filename:
            out += f"; filename=\"{filename}\"".encode()
        out += f"\r\nContent-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n"
    return out + f"--{b}--\r\n".encode(), f"multipart/form-data; boundary={b}"


acct = call("GET", "/accounts")[0]["id"]
print("Akaun:", acct)

# 1) KV
ns = next((n for n in call("GET", f"/accounts/{acct}/storage/kv/namespaces?per_page=100") if n["title"] == NAME), None)
if not ns:
    ns = call("POST", f"/accounts/{acct}/storage/kv/namespaces", {"title": NAME})
print("KV:", ns["id"])

# 2) Script
src = HERE / "src"
meta = {"main_module": "index.js", "compatibility_date": "2025-01-01",
        "bindings": [{"type": "kv_namespace", "name": "KV", "namespace_id": ns["id"]}] +
                    [{"type": "plain_text", "name": k, "text": v} for k, v in VARS.items()],
        "keep_bindings": ["secret_text"]}
body, ctype = multipart([
    ("metadata", None, "application/json", json.dumps(meta).encode()),
    ("index.js", "index.js", "application/javascript+module", (src / "index.js").read_bytes()),
    ("build.js", "build.js", "application/javascript+module", (src / "build.js").read_bytes()),
    ("dashboard.html", "dashboard.html", "text/plain", (src / "dashboard.html").read_bytes()),
    ("README.md", "README.md", "text/plain", (src / "README.md").read_bytes()),
])
call("PUT", f"/accounts/{acct}/workers/scripts/{NAME}", body, ctype)
print("Script dimuat naik")

# 3) workers.dev + 4) cron
call("POST", f"/accounts/{acct}/workers/scripts/{NAME}/subdomain", {"enabled": True, "previews_enabled": False})
call("PUT", f"/accounts/{acct}/workers/scripts/{NAME}/schedules", [{"cron": CRON}] if CRON else [])
sub = call("GET", f"/accounts/{acct}/workers/subdomain")["subdomain"]
print("Cron:", CRON, "| URL:", f"https://{NAME}.{sub}.workers.dev/")

# 5) REFRESH_KEY (sekali sahaja; disimpan dalam worker/.refresh_key yang di-gitignore)
keyfile = HERE / ".refresh_key"
names = {s["name"] for s in call("GET", f"/accounts/{acct}/workers/scripts/{NAME}/secrets")}
if "REFRESH_KEY" not in names or not keyfile.exists():
    key = secrets.token_urlsafe(24)
    call("PUT", f"/accounts/{acct}/workers/scripts/{NAME}/secrets", {"name": "REFRESH_KEY", "text": key, "type": "secret_text"})
    keyfile.write_text(key)
    print("REFRESH_KEY baru disimpan dalam worker/.refresh_key")
print("Secrets sedia ada:", sorted(names | {"REFRESH_KEY"}))

# 6) Seed data (pilihan)
if "--seed" in sys.argv:
    f = Path(sys.argv[sys.argv.index("--seed") + 1])
    call("PUT", f"/accounts/{acct}/storage/kv/namespaces/{ns['id']}/values/data", f.read_bytes(), "application/octet-stream", raw=True)
    print("Data awal dimasukkan dari", f.name)
