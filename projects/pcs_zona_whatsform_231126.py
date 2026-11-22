"""Bina PCS ZON A baru (WhatsForm) dalam campaign sedia ada 161126 / PCS 26 / LEADS / ABO.
1 ad set (RM60, mula 23 Nov 05:00 MYT) + 4 ad (video baru, bukan existing post).
Semua PAUSED. Rekod ID dalam created.json untuk semakan."""
import json, ssl, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from meta_api import cfg

V = "v23.0"
ACC = "act_863467445706037"
PAGE = "106138047883616"
IG_USER = "17841440990166553"
PIXEL = "907174708060871"
CAMPAIGN = "120249139034590618"  # 161126 / PCS 26 / LEADS / ABO
LINK = "https://whatsform.com/wpcs1"
START = "2026-11-23T05:00:00+0800"
OUT = Path(__file__).with_name("pcs_zona_whatsform_231126_created.json")
created = json.loads(OUT.read_text()) if OUT.exists() else {}

TOKEN = cfg()["META_ACCESS_TOKEN"]
CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")


def api(method, path, params=None):
    url = f"https://graph.facebook.com/{V}/{path}"
    p = dict(params or {})
    if TOKEN and TOKEN != "proxy-injected":
        p["access_token"] = TOKEN
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(p)
    else:
        data = urllib.parse.urlencode({k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in p.items()}).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        err = json.load(e).get("error", {})
        raise SystemExit(f"GAGAL {method} {path}: {err.get('message')} | {err.get('error_user_title','')} {err.get('error_user_msg','')}")


def save():
    OUT.write_text(json.dumps(created, indent=1))


EXCLUDE = ["120249061680340618", "120249061506600618", "120248184920120618", "120212962689280618", "120212962805360618",
           "120212960698310618", "120247964873540618", "120241529882410618", "120246754652980618", "120212649816320618",
           "120212649845690618"]

REST = """Cuti sekolah sebulan… jangan biarkan anak terus bergelut membaca.

Anak dah 6 tahun ke atas, tapi masih mengeja satu-satu, cepat bosan atau selalu mengelak apabila diajak membaca?

Gunakan cuti sekolah bulan Disember ini untuk bantu anak belajar membaca dengan lebih teratur melalui

Program Cuti Sekolah Pantas Baca 2026.
✅ Berlangsung sepanjang Disember 2026
✅ Kelas setiap hari kecuali Jumaat
✅ Kaedah pembelajaran 1-to-1 secara bergilir
✅ Teknik Pantas Baca sejak 1995
✅ Fokus “Lancarkan Membaca TANPA Mengeja”

Program ini tersedia di 6 centre terpilih:
📍 Melawati
📍 KLTS
📍 Ampang
📍 Setiawangsa
📍 Wangsa Maju
📍 Sri Gombak

Jangan biarkan cuti sekolah berlalu begitu sahaja. Gunakan peluang ini untuk bantu anak bina asas membaca yang lebih baik sebelum sesi persekolahan bermula.

Klik button sekarang sebelum slot penuh."""

# (nama video, video_id, image_hash, hook)
ADS = [
    ("PCS 1 (2026)", "984226214010573", "a9d1255995261f7379c6826fd5ccfdd4",
     "💥 [PROGRAM CUTI SEKOLAH KINI DIBUKA❗] Bantu Anak Lancarkan Membaca Tanpa Mengeja! 📚"),
    ("PCS 3 (2026)", "1915983702709716", "75ab53dcf98bb0cf9934c10fe810ea5f",
     "💥 [CUTI SEKOLAH 4 MINGGU, ANAK BUAT APA❓] Isi Dengan Program Membaca Intensif! 📚"),
    ("PCS 4 (2026)", "1403815955073043", "5f7293391771790c0ad974c194f71785",
     "⏰ [NAK ANAK LEBIH LANCAR MEMBACA❓] Semak Slot Program Cuti Sekolah Sekarang! 📚"),
    ("PCS 5 (2026)", "1793362625232603", "0259ed01529dac8ed9b0a69e0f3d4a32",
     "💥 [JANGAN BIARKAN ANAK LUPA MEMBACA❗] Kekalkan Momentum Belajar Sepanjang Cuti Sekolah! 📚"),
]

DOF = {"creative_features_spec": {k: {"enroll_status": "OPT_OUT"} for k in [
    "advantage_plus_creative", "carousel_to_video", "creative_stickers", "pac_relaxation",
    "product_extensions", "reveal_details_over_time", "show_destination_blurbs", "show_summary", "site_extensions",
    "video_auto_crop", "video_filtering", "video_uncrop"]}}
DOF["creative_features_spec"]["enhance_cta"] = {"enroll_status": "OPT_IN"}
DOF["creative_features_spec"]["inline_comment"] = {"enroll_status": "OPT_IN"}
DOF["creative_features_spec"]["text_optimizations"] = {"enroll_status": "OPT_IN"}

# --- targeting: salin dari ad set Zon A sedia ada (6 centre + 11 exclude) ---
src = api("GET", "120249139041790618", {"fields": "targeting"})["targeting"]
targeting = dict(src)
targeting["excluded_custom_audiences"] = [{"id": i} for i in EXCLUDE]
targeting.pop("user_age_unknown", None)

# --- 1. ad set ---
if "adset" not in created:
    r = api("POST", f"{ACC}/adsets", {
        "name": "231126 / PCS ZON A / 6 CENTRE / WOMEN / 30-50 / RM60 / WHATSFORM",
        "campaign_id": CAMPAIGN, "daily_budget": "6000", "billing_event": "IMPRESSIONS",
        "optimization_goal": "OFFSITE_CONVERSIONS", "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "promoted_object": {"pixel_id": PIXEL, "custom_event_type": "OTHER", "custom_event_str": "WhatsFormSubmit"},
        "attribution_spec": [{"event_type": "CLICK_THROUGH", "window_days": 7}, {"event_type": "VIEW_THROUGH", "window_days": 1},
                             {"event_type": "ENGAGED_VIDEO_VIEW", "window_days": 1}],
        "targeting": targeting, "start_time": START, "status": "PAUSED",
        "regional_regulated_categories": ["MALAYSIA_UNIVERSAL", "VOLUNTARY_VERIFICATION"],
        "regional_regulation_identities": {"universal_beneficiary": "1737602371705472", "universal_payer": "1737602371705472"}})
    created["adset"] = r["id"]; save(); print("Ad set:", r["id"])

for name, vid, img_hash, hook in ADS:
    k = name.replace(" ", "_").replace("(", "").replace(")", "")
    body = f"{hook}\n\n{REST}"
    if f"creative_{k}" not in created:
        r = api("POST", f"{ACC}/adcreatives", {
            "name": f"231126 / WPCS1 / PCS ZON A - {name}",
            "object_story_spec": json.dumps({
                "page_id": PAGE, "instagram_user_id": IG_USER,
                "video_data": {
                    "video_id": vid, "image_hash": img_hash, "message": body,
                    "call_to_action": {"type": "CONTACT_US", "value": {"link": LINK}},
                },
            }),
            "degrees_of_freedom_spec": DOF, "contextual_multi_ads": {"enroll_status": "OPT_OUT"}})
        created[f"creative_{k}"] = r["id"]; save(); print("Creative", name, r["id"])
    if f"ad_{k}" not in created:
        r = api("POST", f"{ACC}/ads", {
            "name": f"231126 / WPCS1 / PCS ZON A - {name}", "adset_id": created["adset"],
            "creative": {"creative_id": created[f"creative_{k}"]}, "status": "PAUSED",
            "tracking_specs": [{"action.type": ["offsite_conversion"], "fb_pixel": [PIXEL]}]})
        created[f"ad_{k}"] = r["id"]; save(); print("Ad", name, r["id"])

print("SIAP", json.dumps(created))
