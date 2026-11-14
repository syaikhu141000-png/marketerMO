# Dashboard MO2 — Minda Optima 2 · Pantas Baca Daily Monitoring

Dokumen ini untuk team IT atau AI yang nak faham, sambung atau pindahkan dashboard ni
(contohnya masuk ke staff portal syarikat). Semua yang perlu diketahui ada di sini.

## 1. Apa benda ni

Dashboard pemantauan iklan Meta (Facebook/Instagram) untuk akaun iklan **Minda Optima 2**,
produk **Pantas Baca** (kelas membaca kanak-kanak). Ia tarik data sendiri dari Meta Marketing API
setiap pagi, kira CPL, traffic light, red flag, cadangan tindakan, dan papar dalam 10 seksyen.
Pengguna boleh tulis **notes/remark** pada setiap campaign, ad set, ad, red flag dan checklist.
Notes dikongsi untuk semua yang buka link.

## 2. Alur kerja (funnel yang dipantau)

```
Meta Ads -> Landing page / WhatsForm -> Lead (WhatsFormSubmit / Website lead) -> WhatsApp -> Follow-up -> Booking -> Enrollment
```

Dashboard ni hanya nampak bahagian **Meta Ads -> Lead**. Booking dan enrollment **tiada** dalam Meta;
kalau nak, sambung dari sistem sales (Google Sheet / CRM) pada fasa seterusnya.

## 3. Seni bina

```
                 GitHub Actions cron 5:07 pagi MYT (21:07 UTC)
Meta Marketing API  ───────────────►  worker/run_build.mjs  ──►  Cloudflare KV (melalui Cloudflare API)
 (graph.facebook.com)                  (guna src/build.js)        "data"       = data dashboard terkini
                                                               "history:YYYY-MM-DD" = snapshot harian (~13 bulan)
                                                               "notes"      = semua notes
                                                               "last_run"   = status run terakhir
Pelayar / staff portal  ◄── GET / , /api/data , /api/notes ── Cloudflare Worker (src/index.js)
```

- **Hosting dashboard:** satu Cloudflare Worker (`mo2-dashboard`, pelan percuma). Worker cuma papar dashboard, simpan notes dan sajikan API.
- **Enjin data:** GitHub Actions (`.github/workflows/refresh-dashboard.yml`, percuma untuk repo public) jalankan `worker/run_build.mjs`
  setiap hari `7 21 * * *` (UTC) = 5:07 pagi waktu Malaysia (GitHub kadang lewat 5-30 minit). Tarik data **semalam**.
  Kerja berat dibuat di GitHub supaya Worker tak kena had CPU 10ms pelan percuma Cloudflare.
- **Tarik sekarang:** GitHub → Actions → "Tarik data MO2 (harian)" → Run workflow.
- **Storan:** Cloudflare KV (binding `KV`).
- **Kod sumber:** repo `marketerMO`, folder `worker/`. Logik yang sama dalam Python: `scripts/build_dashboard_data.py`.

## 4. Endpoint

| Method | Path | Fungsi |
|---|---|---|
| GET | `/` | Dashboard (HTML) |
| GET | `/data.json` atau `/api/data` | Data penuh dashboard (JSON, CORS dibuka) |
| GET | `/api/status` | Status run terakhir: `ok`, `finished_at`, `data_until`, `error` |
| GET | `/api/notes` | Semua notes: `{ "<key>": [ {"ts":"YYYY-MM-DD HH:MM","text":"..."} ] }` (terbaru dahulu) |
| POST | `/api/notes` | Tambah note. Body: `{"key":"campaign:NAMA CAMPAIGN","text":"..."}` |
| POST | `/api/refresh` | Tarik data sekarang. Header `X-Refresh-Key: <REFRESH_KEY>` wajib |
| GET | `/docs` | Dokumen ni |

Format `key` notes: `campaign:<nama>`, `adset:<nama>`, `ad:<nama>`, `redflag:<entity>`, `checklist:chk_<n>:<entity>`.

## 5. Kontrak data (`/api/data`)

```
{
  "_meta": { "dashboard", "generated_at", "accounts_order": ["mo2"] },
  "accounts": {
    "mo2": {
      "_meta": { account_id, account_name, currency, tracking, generated_at, data_source,
                 date_windows: { yesterday, 3D, 7D, 14D, 30D, this_month, last_month }, IMPORTANT_NOTES: [] },
      "section_1_budget_card":            bajet harian aktif, spend semalam, run-rate, guardrail, pace_status
      "section_2_red_flags":              flags[] {priority P1-P4, level, entity, traffic_light, issue, evidence{}, suggested_action},
                                          resolved_since_last_run[], status_changes_since_last_run[]
      "section_3_account_overview":       metrics{window: spend, leads, whatsform_leads, website_leads, cpl, impressions,
                                          reach, frequency, link_click, ctr_pct, cpm}, total_this_year{}, traffic_light_account_cpl,
                                          trend_7D_vs_14D{cpl, ctr, cpc, cpm, cpl_vs_30D}
      "section_4_performance_trend":      series{window: spend, leads, cpl}, cpl_slope_7D_vs_14D, leads_per_day_*, observation
      "section_5_campaign_summary":       campaigns[] {campaign, status, class NEW/OLD, age_days, spend{}, leads{}, cpl{},
                                          traffic_light, trend, conv_type, frequency_14D, action, action_code}
      "section_6_adset_summary":          adsets[] (sama seperti campaign + daily_budget)
      "section_7_ads_performance":        ads_14D[] (spend >= RM20), ads_7D_top[] (top 40) {ad, adset, campaign, status,
                                          spend, whatsform_leads, cpl, frequency, class, traffic_light, basis, flag?}
      "section_8_diagnostic_recommendation": items[] {n, priority, entity, diagnosis, evidence, action, expected_impact}
      "section_9_action_checklist":       codes{M,S,R,H,O,C}, checklist[] {action, entity, reason, code, status}
      "section_10_historical_comparison": bulan lepas vs MTD vs unjuran akhir bulan
    }
  }
}
```

Window: `yesterday` = semalam, `3D/7D/14D/30D` = N hari berakhir semalam, `this_month` = 1hb hingga semalam,
`last_month` = bulan lepas penuh. Semua ikut zon `Asia/Kuala_Lumpur`. Mata wang MYR.

## 6. Peraturan bisnes

- **Lead** = `WhatsFormSubmit` (pixel custom event `offsite_conversion.fb_pixel_custom`) + **Website leads**
  (`lead` / `offsite_conversion.fb_pixel_lead`, ambil nilai maksimum supaya tak kira dua kali).
  **Chat WhatsApp (messaging conversation) TIDAK dikira** sebagai lead.
- **CPL** = spend ÷ lead. Kempen yang nama mengandungi `AWARENESS`/`BRAND` dikecualikan dari CPL dan lead.
- **Kelas:** `NEW` = umur < 14 hari (dari created_time), `OLD` = 14 hari ke atas.
- **Traffic light OLD:** CPL 7D (fallback 14D): 🟢 ≤ RM15 · 🟡 < RM30 · 🔴 ≥ RM30. Tiada lead dan spend ≥ RM30 = 🔴.
- **Traffic light NEW:** CPL kalau ada lead, kalau 0 lead ikut spend: 🟢 ≤ RM30 · 🟡 ≤ RM55 · 🔴 > RM55.
- **Red flag:** P1 = RED & ACTIVE (atau tiada campaign lead-gen ACTIVE), P2 = RED & PAUSED / ad set RED, P3 = YELLOW & ACTIVE, P4 = YELLOW & PAUSED.
- **Tindakan automatik:** diagnosis, cadangan dan checklist dijana sendiri setiap pagi.
  **Sistem TIDAK mengubah apa-apa di Meta** (tiada auto-pause / ubah bajet). Semua tindakan perlu approval manusia.

## 7. Konfigurasi & rahsia

| Nama | Jenis | Nilai |
|---|---|---|
| `META_ACCESS_TOKEN` | GitHub Secret | Token System User Meta (permission `ads_read`, `business_management`) |
| `CLOUDFLARE_API_TOKEN` | GitHub Secret | Token Cloudflare (Workers KV Storage: Edit) untuk tulis data ke KV |
| `REFRESH_KEY` | Cloudflare Secret | Kunci rawak untuk `/api/refresh` |
| `META_AD_ACCOUNT_ID` | Var | `act_863467445706037` |
| `META_API_VERSION` | Var | `v23.0` (kemas kini bila Meta keluarkan versi baru) |
| `KV` | KV binding | namespace `mo2-dashboard` |

Token **tidak pernah** disimpan dalam kod atau repo. Token Meta & Cloudflare untuk enjin harian disimpan dalam
GitHub → Settings → Secrets and variables → Actions. `CF_ACCOUNT_ID` dan `CF_KV_NAMESPACE_ID` ada dalam fail workflow.

## 8. Sambung ke staff portal

Pilihan paling mudah:
1. **Embed:** `<iframe src="https://mo2-dashboard.<subdomain>.workers.dev/" style="width:100%;height:100vh;border:0"></iframe>`
2. **Guna data sendiri:** `fetch("https://mo2-dashboard.<subdomain>.workers.dev/api/data")` (CORS dibuka), lukis UI portal sendiri.
3. **Pindah ke akaun Cloudflare syarikat:** deploy folder `worker/` (lihat `worker/wrangler.toml` / `worker/deploy.py`), kemas kini ID akaun & KV dalam workflow, isi semula secrets.

## 9. Tambah akaun lain (MO4, MO05)

Token Meta mesti ada akses ke akaun tu. Kemudian jalankan `buildData` untuk setiap akaun dan simpan di
`accounts.mo4`, `accounts.mo05` (frontend sudah menyokong banyak akaun: tambah dalam senarai `ACCOUNTS` dalam `dashboard.html`).

## 10. Had & nota

- Data "hari ini" tidak dipaparkan; Meta kemas kini atribusi sehingga 28 hari, jadi angka semalam boleh berubah sedikit.
- Sesiapa yang ada link boleh baca dan tulis notes (tiada login, ikut keputusan owner).
- Remark lama dari Dashboard-MO-v3 (Firebase) tidak dipindahkan.
