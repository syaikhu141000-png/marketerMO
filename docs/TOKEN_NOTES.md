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