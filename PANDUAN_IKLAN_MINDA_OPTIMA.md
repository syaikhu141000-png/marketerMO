# Panduan Iklan Meta — Minda Optima (Pantas Baca)

> Dokumen rujukan penuh: semua projek, setting, ID, dan cara pembuatan iklan yang diajar owner.
> Dikemas kini: **16 Nov 2026**. Sumber: arahan owner dalam sesi Claude + data terus dari Meta Marketing API.
> Fail berkaitan dalam repo: `CLAUDE.md` (peraturan), `SOP_PROJECT_1.md` (SOP ringkas), `projects/` (skrip pembinaan).

---

## Isi kandungan
1. [Akaun & aset penting](#1-akaun--aset-penting)
2. [Peraturan kerja (wajib ikut)](#2-peraturan-kerja-wajib-ikut)
3. [Had bajet harian RM300](#3-had-bajet-harian-rm300)
4. [Konvensyen penamaan](#4-konvensyen-penamaan)
5. [Definisi lead & traffic light](#5-definisi-lead--traffic-light)
6. [Project 1 — Fizikal WhatsForm](#6-project-1--fizikal-whatsform)
7. [Projek PCS 2026 (Program Cuti Sekolah)](#7-projek-pcs-2026-program-cuti-sekolah)
8. [Awareness](#8-awareness)
9. [Cara pembuatan iklan existing post (langkah demi langkah)](#9-cara-pembuatan-iklan-existing-post-langkah-demi-langkah)
10. [Perpustakaan lokasi](#10-perpustakaan-lokasi)
11. [Perpustakaan audience](#11-perpustakaan-audience)
12. [Keyword WhatsForm & kod creative](#12-keyword-whatsform--kod-creative)
13. [Edit copy untuk existing post](#13-edit-copy-untuk-existing-post)
14. [Nota teknikal & perangkap](#14-nota-teknikal--perangkap)
15. [Dashboard & automasi](#15-dashboard--automasi)
16. [Perkara terbuka](#16-perkara-terbuka)

---

## 1. Akaun & aset penting

### Akaun iklan
| Akaun | ID | Business | Nota |
|---|---|---|---|
| **Minda Optima 2 (MO2)** | `863467445706037` | MindaOptima | **Akaun utama.** Project 1, PCS baru, Awareness. Token API boleh baca & tulis |
| Minda Optima 05 (MO05) | `28873619612279525` | MindaOptima | PCS lama (`031126 / PCS 26 / LOKASI / ABO`) — akan ditutup owner |
| Minda Optima 4 | `4603088879971972` | Minda Optima 02 | Tiada iklan aktif |
| Minda Optima 3 | `365687629464834` | PTMO SDN BHD | Tiada spend |
| Minda Optima (Read-Only) | `792765253548663` | MindaOptima | USD |

### Aset
| Aset | ID / nilai |
|---|---|
| Facebook Page | `106138047883616` |
| Instagram account (instagram_user_id) | `17841440990166553` |
| Pixel / Dataset | **Minda Optima 2 - Pixel** `907174708060871` |
| Event WhatsForm | custom event **`WhatsFormSubmit`** (dalam API: `offsite_conversion.fb_pixel_custom`) |
| Event Website lead | standard event **Lead** (`offsite_conversion.fb_pixel_lead`) |
| Pengesahan pengiklan Malaysia | beneficiary & payer `1737602371705472` (wajib untuk setiap ad set) |

### Token & akses
- Token System User Meta: permission `ads_management`, `ads_read`, `business_management`, `pages_manage_ads`, `pages_read_engagement`, `pages_show_list`.
- Token hanya nampak **MO2**. MO05 dibaca/diubah melalui connector Meta Ads.
- Tahap akses app: **Development access** (had panggilan rendah — lihat §14).

---

## 2. Peraturan kerja (wajib ikut)
1. **Semua campaign baru dicipta PAUSED.** Ad set & ad boleh ACTIVE dengan jadual mula; owner ON-kan campaign sendiri.
2. **Jangan ubah bajet, pause atau padam apa-apa tanpa approval owner.**
3. **Sebelum ubah apa-apa: tunjuk ringkasan perubahan, tunggu owner kata "buat" / "ya".**
   Arahan umum (cth "adjust ikut budget") = **minta cadangan**, bukan kebenaran ubah.
4. **Jangan edit ad set / ad lama** (cth nama tulis RM30 tapi bajet RM200) — biarkan.
5. **Jangan tick pilihan tambahan** yang owner tak biasa tick. Kalau tak pasti, **tanya**.
6. Report dalam Bahasa Melayu, mata wang RM.
7. Jangan nilai iklan ikut CPL sahaja — bandingkan dengan booking/enrollment bila data ada.
8. Token tak pernah ditampal dalam chat atau disimpan dalam kod.

---

## 3. Had bajet harian RM300
**Keputusan consultant (15 Nov 2026):** jumlah semua iklan **RM300 sehari**. Setiap cadangan iklan baru mesti nyatakan bajet diambil dari peruntukan mana.

### Pembahagian semasa (16 Nov 2026)
| Peruntukan | Bajet | Ad set (MO2) |
|---|---|---|
| **Partner** | RM90 | (diurus partner) |
| **Iklan owner — Project 1** | RM90 | DIRECT FORM RM30 · FWR 3 RM30 · FWR 9 RM30 |
| **PCS** | RM90 | Poster RM15 · Zon A RM30 · Zon B RM45 |
| **Awareness** | RM30 | Facebook RM17 · Instagram RM13 |
| **Jumlah** | **RM300** | |

- Bajet Awareness dikira ikut nisbah asal **FB 57.1% : IG 42.9%** (40 : 30).
- Sebelum PCS lama di MO05 ditutup, jumlah sebenar melebihi RM300.

---

## 4. Konvensyen penamaan

### Tarikh
`DDMMYY` = **hari iklan mula jalan**, bukan hari dicipta. Cth jalan 16 Nov 2026 → `161126`. **Sentiasa tanya owner tarikh.**

### Campaign
| Projek | Format | Contoh |
|---|---|---|
| Project 1 | `DDMMYY / JENIS KELAS / SUMBER LEAD / JENIS BAJET` | `161126 / FIZIKAL / WHATSFORM / ABO` |
| PCS | `DDMMYY / PCS 26 / OBJEKTIF / JENIS BAJET` | `161126 / PCS 26 / LEADS / ABO` |

### Ad set
| Projek | Format | Contoh |
|---|---|---|
| Project 1 | `DDMMYY / KEYWORD / WHATSFORM / ABO / 30-50 / BROAD / WOMEN / RM30 - NAMA VIDEO - POST ID` | `161126 / FWR 9 / WHATSFORM / ABO / 30-50 / BROAD / WOMEN / RM30 - KFTY DS 1 SEPT FULL - 1801804417551563` |
| PCS | `DDMMYY / PCS [JENIS] / [LOKASI] / WOMEN / 30-50 / RM[BAJET]` | `161126 / PCS ZON A / 6 CENTRE / WOMEN / 30-50 / RM30` |

- `TOFU` dalam nama lama **ditukar kepada `ABO`** (arahan owner).
- `KEYWORD` = keyword WhatsForm (FWR / WFM / FMO + nombor, atau `DIRECT FORM`).

### Ad
| Projek | Format | Contoh |
|---|---|---|
| Project 1 | `DDMMYY / KEYWORD / NAMA VIDEO - POST ID` | `161126 / FWR 3 / UP-Tim 2 - 1798024114596260` |
| PCS | `DDMMYY / PCS / NAMA CREATIVE - POST ID` | `161126 / PCS / PCS_4_2026_PJBG_final - 2005742443824425` |

---

## 5. Definisi lead & traffic light

### Lead
- **Lead = WhatsFormSubmit + Website lead.**
- **Chat WhatsApp (messaging conversation) TIDAK dikira** sebagai lead (arahan owner).
- Kempen AWARENESS **dikecualikan** dari CPL.
- Meta cuma nampak sampai lead. Booking & enrollment **tiada dalam Meta** — perlu data dari sales.

### Kelas iklan & traffic light (ikut dashboard lama)
| Kelas | Syarat | 🟢 GREEN | 🟡 YELLOW | 🔴 RED |
|---|---|---|---|---|
| **OLD** | umur ≥ 14 hari, CPL 7D (fallback 14D) | ≤ RM15 | < RM30 | ≥ RM30 (atau 0 lead & spend ≥ RM30) |
| **NEW** | umur < 14 hari, CPL (atau spend jika 0 lead) | ≤ RM30 | ≤ RM55 | > RM55 |

---

## 6. Project 1 — Fizikal WhatsForm

Iklan kelas **fizikal** Pantas Baca, lead masuk melalui **WhatsForm**. Project 1 dibahagi kepada **3 projek** ikut peringkat Ads Manager:

| Projek | Peringkat | Isi |
|---|---|---|
| **1. Projek Kempen** | Campaign | Nama, objective Engagement, ABO |
| **2. Projek Fizikal General WhatsForm** | Ad set | 16 lokasi, 11 exclude, perempuan 30–50, RM30, placement |
| **3. Projek Existing** | Ad | Existing post |

**Konsep:** Project 1 = **templat**. Untuk iklan existing post baru → **duplicate ad set dalam campaign sama**, jangan buat campaign baru.

### 6.1 Projek Kempen (Campaign)
| Setting | Nilai |
|---|---|
| Nama | `161126 / FIZIKAL / WHATSFORM / ABO` |
| Buying type | Auction |
| Objective | **Engagement** |
| Special Ad Categories | Tiada |
| Setup | Manual (bukan Advantage+ campaign) |
| Advantage campaign budget (CBO) | **Off — ABO** |
| Spending limit / A/B test / Budget scheduling | Tiada / Off / Off |

### 6.2 Projek Fizikal General WhatsForm (Ad set)
| Setting | Nilai |
|---|---|
| Conversion location | **Website** |
| Performance goal | Maximise number of conversions |
| Dataset / event | Pixel `907174708060871` → **WhatsFormSubmit** |
| Bid strategy | Highest volume (tiada cost cap) |
| **Bajet** | **RM30 sehari** |
| Jadual | Mula 5:00 pagi hari jalan, tiada tarikh tamat |
| Attribution | 7 hari klik · 1 hari view · 1 hari engaged view |
| Lokasi | **16 cawangan** (lihat §10.1), jenis "tinggal / kerap / baru berada" |
| Umur | 30–50 (Advantage+ audience **ON** — umur jadi cadangan) |
| Jantina | Perempuan |
| Bahasa | 3 bahasa (kod Meta 6, 24, 41) — sama seperti ad set sedia ada |
| Include audience | **Tiada (Broad)** |
| Exclude audience | **11 audience** (lihat §11.1) |
| Placement | **Advantage+ placements** |
| Device | **Mobile + Desktop** |
| Brand safety | Relaxed |
| Tick / pilihan lain | **Samakan dengan ad set sedia ada**, jangan tick lain kecuali disuruh |

### 6.3 Projek Existing (Ad)
| Setting | Nilai |
|---|---|
| Jenis | **Use existing post** (FB post; versi IG dibina dari post FB) |
| CTA | **Contact Us** |
| Website URL | Ikut post asal (cth FWR 3 → `https://whatsform.com/ffdpjn`) — **jangan ubah / buang** |
| Tracking | Pixel `907174708060871` |
| Advantage+ creative | **ON:** Enhance CTA, Relevant comments (inline comment), Text optimization. **Lain semua OFF** (auto crop, video filter, uncrop, stickers, dll) |
| Multi-advertiser ads | **OFF** |

**Syarat wajib bila duplicate ad set:** padam **semua ad lama** yang ikut terbawa; pastikan **tiada video lama** atau **video tak berkaitan** dengan kursus. Ad set akhir hanya ada ad existing post baru.

### 6.4 Pembinaan sebenar — 16 Nov 2026 (MO2)
**Campaign:** `161126 / FIZIKAL / WHATSFORM / ABO` — ID `120249134452660618` — status ACTIVE (diaktifkan owner).

| Ad set | ID ad set | Ad | ID ad | Post ID | Bajet |
|---|---|---|---|---|---|
| `161126 / DIRECT FORM / ... RM30 - kfty feb h19-4-b4 - 1774642276934444` | 120249134452960618 | `161126 / DIRECT FORM / kfty feb h19-4-b4 - 1774642276934444` | 120249134454430618 | 1774642276934444 | RM30 |
| `161126 / FWR 3 / ... RM30 - UP-Tim 2 - 1798024114596260` | 120249134454480618 | `161126 / FWR 3 / UP-Tim 2 - 1798024114596260` | 120249134455150618 | 1798024114596260 | RM30 |
| `161126 / FWR 9 / ... RM30 - KFTY DS 1 SEPT FULL - 1801804417551563` | 120249134455220618 | `161126 / FWR 9 / KFTY DS 1 SEPT FULL - 1801804417551563` | 120249134456000618 | 1801804417551563 | RM30 |

Skrip: `projects/project1_161126.py` · ID: `projects/project1_161126_created.json`.

### 6.5 Prestasi rujukan (campaign `090326 / TESTING 2`, 2026 hingga 14 Nov)
**255 ad · RM146,100.66 · 6,408 result · CPL RM22.80**

| Keluarga keyword | Ad | Result | Spend | CPL |
|---|---|---|---|---|
| **FWR** | 143 | 4,527 | RM101,405.60 | **RM22.40** |
| **WFM** | 104 | 440 | RM17,785.26 | RM40.42 |
| **FMO** | 7 | 16 | RM764.81 | RM47.80 |
| **DIRECT FORM** | 1 | 1,425 | RM26,144.99 | RM18.35 |

Top 10 ad (sepanjang 2026):
| # | Keyword | Creative | ID ad | Post ID | Result | CPL |
|---|---|---|---|---|---|---|
| 1 | DIRECT FORM | kfty feb h19-4-b4 | 120239436500140618 | 1774642276934444 | 1,425 | RM18.35 |
| 2 | FWR 13 | FEB KFTY H12V3 | 120241205823470618 | 1802361174162554 | 861 | RM21.62 |
| 3 | FWR 9 | KFTY DS 1 SEPT FULL | 120241153300300618 | 1801804417551563 | 828 | RM16.84 |
| 4 | FWR 8 | KFTY DS 5 SEPT FULL | 120241153265170618 | 1801804310884907 | 491 | RM24.32 |
| 5 | FWR 4 | KFTY DS 3 SEPT FULL | 120241152737660618 | 1801804184218253 | 414 | RM20.91 |
| 6 | FWR 12 | SKB1 V1 | 120241205415520618 | 1802361020829236 | 283 | RM21.11 |
| 7 | FWR 1 | UP-tim 11 | 120240868793490618 | 1798021101263228 | 180 | RM15.54 |
| 8 | FWR 7 | KFTY VH1 SEPT FULL | 120241152853490618 | 1801804087551596 | 160 | RM21.63 |
| 9 | FWR 6 | MOF7 V1 final | 120241152832640618 | 1801804314218240 | 131 | RM22.73 |
| 10 | WFM 36 | w1 h15 b1b jen | 120247173975370618 | 1898297424568928 | 106 | RM26.16 |

**Insight utama:**
- KFTY = 68.5% semua result (CPL RM20.71 vs bukan-KFTY RM27.36). H19 + B4 dan format DS paling cekap.
- Pemenang lama **fatigue**: CPL 10 Sep–12 Nov naik 30–39% berbanding purata tahun.
- W1 / B1 / JEN / H15 banyak diuji (60+ ad) tapi CPL RM31–35 — elak.
- Repost / duplicate pemenang dengan keyword sama hampir tak menjadi.

---

## 7. Projek PCS 2026 (Program Cuti Sekolah)

### 7.1 Latar belakang (dari PCS 2026 Playbook)
| Perkara | Isi |
|---|---|
| Program | Kelas fizikal Pantas Baca sepanjang **Disember 2026** |
| Lokasi | 8 centre: Putrajaya, Bangi, Melawati, KLTS, Wangsa Maju, Sri Gombak, Ampang, Setiawangsa |
| Jadual kelas | Setiap hari kecuali Jumaat, 9:00–10:30 & 11:00–12:30 |
| Target | 128 enrollment (8 × 2 kelas × 8 murid) |
| Tempoh iklan | 12 Okt – **15 Dis** (cut-off) |
| Harga | RM900–1,000 (TBC, **jangan sebut dalam iklan**) |
| USP | Teknik sejak 1995 · "Lancarkan Membaca TANPA Mengeja" · 1-to-1 secara rotation |

> Dengan had bajet baru (PCS ~RM90–120/hari), target 128 **tak realistik** — perlu dibincang dengan consultant/bos. Perlukan data booking sebenar untuk kira semula.

### 7.2 Prestasi PCS (13 Okt – 14 Nov 2026)
| Campaign | Akaun | Spend | Lead | CPL |
|---|---|---|---|---|
| `131026 / PCS26 / LEAD / ABO` (paused) | MO2 | RM5,129.83 | 250 | RM20.52 |
| `031126 / PCS 26 / LOKASI / ABO` | MO05 | RM2,523.16 | 86 | RM29.34 |
| **Jumlah** | | **RM7,652.99** | **336** | **RM22.78** |

- Poster paling murah (CPL RM5–16). Poster terbaik sepanjang PCS: `poster-pcs-compact-structured-orange-v5` (MO2) — 93 lead, CPL RM5.53 (sahkan kualiti lead).
- Zon B (PJ & BG) jauh lebih baik dari Zon A lama (RM22.58 vs RM57.78).
- Testimoni sebagai conversion lemah (RM43.56).

### 7.3 Setting campaign PCS (MO2)
| Peringkat | Setting | Nilai |
|---|---|---|
| Campaign | Nama | `161126 / PCS 26 / LEADS / ABO` |
| | Objective | **Leads** |
| | Bajet | **ABO** |
| Ad set | Conversion location | **Website** (single website) |
| | Dataset | **Minda Optima 2 - Pixel** |
| | Conversion event | **Lead** |
| | Radius | **4 batu** untuk semua centre |
| | Lain-lain | Sama seperti Project 1 (perempuan 30–50, Advantage+ audience, 11 exclude, Advantage+ placements, semua device, bahasa sama, attribution sama) |
| Ad | | Existing post, CTA Contact Us, Advantage+ creative sama seperti Project 1 |

### 7.4 Pembinaan sebenar — 16 Nov 2026 (MO2)
**Campaign:** `161126 / PCS 26 / LEADS / ABO` — ID `120249139034590618` — mula 16 Nov 2026 05:00.

| Ad set | ID | Lokasi (4 batu) | Bajet |
|---|---|---|---|
| `161126 / PCS POSTER / 8 CENTRE / WOMEN / 30-50 / RM17` | 120249139034880618 | 8 centre | **RM15** (diturunkan dari RM17 pada 15 Nov) |
| `161126 / PCS ZON A / 6 CENTRE / WOMEN / 30-50 / RM30` | 120249139041790618 | Melawati, KLTS, Wangsa Maju, Sri Gombak, Ampang, Setiawangsa | RM30 |
| `161126 / PCS ZON B / PJ&BG / WOMEN / 30-50 / RM45` | 120249139043320618 | Putrajaya, Bangi | RM45 |

**Ad (11):**
| Ad set | Creative | ID ad baru | Post ID | Prestasi asal (MO05, 3–14 Nov) |
|---|---|---|---|---|
| Poster | poster-pcs-compact-structured-orange-v6-6tahun | 120249139036930618 | 2007194510345885 | 6 lead, RM11.13 |
| Poster | poster-pcs-compact-forest-v7 | 120249139037810618 | 2016759306056072 | 5 lead, RM15.52 |
| Poster | poster-pcs-compact-structured-sage-v6-6tahun | 120249139039270618 | 2007194470345889 | 3 lead, RM16.28 |
| Poster | poster-pcs-compact-structured-navy-v6-6tahun | 120249139040280618 | 2007194497012553 | 2 lead, RM12.69 |
| Poster | poster-pcs-compact-structured-orange-navy-v6-6tahun | 120249139041630618 | 2007194477012555 | 1 lead, RM5.50 |
| Zon A | PCS_1_2026_final | 120249139042690618 | 2005555933843076 | 15 lead, RM58.85 ⚠️ |
| Zon A | 2025 pcs 2 lama THUMB | 120249139043020618 | 2017231682675501 | 2 lead, RM42.01 |
| Zon A | PCS1 v4 THUMB | 120249139043270618 | 2017231696008833 | 1 lead, RM10.71 |
| Zon B | PCS_4_2026_PJBG_final | 120249139045330618 | 2005742443824425 | 37 lead, RM23.06 |
| Zon B | PCS1 v4 THUMB | 120249139046050618 | 2017231689342167 | 9 lead, RM16.97 |
| Zon B | PCS_2_2026_PJBG_final | 120249139046490618 | 2005742440491092 | 2 lead, RM20.46 |

Skrip: `projects/pcs_161126.py` · ID: `projects/pcs_161126_created.json`.

**Tindakan owner:** tutup PCS lama di MO05 (`031126 / PCS 26 / LOKASI / ABO`) bila campaign baru dah jalan — elak bazir lead & duit.

---

## 8. Awareness
| Perkara | Nilai |
|---|---|
| Campaign | `191026 / AWARENESS / BROAD / FB & IG` — ID `120248665094570618` (MO2) |
| Tujuan | **Video views sahaja** — tiada link, tiada destinasi |
| Ad set Facebook | `191026 / FACEBOOK / RM40` — ID `120248665094610618` — goal **Post engagement** — **RM17** |
| Ad set Instagram | `191026 / INSTAGRAM / RM30` — ID `120248665094600618` — goal **ThruPlay** — **RM13** |

Prestasi 7 hari (hingga 15 Nov):
| | Instagram | Facebook |
|---|---|---|
| Kos setiap ThruPlay | **RM0.05** | RM0.38 |
| ThruPlay | 3,924 | 728 |
| Purata masa tonton | 7 s | 2 s |

- Ukur Awareness guna **kos ThruPlay / masa tonton**, bukan lead atau CTR.
- Facebook lemah sebab goal **Post engagement**. Untuk video view yang lebih baik, buat ad set FB baru dengan goal **ThruPlay** (goal sedia ada tak boleh ditukar).
- Owner mahu **kedua-dua FB & IG kekal jalan**.
- Nota: Project 1 & PCS **exclude** audience video viewer — audience Awareness tak digunakan untuk retargeting selagi tiada campaign retargeting aktif.

---

## 9. Cara pembuatan iklan existing post (langkah demi langkah)

### 9.1 WAJIB tanya owner dulu (jangan mula tanpa jawapan)
1. 📅 **Tarikh jalan** (untuk nama `DDMMYY`) dan masa mula (biasanya 5:00 pagi).
2. 🔑 **Keyword WhatsForm** — ikut **sebiji** yang owner bagi.
3. 🔗 **Post ID / link post** (FB, dan IG kalau ada).
4. 🎬 **Nama video / creative**.
5. ✅ Ada **Advantage / tick tambahan**? (default: tiada)
6. 💰 **Bajet & dari peruntukan mana** (had RM300).
7. 🏢 **Akaun** (default MO2).

### 9.2 Langkah (Project 1 — existing post)
1. Pastikan campaign Project 1 wujud (`DDMMYY / FIZIKAL / WHATSFORM / ABO`, Engagement, ABO). **Cipta sekali sahaja.**
2. **Duplicate ad set templat** dalam campaign yang sama.
3. Tukar nama ad set ikut format §4.
4. Semak setting ad set = templat §6.2 (16 lokasi, 11 exclude, RM30, perempuan 30–50, Advantage+ placements, semua device, WhatsFormSubmit). **Tiada tick tambahan.**
5. **Padam semua ad lama** dalam ad set tu. Pastikan tiada video lama / tak berkaitan.
6. Cipta ad: **Use existing post** → pilih post ID → CTA **Contact Us** → pastikan **Website URL WhatsForm** kekal.
7. Advantage+ creative: ON hanya **Enhance CTA, Relevant comments, Text optimization**. Semak **"Review defaults"** — pastikan tiada enhancement lain auto ON.
8. Multi-advertiser ads **OFF**.
9. Jadual ad set: mula `DDMMYY 05:00`.
10. Campaign **PAUSED** (kalau campaign baru). Tunjuk ringkasan kepada owner.
11. Owner semak di Ads Manager → ON-kan campaign → iklan mula ikut jadual.

### 9.3 Langkah (campaign baru dengan banyak ad set — contoh PCS)
1. Sahkan dengan owner: objective, conversion location, dataset, event, akaun, nama, struktur ad set, lokasi setiap ad set, radius, bajet setiap ad set, senarai post untuk setiap ad set, tarikh & masa mula, dan nasib campaign lama.
2. Cipta campaign (PAUSED, ABO).
3. Cipta setiap ad set (ACTIVE, jadual mula, setting §7.3).
4. Cipta ad existing post dalam setiap ad set.
5. Baca semula semua dari Meta untuk sahkan (bajet, lokasi, radius, exclude, event, jadual).
6. Owner ON-kan campaign; owner tutup campaign lama.

### 9.4 Semakan selepas buat (checklist)
- [ ] Nama campaign / ad set / ad ikut format
- [ ] Bajet betul & jumlah keseluruhan ≤ RM300
- [ ] Lokasi & radius betul
- [ ] 11 exclude ada
- [ ] Event conversion betul (WhatsFormSubmit untuk Project 1, Lead untuk PCS)
- [ ] Jadual mula betul
- [ ] Ad lama dipadam (kalau duplicate)
- [ ] Advantage+ creative ikut SOP
- [ ] Website URL WhatsForm kekal
- [ ] Campaign PAUSED sebelum owner semak

---

## 10. Perpustakaan lokasi
Jenis lokasi: **orang yang tinggal / kerap / baru berada di kawasan** ("People living in or recently in").

### 10.1 16 cawangan (Project 1)
| # | Cawangan | Lokasi Meta | Koordinat | Radius P1 | Alamat cawangan |
|---|---|---|---|---|---|
| 1 | Taman Melawati | Place: Melawati Mall (key `1916025131952167`) | 3.210415, 101.748562 | 3 batu | Level 1, 251A, Jln Bandar 12, Tmn Melawati, 53100 KL |
| 2 | Maxim Sentul | Place: Maxim Citylights Sentul KL | 3.207133, 101.690383 | 3 batu | S-01-15, Maxim Citylights Sentul, Jln Sentul Perdana, 51100 KL |
| 3 | KLTS | Place: KL Traders Square (key `325660801248263`) | 3.203910, 101.703437 | 3 batu | Plaza KLTS, 13A-1, Jln Gombak, Setapak, 53000 KL |
| 4 | Bandar Seri Putra | Place: Bandar Seri Putra/Bukit Mahkota | 2.884714, 101.789212 | 4 batu | 14-1, Jln Seri Putra 1/5, 43000 Kajang |
| 5 | Putrajaya | Pin | 2.946842, 101.723567 | 3 batu | 20-A, Jln Perak P15, Presint Diplomatik, 62050 Putrajaya |
| 6 | Bangi | Pin | 2.959873, 101.753660 | 4 batu | 8A, Jln Medan PB 1, Seksyen 9, 43650 Bandar Baru Bangi |
| 7 | Seri Kembangan | Pin | 2.992149, 101.675274 | 3 batu | A-8-1, Putra Walk, Jln PP 25, 43300 Seri Kembangan |
| 8 | Kajang | Pin | 3.008038, 101.806627 | 4 batu | 6-A, Jln Prima Saujana 1/1A, 43000 Kajang |
| 9 | Ampang | Pin | 3.151914, 101.759052 | 3 batu | 12A-1, Jln Dagang 1/1A, Tmn Dagang, 68000 Ampang |
| 10 | Setiawangsa | Pin | 3.177433, 101.738450 | 3 batu | 11-1, Jln AU 1A/4B, Tmn Keramat Permai, 54200 KL |
| 11 | Sri Damansara | Pin | 3.187243, 101.605806 | 4 batu | 33-1, Jln Tanjung SD 13/1, Bandar Sri Damansara, 52200 KL |
| 12 | Wangsa Maju | Pin | 3.198296, 101.745006 | 3 batu | 15, Jln Wangsa Delima 5, Seksyen 5, 53300 KL |
| 13 | Setapak | Pin | 3.201585, 101.720146 | 3 batu | 70-1, Jln 2/23A, Off Jln Genting Kelang, 53300 KL |
| 14 | Selayang | Pin | 3.233431, 101.641003 | 3 batu | 1-1, Jln Paragon Utama 1, 68100 Batu Caves |
| 15 | Sri Gombak (+ HQ Taman Samudra dalam radius) | Pin | 3.242194, 101.704546 | 3 batu | 1A, Jln SG 3/4, Tmn Sri Gombak, 68100 Selangor |
| 16 | **Shah Alam** (tambahan owner) | Pin (Seksyen 7) | 3.068474, 101.488412 | 4 batu | Belum disahkan (tiada di pantasbaca.com) |

### 10.2 Set lokasi PCS (radius 4 batu semua)
| Set | Centre |
|---|---|
| **8 centre (Poster)** | Putrajaya, Bangi, Melawati, KLTS, Wangsa Maju, Sri Gombak, Ampang, Setiawangsa |
| **Zon A (6 centre)** | Melawati, KLTS, Wangsa Maju, Sri Gombak, Ampang, Setiawangsa |
| **Zon B (PJ & BG)** | Putrajaya, Bangi |

---

## 11. Perpustakaan audience

### 11.1 Exclude — 11 audience (Project 1 & PCS)
| # | Audience | ID | Sebab |
|---|---|---|---|
| 1 | customers_jan_oct_meta_format.csv | 120249061680340618 | Pelanggan |
| 2 | CUSTOMER JAN26 | 120249061506600618 | Pelanggan |
| 3 | MO Whatsform Submit 180D | 120248184920120618 | Dah isi borang |
| 4 | FBMO - [BOFU] SEND MESSAGE 365D | 120212962689280618 | Dah mesej |
| 5 | IGMO - [BOFU] SEND MESSAGE 365D | 120212962805360618 | Dah mesej (IG) |
| 6 | FBMO - [BOFU] Click / CTA Button 365D | 120212960698310618 | Dah klik CTA |
| 7 | VERSION 3 26 3 VV3S 260826 | 120247964873540618 | Video viewer |
| 8 | NEW26- VV10S-200526-FBMO | 120241529882410618 | Video viewer |
| 9 | VERSION 2 26- VV10S-050726-FBMO | 120246754652980618 | Video viewer |
| 10 | VV10S-070825-241024-FBMO 200225 | 120212649816320618 | Video viewer |
| 11 | 241024-FBMO-365D-ENGAGED-POSTADS | 120212649845690618 | Engager post |

### 11.2 Include
**Tiada — Broad** (lokasi + perempuan 30–50 + Advantage+ audience).

### 11.3 Jangan guna (tak include, tak exclude)
| Audience | Sebab |
|---|---|
| MO whasform view 180D, ONPAY VISITORS | Pixel audience cuma ~20 orang — rosak |
| Lookalike (MY 1%, 1–3%, 3–6%) | Status tak sedia |
| RETARGETING [cawangan] ×9 | Simpan untuk campaign retargeting |
| FB/IG Page post/ads 30D/60D/90D | Bertindih dengan ENGAGED-POSTADS 365D |
| MindaOptima VV - Putrajaya, BSP RETARGETING, SAVED POST | Terlalu kecil (< 1,000) |

### 11.4 Cadangan masa depan
- Lookalike 1% dari senarai pelanggan (1,300–1,600 orang) — uji dalam ad set berasingan.
- Betulkan audience pixel WhatsForm di Events Manager.

---

## 12. Keyword WhatsForm & kod creative

### Keyword WhatsForm
- Keyword ialah kod **FWR / WFM / FMO + nombor** dalam nama ad set / ad, atau **DIRECT FORM**.
- Setiap keyword berkait dengan link WhatsForm tersendiri (cth FWR 3 → `whatsform.com/ffdpjn`).
- **Owner yang bagi keyword.** Claude tak reka atau ambil nombor sendiri.
- `TESTING 2` ialah nama ad set; keyword ad dalam ad set tu ialah **DIRECT FORM**.

### Kod creative (andaian, belum disahkan penuh)
| Kod | Andaian |
|---|---|
| KFTY | Siri creative utama (paling berjaya) |
| DS / VH | Format video |
| FEB / SEPT | Bulan creative dibuat |
| H# / B# / C# | Hook / Body / CTA |
| W1 / W3 | Varian (belum disahkan) |

---

## 13. Edit copy untuk existing post
- Dalam Ads Manager versi baru, **primary text boleh diedit** untuk existing post.
- **Belum disahkan** sama ada like/komen post kekal selepas edit. Cara uji: edit satu ad → Publish → semak angka reaction/comment/share dalam Ad preview. Kekal = selamat; jadi 0 = Meta cipta post baru.
- **Website URL WhatsForm wajib kekal.**
- Alternatif selamat: edit caption post asal di Meta Business Suite (like/komen kekal; terkesan pada semua iklan yang guna post tu).
- Struktur copy: **HOOK → PROBLEM → EMOTION → SOLUTION → USP → PROOF → CTA**. Jangan reka USP atau testimoni.

---

## 14. Nota teknikal & perangkap
| Isu | Penjelasan / cara elak |
|---|---|
| **Had panggilan API** ("User request limit reached", code 17) | Tahap Development access. Biasanya pulih dalam beberapa minit – 1 jam. Iklan tak terjejas. Elak banyak panggilan berturut-turut. Mohon **Standard Access** (percuma) di App Review untuk had lebih tinggi |
| **Auto-pause melalui connector** | Ubah bajet melalui connector Meta Ads boleh **auto-PAUSE** ad set aktif. Untuk MO2 guna token terus; untuk MO05 owner ubah sendiri di Ads Manager |
| **"Advertiser is missing"** | Ad set wajib ada `regional_regulated_categories` = MALAYSIA_UNIVERSAL + VOLUNTARY_VERIFICATION dan beneficiary/payer `1737602371705472`. Ad set lama tanpa info ni tak boleh diubah bajet sehingga ditambah |
| **ABO** | Campaign perlu `is_adset_budget_sharing_enabled=false` |
| **Standard enhancements** | Bundle dah deprecated di API → hidupkan komponen: `enhance_cta`, `inline_comment`, `text_optimizations` |
| **Existing post + Instagram** | Guna `object_story_id` + `instagram_user_id` sahaja; tak boleh campur `source_instagram_media_id`. Versi IG jadi iklan baru dari post FB |
| **Status & jadual** | Campaign PAUSED, ad set & ad ACTIVE dengan `start_time` → owner ON campaign, iklan mula ikut jadual |
| **Sambungan terputus semasa cipta** | Semak dulu sama ada objek dah tercipta sebelum cuba semula — elak duplicate |
| **Token tamat** | Semak di developers.facebook.com/tools/debug/accesstoken (Expires). Jika tamat, jana baru dan simpan semula |

---

## 15. Dashboard & automasi
| Perkara | Nilai |
|---|---|
| Dashboard live (MO2) | https://mo2-dashboard.syaikhu141000.workers.dev/ |
| Kandungan | Tab Gabungan + 10 seksyen (sama seperti Dashboard-MO-v3) + **📅 Pilih Tarikh** (macam Ads Manager) |
| Notes | Dikongsi semua yang buka link (Cloudflare KV) |
| Dokumen untuk IT | `/docs` dalam dashboard |
| API | `/api/data`, `/api/daily`, `/api/notes`, `/api/status` |
| Tarik data | Scheduled task Claude **5:08 pagi MYT** setiap hari (data semalam), notifikasi ke phone |
| Kod | Repo `marketerMO`, folder `worker/` |
| Dashboard lama | Dashboard-MO-v3 (GitHub Pages) — **tidak disentuh** |

---

## 16. Perkara terbuka
- Alamat sebenar cawangan **Shah Alam**.
- Audience pixel WhatsForm cuma ~20 orang — semak Events Manager.
- **Booking/enrollment PCS** semasa — perlu untuk kira jarak ke target.
- Campaign **partner** (RM90) — campaign mana.
- Kesahihan **edit primary text** existing post (like/komen kekal?).
- Maksud penuh kod creative (DS, VH, W1, dll).
- Kualiti lead poster orange-v5 (CPL RM5.53).
- Tutup campaign PCS lama MO05.
- Nama ad set Awareness & Poster PCS masih tulis bajet lama (RM40 / RM30 / RM17).
