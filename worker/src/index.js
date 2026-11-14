// Cloudflare Worker: Dashboard MO2 (Minda Optima 2 — Pantas Baca Daily Monitoring)
//
//  GET  /                -> dashboard (HTML, rupa sama Dashboard-MO-v3)
//  GET  /data.json       -> data dashboard terkini (dari KV)
//  GET  /api/data        -> sama, dengan CORS (untuk staff portal / sistem lain)
//  GET  /api/status      -> status run terakhir (bila, berjaya/gagal, berapa panggilan API)
//  GET  /api/notes       -> semua notes/remark { key: [ {ts, text}, ... ] }
//  POST /api/notes       -> tambah satu note  body: {"key":"campaign:NAMA","text":"..."}
//  POST /api/refresh     -> tarik data dlm Worker (header X-Refresh-Key wajib; mungkin kena had CPU pelan percuma)
//  GET  /docs            -> dokumentasi untuk IT / AI (Markdown)
//  Enjin harian: GitHub Actions (worker/run_build.mjs) tarik data 5:07 pagi MYT & tulis ke KV ini.
//
// Binding: KV (namespace), META_AD_ACCOUNT_ID, META_API_VERSION (var), META_ACCESS_TOKEN & REFRESH_KEY (secret)

import { buildData } from "./build.js";
import DASHBOARD_HTML from "./dashboard.html";
import DOCS_MD from "./README.md";

const JSON_HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const CORS = { "access-control-allow-origin": "*", "access-control-allow-methods": "GET,POST,OPTIONS", "access-control-allow-headers": "content-type,x-refresh-key" };
const MAX_NOTE = 2000, MAX_KEY = 300, MAX_NOTES_BYTES = 20 * 1024 * 1024;

const json = (obj, status = 200, extra = {}) => new Response(JSON.stringify(obj), { status, headers: { ...JSON_HEADERS, ...CORS, ...extra } });

async function refresh(env, trigger) {
  const startedAt = new Date().toISOString();
  try {
    if (!env.META_ACCESS_TOKEN) throw new Error("Secret META_ACCESS_TOKEN belum diisi dalam Cloudflare (Settings > Variables and Secrets).");
    const prevRaw = await env.KV.get("data");
    const prev = prevRaw ? JSON.parse(prevRaw) : null;
    const { data, stats } = await buildData(env, prev);
    const body = JSON.stringify(data);
    await env.KV.put("data", body);
    const day = data.accounts.mo2._meta.date_windows.yesterday;
    await env.KV.put(`history:${day}`, body, { expirationTtl: 60 * 60 * 24 * 400 }); // simpan ~13 bulan
    const status = { ok: true, trigger, started_at: startedAt, finished_at: new Date().toISOString(), data_until: day, ...stats };
    await env.KV.put("last_run", JSON.stringify(status));
    return status;
  } catch (e) {
    const status = { ok: false, trigger, started_at: startedAt, finished_at: new Date().toISOString(), error: String(e && e.message || e) };
    await env.KV.put("last_run", JSON.stringify(status));
    return status;
  }
}

async function addNote(env, req) {
  let body;
  try { body = await req.json(); } catch { return json({ error: "Body mesti JSON: {\"key\":\"...\",\"text\":\"...\"}" }, 400); }
  const key = String(body.key || "").trim(), text = String(body.text || "").trim();
  if (!key || !text) return json({ error: "key dan text wajib diisi." }, 400);
  if (key.length > MAX_KEY || text.length > MAX_NOTE) return json({ error: `key max ${MAX_KEY} aksara, text max ${MAX_NOTE} aksara.` }, 400);
  const notes = JSON.parse((await env.KV.get("notes")) || "{}");
  const t = new Date(Date.now() + 8 * 3600000); // waktu Malaysia
  const ts = body.ts && /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(body.ts) ? body.ts : t.toISOString().slice(0, 16).replace("T", " ");
  const entry = { ts, text };
  notes[key] = [entry, ...(Array.isArray(notes[key]) ? notes[key] : [])];
  const out = JSON.stringify(notes);
  if (out.length > MAX_NOTES_BYTES) return json({ error: "Storan notes penuh." }, 413);
  await env.KV.put("notes", out);
  return json({ ok: true, key, entry });
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    const p = url.pathname.replace(/\/+$/, "") || "/";
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });

    if (p === "/" || p === "/index.html")
      return new Response(DASHBOARD_HTML, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-cache" } });

    if (p === "/data.json" || p === "/api/data") {
      const d = await env.KV.get("data");
      if (!d) return json({ error: "Data belum dijana. Tunggu cron 5:30 pagi atau jalankan /api/refresh." }, 503);
      return new Response(d, { headers: { ...JSON_HEADERS, ...CORS } });
    }
    if (p === "/api/status") return json(JSON.parse((await env.KV.get("last_run")) || '{"ok":null,"note":"belum pernah run"}'));

    if (p === "/api/notes" && req.method === "GET") return new Response((await env.KV.get("notes")) || "{}", { headers: { ...JSON_HEADERS, ...CORS } });
    if (p === "/api/notes" && req.method === "POST") return addNote(env, req);

    if (p === "/api/refresh" && req.method === "POST") {
      if (!env.REFRESH_KEY || req.headers.get("x-refresh-key") !== env.REFRESH_KEY) return json({ error: "X-Refresh-Key salah." }, 401);
      return json(await refresh(env, "manual"));
    }
    if (p === "/docs" || p === "/api/docs" || p === "/README.md")
      return new Response(DOCS_MD, { headers: { "content-type": "text/markdown; charset=utf-8", ...CORS } });

    return json({ error: "Tidak dijumpai", routes: ["/", "/data.json", "/api/data", "/api/status", "/api/notes", "/docs"] }, 404);
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(refresh(env, "cron"));
  },
};
