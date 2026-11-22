"""Ad set RETARGETING PCS (RM50, mula 23 Nov 05:00 MYT, PAUSED) dalam campaign 161126 / PCS 26 / LEADS / ABO.
Include 13 audience, exclude 5, 8 centre. Ad dicipta kemudian (lihat created.json)."""
import json, ssl, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from meta_api import cfg

ACC = "act_863467445706037"; CAMPAIGN = "120249139034590618"; PIXEL = "907174708060871"
OUT = Path(__file__).with_name("pcs_retargeting_231126_created.json")
created = json.loads(OUT.read_text()) if OUT.exists() else {}
TOKEN = cfg()["META_ACCESS_TOKEN"]
CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")

def api(method, path, params=None):
    url = f"https://graph.facebook.com/v23.0/{path}"
    p = dict(params or {})
    if TOKEN and TOKEN != "proxy-injected": p["access_token"] = TOKEN
    data = None
    if method == "GET": url += "?" + urllib.parse.urlencode(p)
    else: data = urllib.parse.urlencode({k:(json.dumps(v) if isinstance(v,(dict,list)) else v) for k,v in p.items()}).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"GAGAL {method} {path}: {json.load(e).get('error',{}).get('message')}")

INCLUDE = ["120212792524250739","120212792541490739","120212792542920739","120212792571760739",
           "120212649845690618","120212649899160618","120247964873540618","120241529882410618",
           "120246754652980618","120212649816320618","120212792605420739","120248184902730618","120249233358010618"]
EXCLUDE = ["120249061680340618","120249061506600618","120248184920120618","120212962689280618","120212962805360618"]
PINS = [(2.946842,101.723567),(2.959873,101.75366),(3.151914,101.759052),(3.177433,101.73845),
        (3.198296,101.745006),(3.242194,101.704546)]
PLACES = [("1916025131952167","Melawati Mall",3.2104149080587,101.74856236861),
          ("325660801248263","KL Traders Square",3.2039103822787,101.70343734495)]

targeting = {
    "geo_locations": {
        "custom_locations": [{"latitude":a,"longitude":b,"radius":4,"distance_unit":"mile"} for a,b in PINS],
        "places": [{"key":k,"name":n,"latitude":a,"longitude":b,"radius":4,"distance_unit":"mile"} for k,n,a,b in PLACES],
        "location_types": ["home","recent"]},
    "age_min": 18, "age_max": 65, "age_range": [30,50], "genders": [2],
    "locales": [6,24,41],
    "custom_audiences": [{"id": i} for i in INCLUDE],
    "excluded_custom_audiences": [{"id": i} for i in EXCLUDE],
    "brand_safety_content_filter_levels": ["FACEBOOK_RELAXED"],
    "targeting_automation": {"advantage_audience": 1},
}

if "adset" not in created:
    r = api("POST", f"{ACC}/adsets", {
        "name": "231126 / RETARGETING PCS / WOMEN / 30-50 / RM50",
        "campaign_id": CAMPAIGN, "daily_budget": "5000", "billing_event": "IMPRESSIONS",
        "optimization_goal": "OFFSITE_CONVERSIONS", "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "promoted_object": {"pixel_id": PIXEL, "custom_event_type": "OTHER", "custom_event_str": "WhatsFormSubmit"},
        "attribution_spec": [{"event_type":"CLICK_THROUGH","window_days":7},{"event_type":"VIEW_THROUGH","window_days":1},
                             {"event_type":"ENGAGED_VIDEO_VIEW","window_days":1}],
        "targeting": targeting, "start_time": "2026-11-23T05:00:00+0800", "status": "PAUSED",
        "regional_regulated_categories": ["MALAYSIA_UNIVERSAL","VOLUNTARY_VERIFICATION"],
        "regional_regulation_identities": {"universal_beneficiary":"1737602371705472","universal_payer":"1737602371705472"}})
    created["adset"] = r["id"]; OUT.write_text(json.dumps(created, indent=1))
    print("Ad set PAUSED:", r["id"])
print("SIAP", json.dumps(created))
