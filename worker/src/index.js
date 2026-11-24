// Cloudflare Worker: Dashboard MO2 (Minda Optima 2 — Pantas Baca Daily Monitoring)
//
//  GET  /                -> dashboard (HTML, rupa sama Dashboard-MO-v3)
//  GET  /data.json       -> data dashboard terkini (dari KV)
//  GET  /api/data        -> sama, dengan CORS (untuk staff portal / sistem lain)
//  GET  /api/daily       -> data harian setiap ad (untuk pemilih tarikh / sistem lain)
//  GET  /api/status      -> status run terakhir (bila, berjaya/gagal, berapa panggilan API)
//  GET  /api/notes       -> semua notes/remark { key: [ {ts, text}, ... ] }
//  POST /api/notes       -> tambah satu note  body: {"key":"campaign:NAMA","text":"..."}
//  POST /api/refresh     -> tarik data dlm Worker (header X-Refresh-Key wajib; mungkin kena had CPU pelan percuma)
//  GET  /docs            -> dokumentasi untuk IT / AI (Markdown)
//  Enjin harian: GitHub Actions (worker/run_build.mjs) tarik data 5:07 pagi MYT & tulis ke KV ini.
//
//  GET  /api/rv2/state    -> kunci STATIC + catatan Report Marketing V2 (public) { locks, notes, at }
//  POST /api/rv2/check    -> semak password edit (header X-RV2-Password)  -> {ok:true/false}
//  POST /api/rv2/lock     -> tulis/padam SATU kunci STATIC (header X-RV2-Password wajib)
//                            body {"doc_id":"Facebook_2026-11-3","data":{...}} atau {"doc_id":"...","delete":true}
//  POST /api/rv2/note     -> tulis SATU catatan (header X-RV2-Password wajib)  body {"key":"Facebook_2026_W11-3","text":"..."}
//  GET  /api/rv2/meta     -> cache spend/lead Meta mingguan {at,ver,weeks} (public, read-only)
//  POST /api/rv2/meta     -> cantum (merge) minggu baru ke cache meta (header X-RV2-Password wajib)  body {"weeks":{"11-3":{...}}}
//  POST /api/rv2/import   -> migrasi sekali sahaja: ganti terus locks/notes/meta (header X-RV2-Password wajib)
//
// Binding: KV (namespace), META_AD_ACCOUNT_ID, META_API_VERSION (var), META_ACCESS_TOKEN & REFRESH_KEY & RV2_PASSWORD (secret)
// report-v2 (page public, Dashboard-MO-v3 repo) ambil locks/notes/meta DARI SINI SAHAJA — tiada lagi panggilan ke artifact claude.ai.

import { buildData } from "./build.js";
import DASHBOARD_HTML from "./dashboard.html";
import DOCS_MD from "./README.md";

const JSON_HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const CORS = { "access-control-allow-origin": "*", "access-control-allow-methods": "GET,POST,OPTIONS", "access-control-allow-headers": "content-type,x-refresh-key,x-rv2-password" };
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

const MAX_RV2_NOTE = 4000, MAX_RV2_KEY = 120, MAX_RV2_BYTES = 5 * 1024 * 1024;

function rv2Auth(env, req) {
  const pw = req.headers.get("x-rv2-password") || "";
  return !!env.RV2_PASSWORD && pw.length > 0 && pw === env.RV2_PASSWORD;
}

async function rv2State(env) {
  const locks = JSON.parse((await env.KV.get("rv2:locks")) || "{}");
  const notes = JSON.parse((await env.KV.get("rv2:notes")) || "{}");
  return { locks, notes };
}

async function rv2Lock(env, req) {
  if (!rv2Auth(env, req)) return json({ error: "Password salah." }, 401);
  let body;
  try { body = await req.json(); } catch { return json({ error: "Body mesti JSON." }, 400); }
  const doc_id = String(body.doc_id || "").trim();
  if (!doc_id || doc_id.length > MAX_RV2_KEY) return json({ error: "doc_id tak sah." }, 400);
  const locks = JSON.parse((await env.KV.get("rv2:locks")) || "{}");
  if (body.delete) delete locks[doc_id];
  else {
    if (!body.data || typeof body.data !== "object") return json({ error: "data wajib (objek)." }, 400);
    locks[doc_id] = { ...body.data, at: new Date().toISOString(), src: "edit public (password)" };
  }
  const out = JSON.stringify(locks);
  if (out.length > MAX_RV2_BYTES) return json({ error: "Storan locks penuh." }, 413);
  await env.KV.put("rv2:locks", out);
  return json({ ok: true, doc_id, deleted: !!body.delete });
}

async function rv2Meta(env, req) {
  if (req.method === "GET") {
    const meta = JSON.parse((await env.KV.get("rv2:meta")) || '{"at":null,"ver":null,"weeks":{}}');
    return json(meta);
  }
  if (!rv2Auth(env, req)) return json({ error: "Password salah." }, 401);
  let body;
  try { body = await req.json(); } catch { return json({ error: "Body mesti JSON." }, 400); }
  const cur = JSON.parse((await env.KV.get("rv2:meta")) || '{"at":null,"ver":null,"weeks":{}}');
  const weeks = { ...(cur.weeks || {}) };
  if (body.weeks && typeof body.weeks === "object") {
    for (const k in body.weeks) { if (/^\d{1,2}-[1-4]$/.test(k)) weeks[k] = body.weeks[k]; }
  }
  const out = { at: new Date().toISOString(), ver: body.ver || cur.ver || null, weeks };
  const str = JSON.stringify(out);
  if (str.length > MAX_RV2_BYTES) return json({ error: "Storan meta penuh." }, 413);
  await env.KV.put("rv2:meta", str);
  return json({ ok: true, weeks: Object.keys(weeks).length });
}

async function rv2Import(env, req) {
  // Migrasi sekali sahaja: ganti terus rv2:locks/rv2:notes/rv2:meta (password wajib). Tak pernah dipanggil oleh page public.
  if (!rv2Auth(env, req)) return json({ error: "Password salah." }, 401);
  let body;
  try { body = await req.json(); } catch { return json({ error: "Body mesti JSON." }, 400); }
  const r = {};
  if (body.locks && typeof body.locks === "object") { const s = JSON.stringify(body.locks); if (s.length > MAX_RV2_BYTES) return json({ error: "locks terlalu besar." }, 413); await env.KV.put("rv2:locks", s); r.locks = Object.keys(body.locks).length; }
  if (body.notes && typeof body.notes === "object") { const s = JSON.stringify(body.notes); if (s.length > MAX_RV2_BYTES) return json({ error: "notes terlalu besar." }, 413); await env.KV.put("rv2:notes", s); r.notes = Object.keys(body.notes).length; }
  if (body.meta && typeof body.meta === "object") { const s = JSON.stringify(body.meta); if (s.length > MAX_RV2_BYTES) return json({ error: "meta terlalu besar." }, 413); await env.KV.put("rv2:meta", s); r.meta = Object.keys(body.meta.weeks || {}).length; }
  return json({ ok: true, ...r });
}

async function rv2Note(env, req) {
  if (!rv2Auth(env, req)) return json({ error: "Password salah." }, 401);
  let body;
  try { body = await req.json(); } catch { return json({ error: "Body mesti JSON." }, 400); }
  const key = String(body.key || "").trim();
  if (!key || key.length > MAX_RV2_KEY) return json({ error: "key tak sah." }, 400);
  if (!body.data || typeof body.data !== "object") return json({ error: "data wajib (objek)." }, 400);
  if (JSON.stringify(body.data).length > MAX_RV2_NOTE) return json({ error: `data terlalu panjang (max ${MAX_RV2_NOTE} aksara).` }, 400);
  const notes = JSON.parse((await env.KV.get("rv2:notes")) || "{}");
  const hasText = Object.keys(body.data).some((k) => k !== "key" && k !== "at" && String(body.data[k] || "").trim());
  if (!hasText) delete notes[key];
  else notes[key] = { ...body.data, key, at: new Date().toISOString() };
  const out = JSON.stringify(notes);
  if (out.length > MAX_RV2_BYTES) return json({ error: "Storan notes penuh." }, 413);
  await env.KV.put("rv2:notes", out);
  return json({ ok: true, key });
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
    if (p === "/api/daily") {
      const d = await env.KV.get("daily");
      if (!d) return json({ error: "Data harian belum dijana." }, 503);
      return new Response(d, { headers: { ...JSON_HEADERS, ...CORS } });
    }
    if (p === "/api/status") return json(JSON.parse((await env.KV.get("last_run")) || '{"ok":null,"note":"belum pernah run"}'));

    if (p === "/api/notes" && req.method === "GET") return new Response((await env.KV.get("notes")) || "{}", { headers: { ...JSON_HEADERS, ...CORS } });
    if (p === "/api/notes" && req.method === "POST") return addNote(env, req);

    if (p === "/api/refresh" && req.method === "POST") {
      if (!env.REFRESH_KEY || req.headers.get("x-refresh-key") !== env.REFRESH_KEY) return json({ error: "X-Refresh-Key salah." }, 401);
      return json(await refresh(env, "manual"));
    }
    if (p === "/api/rv2/state" && req.method === "GET") return json(await rv2State(env));
    if (p === "/api/rv2/check" && req.method === "POST") return json({ ok: rv2Auth(env, req) });
    if (p === "/api/rv2/lock" && req.method === "POST") return rv2Lock(env, req);
    if (p === "/api/rv2/note" && req.method === "POST") return rv2Note(env, req);
    if (p === "/api/rv2/meta" && (req.method === "GET" || req.method === "POST")) return rv2Meta(env, req);
    if (p === "/api/rv2/import" && req.method === "POST") return rv2Import(env, req);

    if (p === "/docs" || p === "/api/docs" || p === "/README.md")
      return new Response(DOCS_MD, { headers: { "content-type": "text/markdown; charset=utf-8", ...CORS } });

    return json({ error: "Tidak dijumpai", routes: ["/", "/data.json", "/api/data", "/api/status", "/api/notes", "/docs"] }, 404);
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(refresh(env, "cron"));
  },
};
