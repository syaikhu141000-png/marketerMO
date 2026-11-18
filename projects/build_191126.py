"""19 Nov 2026: (1) ad set FWR 11 dalam Project 1 (PAUSED, mula 19 Nov 05:00), (2) ad PCS 1 (2026) dalam PCS Zon A (PAUSED).
Rekod ID dalam created.json."""
import json, ssl, urllib.parse, urllib.request
from pathlib import Path
V="v23.0"; ACC="act_863467445706037"; PAGE="106138047883616"; PIXEL="907174708060871"; IG_USER="17841440990166553"
CTX=ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
OUT=Path(__file__).with_name("build_191126_created.json"); created=json.loads(OUT.read_text()) if OUT.exists() else {}
def api(m,p,params=None):
    url=f"https://graph.facebook.com/{V}/{p}"; data=None
    if m=="GET": url+="?"+urllib.parse.urlencode(params or {})
    else: data=urllib.parse.urlencode({k:(json.dumps(v) if isinstance(v,(dict,list)) else v) for k,v in (params or {}).items()}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url,data=data,method=m),context=CTX,timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        err=json.load(e).get("error",{}); raise SystemExit(f"GAGAL {m} {p}: {err.get('message')} | {err.get('error_user_title','')} {err.get('error_user_msg','')}")
def save(): OUT.write_text(json.dumps(created,indent=1))
DOF={"creative_features_spec":{k:{"enroll_status":"OPT_OUT"} for k in ["advantage_plus_creative","carousel_to_video","creative_stickers","pac_relaxation","product_extensions","reveal_details_over_time","show_destination_blurbs","show_summary","site_extensions","video_auto_crop","video_filtering","video_uncrop"]}}
for k in ("enhance_cta","inline_comment","text_optimizations"): DOF["creative_features_spec"][k]={"enroll_status":"OPT_IN"}

# --- (1) Fizikal FWR 11: salin setting ad set FWR 9 (templat Project 1) ---
src=api("GET","120249134455220618",{"fields":"campaign_id,daily_budget,billing_event,optimization_goal,bid_strategy,promoted_object,attribution_spec,targeting"})
t=src["targeting"]; g=t["geo_locations"]
geo={"location_types":g.get("location_types",["home","recent"])}
if g.get("places"): geo["places"]=[{"key":p["key"],"radius":p["radius"],"distance_unit":p["distance_unit"]} for p in g["places"]]
if g.get("custom_locations"): geo["custom_locations"]=[{"latitude":c["latitude"],"longitude":c["longitude"],"radius":c["radius"],"distance_unit":c["distance_unit"]} for c in g["custom_locations"]]
targ={"geo_locations":geo,"age_min":t["age_min"],"age_max":t["age_max"],"age_range":t.get("age_range",[30,50]),"genders":t["genders"],"locales":t["locales"],
      "excluded_custom_audiences":[{"id":a["id"]} for a in t.get("excluded_custom_audiences",[])],
      "brand_safety_content_filter_levels":t.get("brand_safety_content_filter_levels",["FACEBOOK_RELAXED"]),"targeting_automation":{"advantage_audience":1}}
assert len(targ["excluded_custom_audiences"])==11 and len(geo.get("places",[]))+len(geo.get("custom_locations",[]))==16
po=src["promoted_object"]; po={"pixel_id":po["pixel_id"],"custom_event_type":po["custom_event_type"],"custom_event_str":po.get("custom_event_str")}
KW,VID,POST="FWR 11","KFTY DS2 SEPT FULL","1802361027495902"
if "adset_fwr11" not in created:
    created["adset_fwr11"]=api("POST",f"{ACC}/adsets",{"name":f"191126 / {KW} / WHATSFORM / ABO / 30-50 / BROAD / WOMEN / RM30 - {VID} - {POST}",
        "campaign_id":src["campaign_id"],"daily_budget":"3000","billing_event":src["billing_event"],"optimization_goal":src["optimization_goal"],
        "bid_strategy":src["bid_strategy"],"promoted_object":po,"attribution_spec":src["attribution_spec"],"targeting":targ,
        "start_time":"2026-11-19T05:00:00+0800","status":"PAUSED",
        "regional_regulated_categories":["MALAYSIA_UNIVERSAL","VOLUNTARY_VERIFICATION"],
        "regional_regulation_identities":{"universal_beneficiary":"1737602371705472","universal_payer":"1737602371705472"}})["id"]; save(); print("Ad set FWR 11",created["adset_fwr11"])
for tag,adset,name,post in (("fwr11",created["adset_fwr11"],f"191126 / {KW} / {VID} - {POST}",POST),
                            ("pcs1",  "120249139041790618","191126 / PCS / PCS 1 (2026) - 2005407593857910","2005407593857910")):
    if f"creative_{tag}" not in created:
        created[f"creative_{tag}"]=api("POST",f"{ACC}/adcreatives",{"name":name,"object_story_id":f"{PAGE}_{post}","instagram_user_id":IG_USER,
            "degrees_of_freedom_spec":DOF,"contextual_multi_ads":{"enroll_status":"OPT_OUT"}})["id"]; save(); print("Creative",tag,created[f"creative_{tag}"])
    if f"ad_{tag}" not in created:
        created[f"ad_{tag}"]=api("POST",f"{ACC}/ads",{"name":name,"adset_id":adset,"creative":{"creative_id":created[f"creative_{tag}"]},"status":"PAUSED",
            "tracking_specs":[{"action.type":["offsite_conversion"],"fb_pixel":[PIXEL]}]})["id"]; save(); print("Ad",tag,created[f"ad_{tag}"])
print("SIAP",json.dumps(created))
