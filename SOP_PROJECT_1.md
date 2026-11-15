# SOP Project 1 — Iklan Fizikal WhatsForm (Minda Optima 2)

Project 1 terdiri daripada **3 projek**, ikut peringkat Ads Manager:

| Projek | Peringkat | Isi |
|---|---|---|
| **1. Projek Kempen** | Campaign | Nama campaign, objective **Engagement**, **ABO** |
| **2. Projek Fizikal General WhatsForm** | Ad set | Lokasi 16 cawangan, exclude, umur/jantina, bajet, placement |
| **3. Projek Existing** | Ad (creative) | Iklan guna existing post |

> Status: **DRAF, sedang diajar oleh owner.** Claude TIDAK cipta / ubah / aktifkan apa-apa di Meta sehingga owner beri arahan jelas.
> Akaun iklan: Minda Optima 2 (`act_863467445706037`). Pixel: `907174708060871`.

## Cara guna (aliran kerja)
- **Project 1 = templat.** Semua setting campaign & ad set di bawah ialah "acuan".
- Bila owner minta buat **iklan existing / existing post**: **duplicate ad set** dalam campaign Project 1 sahaja.
  **Jangan cipta campaign baru**, jangan duplicate campaign.
- Semua yang dicipta mesti status **PAUSED** dulu (peraturan CLAUDE.md), owner semak di Ads Manager sebelum aktif.

## 1. Projek Kempen (Campaign)
| Setting | Nilai |
|---|---|
| Nama | `161126 / FIZIKAL / WHATSFORM / ABO` (format: `DDMMYY / JENIS KELAS / SUMBER LEAD / JENIS BAJET`) |
| Buying type | Auction |
| Objective | **Engagement** (disahkan owner) |
| Special Ad Categories | Tiada |
| Setup | Manual (bukan Advantage+ campaign) |
| Advantage campaign budget (CBO) | **Off — ABO** (bajet di ad set) |
| Spending limit / A/B test / budget scheduling | Tiada / Off / Off |

## 2. Projek Fizikal General WhatsForm (Ad set)
| Setting | Nilai |
|---|---|
| Nama | `DDMMYY / KEYWORD / WHATSFORM / ABO / 30-50 / BROAD / WOMEN / RM30 - NAMA VIDEO - POST ID` — **disahkan owner**. KEYWORD = keyword WhatsForm (FWR/WFM/FMO + nombor). Untuk existing post, kod creative = **nama video + ID post di belakang** |
| Conversion location | Website |
| Performance goal | Maximise conversions — pixel `907174708060871`, event custom **`WhatsFormSubmit`** |
| Bid strategy | Highest volume (lowest cost, tiada cap) |
| **Bajet** | **RM30 sehari** |
| Attribution | 7 hari klik · 1 hari view · 1 hari engaged view |
| Umur | 30–50 (Advantage+ audience **on**) |
| Jantina | Perempuan |
| **Bahasa** | Sama seperti TESTING 2 (3 bahasa, kod Meta 6, 24, 41) — **disahkan owner** |
| **Placement** | **Advantage+ placements** |
| **Device** | **Mobile + Desktop (semua device)** |
| Brand safety | Relaxed *(ikut TESTING 2)* |
| Include audience | **Tiada — Broad** |
| **Checkbox / pilihan lain** | **Samakan dengan ad set sedia ada. Jangan tick yang lain**, kecuali owner suruh (cth Advantage). Kalau tak pasti sama ada perlu tick, **tanya owner dulu** semasa buat iklan. |

### Lokasi — 16 cawangan (jenis: orang yang tinggal / kerap / baru berada di kawasan)
| # | Cawangan | Lokasi dalam Meta | Radius |
|---|---|---|---|
| 1 | Taman Melawati | Place: Melawati Mall (3.210415, 101.748562) | 3 batu |
| 2 | Maxim Sentul | Place: Maxim Citylights Sentul KL (3.207133, 101.690383) | 3 batu |
| 3 | KLTS | Place: KL Traders Square (3.203910, 101.703437) | 3 batu |
| 4 | Bandar Seri Putra | Place: Bandar Seri Putra/Bukit Mahkota (2.884714, 101.789212) | 4 batu |
| 5 | Putrajaya | Pin 2.946842, 101.723567 (Jln Perak P15, Presint Diplomatik) | 3 batu |
| 6 | Bangi | Pin 2.959873, 101.753660 (Jln Medan PB 1) | 4 batu |
| 7 | Seri Kembangan | Pin 2.992149, 101.675274 (Jln PP 25, Tmn Pinggiran Putra) | 3 batu |
| 8 | Kajang | Pin 3.008038, 101.806627 (Jenaris / Prima Saujana) | 4 batu |
| 9 | Ampang | Pin 3.151914, 101.759052 (Taman Dagang) | 3 batu |
| 10 | Setiawangsa | Pin 3.177433, 101.738450 (Jln AU 1A/4B) | 3 batu |
| 11 | Sri Damansara | Pin 3.187243, 101.605806 (Bandar Sri Damansara) | 4 batu |
| 12 | Wangsa Maju | Pin 3.198296, 101.745006 (Jln Wangsa Delima) | 3 batu |
| 13 | Setapak | Pin 3.201585, 101.720146 (Jln 2/23A, Taman Danau Kota) | 3 batu |
| 14 | Selayang | Pin 3.233431, 101.641003 (Jln Paragon Utama 1) | 3 batu |
| 15 | Sri Gombak (+ HQ Taman Samudra dalam radius) | Pin 3.242194, 101.704546 (Taman Sri Gombak) | 3 batu |
| 16 | **Shah Alam (BARU)** | Pin 3.068474, 101.488412 (Seksyen 7) | 4 batu |

### Exclude audience
**Wajib:**
1. `customers_jan_oct_meta_format.csv` — 120249061680340618 (pelanggan)
2. `CUSTOMER JAN26` — 120249061506600618 (pelanggan)
3. `MO Whatsform Submit 180D` — 120248184920120618
4. `FBMO - [BOFU] SEND MESSAGE 365D` — 120212962689280618
5. `IGMO - [BOFU] SEND MESSAGE 365D` — 120212962805360618
6. `FBMO - [BOFU] Click / CTA Button 365D` — 120212960698310618

**Juga exclude (keputusan owner 15 Nov):**
7. `VERSION 3 26 3 VV3S 260826` — 120247964873540618
8. `NEW26- VV10S-200526-FBMO` — 120241529882410618
9. `VERSION 2 26- VV10S-050726-FBMO` — 120246754652980618
10. `VV10S-070825-241024-FBMO 200225` — 120212649816320618
11. `241024-FBMO-365D-ENGAGED-POSTADS` — 120212649845690618

**Jangan guna:** MO whasform view 180D & ONPAY VISITORS (pixel audience ~20, rosak), 3 Lookalike (tak sedia),
RETARGETING [cawangan] (untuk campaign retargeting), FB/IG Page 30/60/90D (bertindih), audience < 1,000.

## 3. Projek Existing (Ad — khas existing post)
**Syarat wajib selepas duplicate ad set:**
- **Padam semua ad lama** yang ikut terbawa dalam ad set yang di-duplicate.
- Pastikan **tiada video lama** dan **tiada video yang tak berkaitan** dengan kursus tu dalam ad set.
- Ad set akhir hanya mengandungi ad existing post yang baru.

| Setting | Nilai |
|---|---|
| Nama ad | `DDMMYY / KEYWORD / NAMA VIDEO - POST ID` *(ikut ad sedia ada, cth `121126 / FMO 8 ep / 06 KFTY H14-B2-C3 - 2007278590337477`)* |
| Jenis | **Use existing post** (post ID FB, IG ikut sekali jika ada) |
| Page | `106138047883616` |
| CTA | **Contact Us** (disahkan owner) |
| Tracking | Pixel `907174708060871` on |
| Advantage+ creative | **Semua OFF**, kecuali **Standard enhancements = ON** dan **Text optimizations = ON** |
| Multi-advertiser ads | **OFF** |
| Status | **PAUSED** — owner semak & aktifkan |

## 4. WAJIB tanya owner sebelum buat (jangan andaikan)
Claude mesti **minta semua ni setiap kali** sebelum mula, supaya owner tak terlepas:
1. **Tarikh** untuk nama (`DDMMYY`) = **hari iklan jalan**. Cth buat & jalan 16 hb -> `16xx26`. Owner akan beritahu; kalau tak disebut, **tanya**.
2. **Keyword WhatsForm** — owner bagi. Untuk existing post, **ikut sebiji** keyword yang owner bagi (jangan reka / jangan ambil nombor sendiri).
3. **Post ID / link post** (FB, dan IG kalau ada).
4. **Nama video**.
5. Ada apa-apa **Advantage / tick tambahan** kali ni? (default: tiada)

## 5. Aliran penuh: buat iklan existing post
1. Campaign Project 1 (`161126 / FIZIKAL / WHATSFORM / ABO`) — cipta sekali sahaja.
2. **Duplicate ad set templat** dalam campaign yang sama (bukan campaign baru).
3. Tukar nama ad set: `DDMMYY / KEYWORD / WHATSFORM / ABO / 30-50 / BROAD / WOMEN / RM30 - NAMA VIDEO - POST ID`.
4. Semak setting ad set sama dengan templat (16 lokasi, 11 exclude, RM30, perempuan 30–50 Broad, Advantage+ placements, semua device, WhatsFormSubmit). Tiada tick tambahan.
5. **Padam ad lama** dalam ad set tu; pastikan tiada video lama / tak berkaitan.
6. Cipta ad existing post baru (setting seksyen 3).
7. Semua **PAUSED**. Tunjuk ringkasan kepada owner. Owner semak di Ads Manager, kemudian aktifkan.

## Nota teknikal API (dari pembinaan pertama 16 Nov 2026)
- Ad set wajib ada pengesahan pengiklan Malaysia: `regional_regulated_categories` = MALAYSIA_UNIVERSAL + VOLUNTARY_VERIFICATION,
  `regional_regulation_identities` beneficiary & payer = `1737602371705472`.
- Campaign ABO perlu `is_adset_budget_sharing_enabled=false`.
- "Standard enhancements" (bundle) dah deprecated di API -> aktifkan komponen individu: **enhance_cta, inline_comment (relevant comments), text_optimizations**; lain OPT_OUT.
- Existing post: guna `object_story_id` + `instagram_user_id` sahaja (tak boleh campur dgn `source_instagram_media_id`). Iklan IG jadi versi baru dari post FB (like/komen post IG asal tak ikut).
- Status: campaign PAUSED (owner aktifkan), ad set & ad ACTIVE dengan `start_time` jadual -> bila owner aktifkan campaign, ia mula ikut jadual.
- Skrip rujukan: `projects/project1_161126.py`.

## Nota keyword
- Ad `120239436500140618` (kfty feb h19-4-b4, ad set `🟢090326 / TESTING 2 / ...`) guna keyword **DIRECT FORM** (disahkan owner).
- **Jangan edit ad set / ad lama** (cth nama RM30 tapi bajet RM200) — biarkan seperti asal.

## Perkara terbuka
- Alamat sebenar cawangan Shah Alam (tiada di pantasbaca.com).
- Audience pixel WhatsForm cuma ~20 orang — semak Events Manager.
