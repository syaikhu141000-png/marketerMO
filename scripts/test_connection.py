"""Uji sambungan: nama akaun, status, mata wang, spend 7 hari. Token tak dipaparkan."""
from meta_api import cfg, get, get_all

STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW",
          8: "PENDING_SETTLEMENT", 9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE",
          101: "CLOSED", 201: "ANY_ACTIVE", 202: "ANY_CLOSED"}

acc = cfg(need_account=False)["META_AD_ACCOUNT_ID"]
if not acc or acc == "act_":
    print("META_AD_ACCOUNT_ID kosong. Akaun yang token ni boleh akses:")
    for x in get_all("me/adaccounts", {"fields": "name,account_id,account_status,currency", "limit": 50}):
        print(f"  act_{x['account_id']}  {x['name']}  ({x['currency']})")
    raise SystemExit("Salin ID yang betul ke .env, kemudian jalankan semula.")
a = get(acc, {"fields": "name,account_status,currency"})
ins = get(f"{acc}/insights", {"date_preset": "last_7d", "fields": "spend"}).get("data", [])
spend = float(ins[0]["spend"]) if ins else 0.0
print("Sambungan berjaya")
print(f"  Akaun   : {a['name']} ({acc[:6]}...)")
print(f"  Status  : {STATUS.get(a['account_status'], a['account_status'])}  ·  Mata wang: {a['currency']}")
print(f"  Spend 7 hari: {a['currency']} {spend:,.2f}")
