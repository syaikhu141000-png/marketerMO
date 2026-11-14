// Enjin harian (dijalankan oleh GitHub Actions, percuma): tarik data Meta -> kira 10 seksyen -> simpan ke Cloudflare KV.
// Dashboard di Cloudflare Worker cuma baca hasilnya, jadi Worker kekal dalam had pelan percuma.
//
// Env wajib: META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, CF_ACCOUNT_ID, CF_KV_NAMESPACE_ID
// Env pilihan: META_API_VERSION (default v23.0)
import { writeFileSync, mkdirSync } from "node:fs";
import { buildData } from "./src/build.js";

const E = process.env;
for (const k of ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "CF_ACCOUNT_ID", "CF_KV_NAMESPACE_ID"])
  if (!E[k]) { console.error(`Env ${k} kosong. Isi dalam GitHub Secrets / workflow.`); process.exit(1); }

const KV = `https://api.cloudflare.com/client/v4/accounts/${E.CF_ACCOUNT_ID}/storage/kv/namespaces/${E.CF_KV_NAMESPACE_ID}/values/`;
const H = { Authorization: `Bearer ${E.CLOUDFLARE_API_TOKEN}` };

async function kvGet(key) {
  const r = await fetch(KV + encodeURIComponent(key), { headers: H });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`KV get ${key}: HTTP ${r.status} ${await r.text()}`);
  return r.text();
}
async function kvPut(key, body, ttl) {
  const r = await fetch(KV + encodeURIComponent(key) + (ttl ? `?expiration_ttl=${ttl}` : ""), {
    method: "PUT", headers: { ...H, "content-type": "text/plain" }, body,
  });
  if (!r.ok) throw new Error(`KV put ${key}: HTTP ${r.status} ${await r.text()}`);
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const env = { META_ACCESS_TOKEN: E.META_ACCESS_TOKEN, META_AD_ACCOUNT_ID: E.META_AD_ACCOUNT_ID, META_API_VERSION: E.META_API_VERSION || "v23.0" };
const startedAt = new Date().toISOString();
let status;
try {
  const prevRaw = await kvGet("data");
  const prev = prevRaw ? JSON.parse(prevRaw) : null;
  let out, lastErr;
  for (let i = 1; i <= 3; i++) { // cuba semula kalau Meta kenakan had sementara
    try { out = await buildData(env, prev); break; }
    catch (e) { lastErr = e; console.error(`Cubaan ${i} gagal: ${e.message}`); if (i < 3) await sleep(5 * 60 * 1000); }
  }
  if (!out) throw lastErr;
  const body = JSON.stringify(out.data);
  const day = out.data.accounts.mo2._meta.date_windows.yesterday;
  await kvPut("data", body);
  await kvPut(`history:${day}`, body, 60 * 60 * 24 * 400);
  status = { ok: true, trigger: "github-actions", started_at: startedAt, finished_at: new Date().toISOString(), data_until: day, ...out.stats };
  console.log("Berjaya:", JSON.stringify(status));
} catch (e) {
  status = { ok: false, trigger: "github-actions", started_at: startedAt, finished_at: new Date().toISOString(), error: String(e.message || e) };
  console.error("GAGAL:", status.error);
}
await kvPut("last_run", JSON.stringify(status)).catch((e) => console.error(e.message));
mkdirSync("docs", { recursive: true });
writeFileSync("docs/last_run.json", JSON.stringify(status, null, 1) + "\n"); // heartbeat (tiada data iklan)
process.exit(status.ok ? 0 : 1);
