"""Bina campaign PCS (16 Nov 2026) di MO2: Leads, ABO, 3 ad set (Poster / Zon A / Zon B), existing post.
Campaign PAUSED (owner aktifkan), ad set & ad ACTIVE, mula 16 Nov 05:00 MYT. Rekod ID dalam created.json."""
import json, ssl, urllib.parse, urllib.request
from pathlib import Path

V = "v23.0"; ACC = "act_863467445706037"; PAGE = "106138047883616"; PIXEL = "907174708060871"; IG_USER = "17841440990166553"
CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
OUT = Path(__file__).with_name("pcs_161126_created.json")
created = json.loads(OUT.read_text()) if OUT.exists() else {}
DATE = "161126"; START = "2026-11-16T05:00:00+0800"

def api(method, path, params=None):
    url = f"https://graph.facebook.com/{V}/{path}"; data = None
    if method == "GET": url += "?" + urllib.parse.urlencode(params or {})
    else: data = urllib.parse.urlencode({k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in (params or {}).items()}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), context=CTX, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        err = json.load(e).get("error", {}); raise SystemExit(f"GAGAL {method} {path}: {err.get('message')} | {err.get('error_user_title','')} {err.get('error_user_msg','')}")
def save(): OUT.write_text(json.dumps(created, indent=1))

# 8 centre PCS, radius 4 batu
R = {"radius": 4, "distance_unit": "mile"}
C = {  # nama: (jenis, data)
    "Melawati":   ("place", {"key": "1916025131952167"}),
    "KLTS":       ("place", {"key": "325660801248263"}),
    "WangsaMaju": ("pin", {"latitude": 3.198296, "longitude": 101.745006}),
    "SriGombak":  ("pin", {"latitude": 3.242194, "longitude": 101.704546}),
    "Ampang":     ("pin", {"latitude": 3.151914, "longitude": 101.759052}),
    "Setiawangsa":("pin", {"latitude": 3.177433, "longitude": 101.738450}),
    "Putrajaya":  ("pin", {"latitude": 2.946842, "longitude": 101.723567}),
    "Bangi":      ("pin", {"latitude": 2.959873, "longitude": 101.753660}),
}
def geo(names):
    g = {"places": [], "custom_locations": [], "location_types": ["home", "recent"]}
    for n in names:
        t, d = C[n]; g["places" if t == "place" else "custom_locations"].append({**d, **R})
    if not g["places"]: del g["places"]
    if not g["custom_locations"]: del g["custom_locations"]
    return g
EXCLUDE = ["120249061680340618", "120249061506600618", "120248184920120618", "120212962689280618", "120212962805360618",
           "120212960698310618", "120247964873540618", "120241529882410618", "120246754652980618", "120212649816320618",
           "120212649845690618"]
src = api("GET", "120249078317580618", {"fields": "targeting"})["targeting"]  # templat Project 1 (umur/jantina/bahasa/brand safety)
def targeting(names):
    return {"geo_locations": geo(names), "age_min": src["age_min"], "age_max": src["age_max"], "age_range": src.get("age_range", [30, 50]),
            "genders": src["genders"], "locales": src["locales"], "excluded_custom_audiences": [{"id": i} for i in EXCLUDE],
            "brand_safety_content_filter_levels": src.get("brand_safety_content_filter_levels", ["FACEBOOK_RELAXED"]),
            "targeting_automation": {"advantage_audience": 1}}

ALL8 = list(C); ZA = ["Melawati", "KLTS", "WangsaMaju", "SriGombak", "Ampang", "Setiawangsa"]; ZB = ["Putrajaya", "Bangi"]
ADSETS = [
    ("POSTER", f"{DATE} / PCS POSTER / 8 CENTRE / WOMEN / 30-50 / RM17", 1700, ALL8, [
        ("poster-pcs-compact-structured-orange-v6-6tahun", "2007194510345885"),
        ("poster-pcs-compact-forest-v7", "2016759306056072"),
        ("poster-pcs-compact-structured-sage-v6-6tahun", "2007194470345889"),
        ("poster-pcs-compact-structured-navy-v6-6tahun", "2007194497012553"),
        ("poster-pcs-compact-structured-orange-navy-v6-6tahun", "2007194477012555")]),
    ("ZONA", f"{DATE} / PCS ZON A / 6 CENTRE / WOMEN / 30-50 / RM30", 3000, ZA, [
        ("PCS_1_2026_final", "2005555933843076"),
        ("2025 pcs 2 lama THUMB", "2017231682675501"),
        ("PCS1 v4 THUMB", "2017231696008833")]),
    ("ZONB", f"{DATE} / PCS ZON B / PJ&BG / WOMEN / 30-50 / RM45", 4500, ZB, [
        ("PCS_4_2026_PJBG_final", "2005742443824425"),
        ("PCS1 v4 THUMB", "2017231689342167"),
        ("PCS_2_2026_PJBG_final", "2005742440491092")]),
]
DOF = {"creative_features_spec": {k: {"enroll_status": "OPT_OUT"} for k in [
    "advantage_plus_creative", "carousel_to_video", "creative_stickers", "pac_relaxation", "product_extensions",
    "reveal_details_over_time", "show_destination_blurbs", "show_summary", "site_extensions", "video_auto_crop", "video_filtering", "video_uncrop"]}}
for k in ("enhance_cta", "inline_comment", "text_optimizations"): DOF["creative_features_spec"][k] = {"enroll_status": "OPT_IN"}

if "campaign" not in created:
    created["campaign"] = api("POST", f"{ACC}/campaigns", {"name": f"{DATE} / PCS 26 / LEADS / ABO", "objective": "OUTCOME_LEADS",
        "buying_type": "AUCTION", "special_ad_categories": [], "status": "PAUSED", "is_adset_budget_sharing_enabled": "false"})["id"]; save()
    print("Campaign", created["campaign"])
for key, name, budget, locs, ads in ADSETS:
    if f"adset_{key}" not in created:
        created[f"adset_{key}"] = api("POST", f"{ACC}/adsets", {"name": name, "campaign_id": created["campaign"], "daily_budget": str(budget),
            "billing_event": "IMPRESSIONS", "optimization_goal": "OFFSITE_CONVERSIONS", "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "promoted_object": {"pixel_id": PIXEL, "custom_event_type": "LEAD"},
            "attribution_spec": [{"event_type": "CLICK_THROUGH", "window_days": 7}, {"event_type": "VIEW_THROUGH", "window_days": 1},
                                 {"event_type": "ENGAGED_VIDEO_VIEW", "window_days": 1}],
            "targeting": targeting(locs), "start_time": START, "status": "ACTIVE",
            "regional_regulated_categories": ["MALAYSIA_UNIVERSAL", "VOLUNTARY_VERIFICATION"],
            "regional_regulation_identities": {"universal_beneficiary": "1737602371705472", "universal_payer": "1737602371705472"}})["id"]; save()
        print("Ad set", key, created[f"adset_{key}"])
    for i, (cname, post) in enumerate(ads, 1):
        tag = f"{key}_{i}"; title = f"{DATE} / PCS / {cname} - {post}"
        if f"creative_{tag}" not in created:
            created[f"creative_{tag}"] = api("POST", f"{ACC}/adcreatives", {"name": title, "object_story_id": f"{PAGE}_{post}",
                "instagram_user_id": IG_USER, "degrees_of_freedom_spec": DOF, "contextual_multi_ads": {"enroll_status": "OPT_OUT"}})["id"]; save()
        if f"ad_{tag}" not in created:
            created[f"ad_{tag}"] = api("POST", f"{ACC}/ads", {"name": title, "adset_id": created[f"adset_{key}"],
                "creative": {"creative_id": created[f"creative_{tag}"]}, "status": "ACTIVE",
                "tracking_specs": [{"action.type": ["offsite_conversion"], "fb_pixel": [PIXEL]}]})["id"]; save()
            print("  Ad", tag, created[f"ad_{tag}"])
print("SIAP")
