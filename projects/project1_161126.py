"""Bina Project 1 (16 Nov 2026): 1 campaign, 3 ad set, 3 ad existing post. Ikut SOP_PROJECT_1.md.
Campaign PAUSED (owner aktifkan), ad set & ad ACTIVE, ad set mula 16 Nov 05:00 MYT.
Rekod semua ID yang dicipta dalam created.json (untuk semakan / rollback)."""
import json, ssl, sys, urllib.parse, urllib.request
from pathlib import Path

V = "v23.0"; ACC = "act_863467445706037"; PAGE = "106138047883616"; PIXEL = "907174708060871"; IG_USER = "17841440990166553"
CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
OUT = Path(__file__).with_name("project1_161126_created.json")
created = json.loads(OUT.read_text()) if OUT.exists() else {}

def api(method, path, params=None):
    url = f"https://graph.facebook.com/{V}/{path}"
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params or {})
    else:
        data = urllib.parse.urlencode({k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in (params or {}).items()}).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        err = json.load(e).get("error", {})
        raise SystemExit(f"GAGAL {method} {path}: {err.get('message')} | {err.get('error_user_title','')} {err.get('error_user_msg','')}")

def save():
    OUT.write_text(json.dumps(created, indent=1))

ADS = [  # keyword, nama video, post id, IG media id (dari ad asal)
    ("DIRECT FORM", "kfty feb h19-4-b4", "1774642276934444", "18309150889287776"),
    ("FWR 3", "UP-Tim 2", "1798024114596260", "18140453263506851"),
    ("FWR 9", "KFTY DS 1 SEPT FULL", "1801804417551563", "17883609255524964"),
]
EXCLUDE = ["120249061680340618", "120249061506600618", "120248184920120618", "120212962689280618", "120212962805360618",
           "120212960698310618", "120247964873540618", "120241529882410618", "120246754652980618", "120212649816320618",
           "120212649845690618"]
DATE = "161126"; START = "2026-11-16T05:00:00+0800"

# --- targeting: salin dari ad set templat TESTING 2 terkini, kemudian ikut SOP ---
src = api("GET", "120249078317580618", {"fields": "targeting"})["targeting"]
geo = src["geo_locations"]
places = [{"key": p["key"], "radius": p["radius"], "distance_unit": p["distance_unit"]} for p in geo.get("places", [])]
pins = [{"latitude": c["latitude"], "longitude": c["longitude"], "radius": c["radius"], "distance_unit": c["distance_unit"]} for c in geo.get("custom_locations", [])]
pins.append({"latitude": 3.068474, "longitude": 101.488412, "radius": 4, "distance_unit": "mile"})  # Shah Alam Seksyen 7
assert len(places) + len(pins) == 16, (len(places), len(pins))
targeting = {
    "geo_locations": {"places": places, "custom_locations": pins, "location_types": geo.get("location_types", ["home", "recent"])},
    "age_min": src["age_min"], "age_max": src["age_max"], "age_range": src.get("age_range", [30, 50]),
    "genders": src["genders"], "locales": src["locales"],
    "excluded_custom_audiences": [{"id": i} for i in EXCLUDE],
    "brand_safety_content_filter_levels": src.get("brand_safety_content_filter_levels", ["FACEBOOK_RELAXED"]),
    "targeting_automation": {"advantage_audience": 1},
    # tiada publisher_platforms / positions / device_platforms = Advantage+ placements, semua device
}

# --- 1. campaign ---
if "campaign" not in created:
    r = api("POST", f"{ACC}/campaigns", {"name": f"{DATE} / FIZIKAL / WHATSFORM / ABO", "objective": "OUTCOME_ENGAGEMENT",
        "buying_type": "AUCTION", "special_ad_categories": [], "status": "PAUSED", "is_adset_budget_sharing_enabled": "false"})
    created["campaign"] = r["id"]; save(); print("Campaign:", r["id"])

DOF = {"creative_features_spec": {k: {"enroll_status": "OPT_OUT"} for k in [
    "advantage_plus_creative", "carousel_to_video", "creative_stickers", "enhance_cta", "inline_comment", "pac_relaxation",
    "product_extensions", "reveal_details_over_time", "show_destination_blurbs", "show_summary", "site_extensions",
    "video_auto_crop", "video_filtering", "video_uncrop"]}}
# "standard_enhancements" (bundle) dah deprecated di API: aktifkan komponen standard enhancements untuk video secara individu
DOF["creative_features_spec"]["enhance_cta"] = {"enroll_status": "OPT_IN"}
DOF["creative_features_spec"]["inline_comment"] = {"enroll_status": "OPT_IN"}
DOF["creative_features_spec"]["text_optimizations"] = {"enroll_status": "OPT_IN"}

for kw, video, post, igmedia in ADS:
    k = kw.replace(" ", "_")
    tail = f"{video} - {post}"
    if f"adset_{k}" not in created:
        r = api("POST", f"{ACC}/adsets", {
            "name": f"{DATE} / {kw} / WHATSFORM / ABO / 30-50 / BROAD / WOMEN / RM30 - {tail}",
            "campaign_id": created["campaign"], "daily_budget": "3000", "billing_event": "IMPRESSIONS",
            "optimization_goal": "OFFSITE_CONVERSIONS", "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "promoted_object": {"pixel_id": PIXEL, "custom_event_type": "OTHER", "custom_event_str": "WhatsFormSubmit"},
            "attribution_spec": [{"event_type": "CLICK_THROUGH", "window_days": 7}, {"event_type": "VIEW_THROUGH", "window_days": 1},
                                 {"event_type": "ENGAGED_VIDEO_VIEW", "window_days": 1}],
            "targeting": targeting, "start_time": START, "status": "ACTIVE",
            # pengesahan pengiklan Malaysia: salin dari ad set sedia ada
            "regional_regulated_categories": ["MALAYSIA_UNIVERSAL", "VOLUNTARY_VERIFICATION"],
            "regional_regulation_identities": {"universal_beneficiary": "1737602371705472", "universal_payer": "1737602371705472"}})
        created[f"adset_{k}"] = r["id"]; save(); print("Ad set", kw, r["id"])
    if f"creative_{k}" not in created:
        r = api("POST", f"{ACC}/adcreatives", {"name": f"{DATE} / {kw} / {tail}", "object_story_id": f"{PAGE}_{post}",
            "instagram_user_id": IG_USER,
            "degrees_of_freedom_spec": DOF, "contextual_multi_ads": {"enroll_status": "OPT_OUT"}})
        created[f"creative_{k}"] = r["id"]; save(); print("Creative", kw, r["id"])
    if f"ad_{k}" not in created:
        r = api("POST", f"{ACC}/ads", {"name": f"{DATE} / {kw} / {tail}", "adset_id": created[f"adset_{k}"],
            "creative": {"creative_id": created[f"creative_{k}"]}, "status": "ACTIVE",
            "tracking_specs": [{"action.type": ["offsite_conversion"], "fb_pixel": [PIXEL]}]})
        created[f"ad_{k}"] = r["id"]; save(); print("Ad", kw, r["id"])
print("SIAP", json.dumps(created))
