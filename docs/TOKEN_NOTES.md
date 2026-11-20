# Nota: Token Meta Ads dalam automation (scheduled task Claude)

**Status: confirmed 2026-11-20.** Assumption lama (`META_ACCESS_TOKEN=proxy-injected` akan
disuntik automatik oleh proxy sesi cloud) **tidak berfungsi** dalam Claude Code / Cowork
scheduled task environment. Nota ni rekod apa yang dah disahkan, supaya tak perlu debug semula
lain kali.

## Apa yang disahkan

1. **Network block (lapisan pertama)** — Claude cloud session punya outbound HTTPS pergi
   melalui agent-proxy (`127.0.0.1:36747`), dan `graph.facebook.com` TIDAK dibenarkan secara
   default. Fix: tambah `graph.facebook.com` di **Claude Settings > Capabilities > Allowed
   websites** (pilih "Standard download sites only" + tambah domain tu dalam senarai custom).

2. **Token tak auto-inject (lapisan kedua, root cause sebenar)** — Lepas network settle,
   request dengan `META_ACCESS_TOKEN=proxy-injected` (tiada `access_token` dihantar) kena ralat:

Ini confirm agent-proxy tu **general-purpose TLS tunnel + domain allowlist sahaja** — ia
bukan API-aware proxy, dan TIDAK suntik `Authorization` header untuk Graph API (atau API
lain). Assumption dalam komen lama `meta_api.py` adalah salah untuk environment ni.

3. **Fix sementara yang jalan**: masukkan token sebenar (System User Access Token) terus dalam
`.env` sebelum run script — token bekerja normal lepas tu (confirmed: report jana dan email
hantar dengan betul).

4. **Platform block simpan token dalam scheduled task prompt** — percubaan letak token sebenar
terus dalam prompt scheduled task (supaya setiap firing automatik ada token) di-**block** oleh
classifier keselamatan Claude ("Sensitive Information Leakage"). Jadi token **tak boleh**
disimpan kekal dalam prompt automation — ia kena disediakan di luar prompt tu.

## Pilihan fix jangka panjang

- **A. Token broker/endpoint sendiri** — host token (atau refresh logic) di server/secret-store
sendiri, dan `meta_api.py` panggil endpoint tu runtime untuk dapat token terkini, bukan baca
terus dari `.env` static. Ini cara paling robust untuk automation betul-betul jalan sendiri.
- **B. Manual refresh** — bila scheduled task gagal (token expired/invalid), owner masukkan
token baru dalam chat Claude untuk satu run manual (± 2 minit), sambil tunggu fix A siap.
System User token biasanya tahan agak lama, jadi kekerapan refresh patut rendah.

## Meta Ads MCP connector — kenapa TAK sesuai ganti script ni

Connector `mcp__Meta_Ads__*` yang ada dalam sesetengah Claude session sudah authenticated
(tiada isu token), tapi field `lead` dia adalah agregat standard Meta (lead form / messaging /
dll) — ia **TIDAK** capture custom pixel event `WhatsFormSubmit` yang akaun MO2 guna untuk
tracking lead. Test langsung (2026-11-20): campaign "161126 / FIZIKAL / WHATSFORM / ABO" ada
spend RM62.94 dan 2 lead sebenar (dari script asal), tapi connector punya field `lead` return
**null untuk semua 19 jam data hari ini** bagi campaign yang sama. Jangan guna connector untuk
gantikan report ni — nombor lead akan salah (nampak macam 0 lead walaupun ada).