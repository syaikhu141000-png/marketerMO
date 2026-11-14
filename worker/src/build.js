// Penjana data dashboard MO2 (format sama Dashboard-MO-v3, 10 seksyen) terus dari Meta Marketing API.
// Port JavaScript bagi scripts/build_dashboard_data.py — dijalankan oleh Cloudflare Worker (cron 5:30 pagi MYT).
//
// Lead = WhatsFormSubmit + Website leads. Chat WhatsApp TIDAK dikira. Kempen AWARENESS dikecualikan dari CPL.
// Traffic light (ikut dashboard lama):
//   OLD (umur >= 14 hari): CPL 7D (fallback 14D)  🟢 <=15 · 🟡 <30 · 🔴 >=30 ; tiada lead & spend >= RM30 -> 🔴
//   NEW (umur < 14 hari) : CPL kalau ada lead, kalau 0 lead ikut spend  🟢 <=30 · 🟡 <=55 · 🔴 >55

const LEAD_TYPES = new Set(["lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead", "onsite_web_lead"]);
const FORM_TYPE = "offsite_conversion.fb_pixel_custom"; // WhatsFormSubmit
const GUARDRAIL_MIN = 20, GUARDRAIL_MAX = 2700;
const NEW_DAYS = 14;
const WINS = ["yesterday", "3D", "7D", "14D", "30D"];
const INS = "spend,impressions,reach,frequency,inline_link_clicks,actions";

// ---------------- helper ----------------
const r2 = (x) => (x == null || Number.isNaN(x) ? null : Math.round(x * 100) / 100);
const cpl = (s, l) => (l ? r2(s / l) : null);
const pct = (n, o) => (!o || n == null ? null : ((n - o) / o) * 100);
const fmt2 = (x) => Number(x).toFixed(2);
const money = (x) => Number(x).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function arrow(n, o) {
  const p = pct(n, o);
  if (p == null) return "—";
  const s = (p >= 0 ? "+" : "") + p.toFixed(1) + "%";
  if (Math.abs(p) < 1) return `≈ stabil (${s})`;
  return `${p > 0 ? "▲" : "▼"} ${s}`;
}
function leadsOf(actions) {
  let web = 0, form = 0;
  for (const a of actions || []) {
    const v = Math.trunc(Number(a.value));
    if (LEAD_TYPES.has(a.action_type)) web = Math.max(web, v);
    else if (a.action_type === FORM_TYPE) form = v;
  }
  return [form, web];
}
function stat(r = {}) {
  const [form, web] = leadsOf(r.actions);
  return {
    spend: Number(r.spend || 0), impressions: Math.trunc(Number(r.impressions || 0)), reach: Math.trunc(Number(r.reach || 0)),
    frequency: Number(r.frequency || 0), link_click: Math.trunc(Number(r.inline_link_clicks || 0)), form, web, leads: form + web,
  };
}
const tlOld = (c, spend) => (c == null ? (spend >= 30 ? "🔴 RED" : "🟢 GREEN") : c <= 15 ? "🟢 GREEN" : c < 30 ? "🟡 YELLOW" : "🔴 RED");
const tlNew = (v) => (v <= 30 ? "🟢 GREEN" : v <= 55 ? "🟡 YELLOW" : "🔴 RED");
const tlc = (t) => (t.includes("🔴") ? "red" : t.includes("🟡") ? "yellow" : t.includes("🟢") ? "green" : "na");

function classify(age, sp7, sp14, c7, c14) {
  const c = c7 != null ? c7 : c14;
  const s = sp7 || sp14 || 0;
  if (age != null && age < NEW_DAYS) {
    if (c != null) return ["NEW", tlNew(c), `CPL-based (RM${fmt2(c)})`];
    return ["NEW", tlNew(s), `Spend-based (RM${fmt2(s)}, 0 leads)`];
  }
  if (c != null) return ["OLD", tlOld(c, s), `CPL-based (RM${fmt2(c)})`];
  return ["OLD", tlOld(null, s), `Spend-based (RM${fmt2(s)}, 0 leads)`];
}
function actionFor(tl, cls, status, c7) {
  const t = tlc(tl);
  if (String(status).includes("PAUSED")) return ["H", "Kekal PAUSED - sahkan dgn owner sama ada nak archive atau re-test dgn creative baru."];
  if (t === "red") {
    if (cls === "NEW") return ["R", "Review spend vs CPL - testing baru, jangan tambah budget sebelum cukup data leads."];
    return ["R", "Semak/refresh adset & ad lama berprestasi rendah; jangan naikkan budget sebelum CPL turun."];
  }
  if (t === "yellow") return ["M", "Monitor - hold budget, pantau trend CPL 7D/14D."];
  if (c7 != null && c7 <= 15) return ["S", "Pertimbang scale budget +20% (perlu approval) - CPL dalam sasaran."];
  return ["M", "Maintain - teruskan pantau."];
}
const isAwareness = (name, obj) => /AWARENESS|BRAND/i.test(name || "") || obj === "OUTCOME_AWARENESS";

// ---------------- tarikh (waktu Malaysia, UTC+8 tanpa DST) ----------------
const DAY = 86400000;
const iso = (d) => d.toISOString().slice(0, 10);
const addDays = (d, n) => new Date(d.getTime() + n * DAY);
function mytToday() {
  const t = new Date(Date.now() + 8 * 3600000);
  return new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth(), t.getUTCDate()));
}
const ageDays = (created, today) => (created ? Math.round((today - Date.parse(created.slice(0, 10) + "T00:00:00Z")) / DAY) : null);

// ---------------- Meta API ----------------
function metaClient(env) {
  const ver = env.META_API_VERSION || "v23.0";
  const token = env.META_ACCESS_TOKEN;
  let calls = 0;
  async function getUrl(url) {
    calls++;
    const res = await fetch(url);
    const j = await res.json();
    if (j.error) throw new Error(`Meta API ralat code ${j.error.code}: ${j.error.message}`);
    return j;
  }
  function url(path, params = {}) {
    const p = new URLSearchParams(params);
    if (token && token !== "proxy-injected") p.set("access_token", token);
    return `https://graph.facebook.com/${ver}/${path}?${p}`;
  }
  return {
    get: (path, params) => getUrl(url(path, params)),
    async all(path, params) {
      let j = await getUrl(url(path, params));
      const out = [...(j.data || [])];
      while (j.paging && j.paging.next) {
        j = await getUrl(j.paging.next);
        out.push(...(j.data || []));
      }
      return out;
    },
    calls: () => calls,
  };
}

// ---------------- utama ----------------
export async function buildData(env, prevData) {
  const meta = metaClient(env);
  let acc = env.META_AD_ACCOUNT_ID || "";
  if (!acc.startsWith("act_")) acc = "act_" + acc;

  const now = new Date();
  const today = mytToday();
  const Y = addDays(today, -1);
  const mStart = new Date(Date.UTC(Y.getUTCFullYear(), Y.getUTCMonth(), 1));
  const lmEnd = addDays(mStart, -1);
  const lmStart = new Date(Date.UTC(lmEnd.getUTCFullYear(), lmEnd.getUTCMonth(), 1));
  const ranges = {
    yesterday: [Y, Y], "3D": [addDays(Y, -2), Y], "7D": [addDays(Y, -6), Y], "14D": [addDays(Y, -13), Y],
    "30D": [addDays(Y, -29), Y], this_month: [mStart, Y], last_month: [lmStart, lmEnd],
  };
  const ytd = [new Date(Date.UTC(Y.getUTCFullYear(), 0, 1)), Y];
  const tr = ([a, b]) => JSON.stringify({ since: iso(a), until: iso(b) });

  const [info, campList, adsetList, adList] = await Promise.all([
    meta.get(acc, { fields: "name,currency,timezone_name,business{name}" }),
    meta.all(`${acc}/campaigns`, { fields: "id,name,effective_status,objective,created_time,daily_budget", limit: "200" }),
    meta.all(`${acc}/adsets`, { fields: "id,name,campaign_id,effective_status,daily_budget,created_time", limit: "500" }),
    meta.all(`${acc}/ads`, { fields: "id,name,adset_id,campaign_id,effective_status,created_time", limit: "500" }),
  ]);
  const campaigns = Object.fromEntries(campList.map((x) => [x.id, x]));
  const adsets = Object.fromEntries(adsetList.map((x) => [x.id, x]));
  const ads = Object.fromEntries(adList.map((x) => [x.id, x]));
  const awareIds = campList.filter((c) => isAwareness(c.name, c.objective)).map((c) => c.id);

  const insights = (level, rng, extra) => {
    const p = { level, time_range: tr(rng), fields: INS + (extra ? "," + extra : ""), limit: "500" };
    if (awareIds.length && level === "account")
      p.filtering = JSON.stringify([{ field: "campaign.id", operator: "NOT_IN", value: awareIds }]);
    return meta.all(`${acc}/insights`, p);
  };
  const byId = (rows, k) => Object.fromEntries(rows.map((r) => [r[k], stat(r)]));

  const acctKeys = Object.keys(ranges);
  const [acctRows, campRowsW, adsetRowsW, adRowsW, ytdAcctRows, ytdCampRows] = await Promise.all([
    Promise.all(acctKeys.map((k) => insights("account", ranges[k]))),
    Promise.all(WINS.map((k) => insights("campaign", ranges[k], "campaign_id"))),
    Promise.all(["3D", "7D", "14D"].map((k) => insights("adset", ranges[k], "adset_id"))),
    Promise.all(["7D", "14D"].map((k) => insights("ad", ranges[k], "ad_id"))),
    meta.all(`${acc}/insights`, { level: "account", time_range: tr(ytd), fields: INS }),
    insights("campaign", ytd, "campaign_id"),
  ]);
  const acct = Object.fromEntries(acctKeys.map((k, i) => [k, stat(acctRows[i][0])]));
  const campW = Object.fromEntries(WINS.map((k, i) => [k, byId(campRowsW[i], "campaign_id")]));
  const adsetW = Object.fromEntries(["3D", "7D", "14D"].map((k, i) => [k, byId(adsetRowsW[i], "adset_id")]));
  const adW = Object.fromEntries(["7D", "14D"].map((k, i) => [k, byId(adRowsW[i], "ad_id")]));
  const ytdAcct = stat(ytdAcctRows[0]);
  const ytdCamp = byId(ytdCampRows, "campaign_id");
  const s0 = (d, id) => d[id] || stat();

  const prev = (prevData && prevData.accounts && prevData.accounts.mo2) || {};
  const prevFlags = Object.fromEntries(((prev.section_2_red_flags || {}).flags || []).map((f) => [f.entity, f]));
  const prevCamp = Object.fromEntries(((prev.section_5_campaign_summary || {}).campaigns || []).map((x) => [x.campaign, x]));

  // ---------- Section 5: campaign ----------
  const campRows = [];
  for (const [cid, cm] of Object.entries(campaigns)) {
    if (awareIds.includes(cid)) continue;
    const w = Object.fromEntries(WINS.map((k) => [k, s0(campW[k], cid)]));
    if (w["30D"].spend <= 0 && cm.effective_status !== "ACTIVE") continue;
    const sp = {}, ld = {}, cp = {};
    for (const k of WINS) { sp[k] = r2(w[k].spend); ld[k] = w[k].leads; cp[k] = cpl(w[k].spend, w[k].leads); }
    const age = ageDays(cm.created_time, today);
    const [cls, tl, basis] = classify(age, sp["7D"], sp["14D"], cp["7D"], cp["14D"]);
    const conv = w["30D"].web > w["30D"].form || cm.objective === "OUTCOME_LEADS" ? "Website leads" : "WhatsFormSubmit";
    const [code, act] = actionFor(tl, cls, cm.effective_status, cp["7D"]);
    const hasTrend = cp["7D"] != null && cp["14D"] != null;
    campRows.push({
      campaign: cm.name, status: cm.effective_status, class: cls, age_days: age, spend: sp, leads: ld, whatsform_leads: ld,
      cpl: cp, traffic_light: tl, trend: hasTrend ? "CPL 7D vs 14D " + arrow(cp["7D"], cp["14D"]) : basis, basis,
      conv_type: conv, frequency_14D: r2(w["14D"].frequency) || null, action: act, action_code: code,
    });
  }
  campRows.sort((a, b) => (b.spend["14D"] || 0) - (a.spend["14D"] || 0));

  // ---------- Section 6: adset ----------
  const adsetRows = [];
  for (const [aid, a] of Object.entries(adsets)) {
    if (awareIds.includes(a.campaign_id)) continue;
    const w = { "3D": s0(adsetW["3D"], aid), "7D": s0(adsetW["7D"], aid), "14D": s0(adsetW["14D"], aid) };
    if (a.effective_status !== "ACTIVE" && w["14D"].spend <= 0) continue;
    const sp = {}, ld = {}, cp = {};
    for (const k of Object.keys(w)) { sp[k] = r2(w[k].spend); ld[k] = w[k].leads; cp[k] = cpl(w[k].spend, w[k].leads); }
    const age = ageDays(a.created_time, today);
    const [cls, tl, basis] = classify(age, sp["7D"], sp["14D"], cp["7D"], cp["14D"]);
    const [code, act] = actionFor(tl, cls, a.effective_status, cp["7D"]);
    adsetRows.push({
      adset: a.name, campaign: (campaigns[a.campaign_id] || {}).name || "", status: a.effective_status, class: cls, age_days: age,
      daily_budget: a.daily_budget ? r2(Number(a.daily_budget) / 100) : null, spend: sp, leads: ld, whatsform_leads: ld, cpl: cp,
      traffic_light: tl, trend: cp["7D"] != null && cp["14D"] != null ? arrow(cp["7D"], cp["14D"]) : basis,
      frequency_14D: r2(w["14D"].frequency) || null, action: act, action_code: code,
    });
  }

  // ---------- Section 7: ads ----------
  const adRow = (adid, s, sp7, sp14, l7, l14) => {
    const a = ads[adid] || {};
    const [cls, tl, basis] = classify(ageDays(a.created_time, today), sp7, sp14, cpl(sp7, l7), cpl(sp14, l14));
    const row = {
      ad: a.name || adid, adset: (adsets[a.adset_id] || {}).name || "", campaign: (campaigns[a.campaign_id] || {}).name || "",
      status: a.effective_status || "?", spend: r2(s.spend), whatsform_leads: s.leads, cpl: cpl(s.spend, s.leads),
      frequency: r2(s.frequency) || null, class: cls, traffic_light: tl, basis,
    };
    if (s.leads === 0 && s.spend >= 90) row.flag = `0 lead dgn spend RM${fmt2(s.spend)} - cadang semak/OFF (perlu approval)`;
    return row;
  };
  const notAware = (adid) => !(ads[adid] && awareIds.includes(ads[adid].campaign_id));
  const ads14 = Object.entries(adW["14D"]).filter(([id, s]) => notAware(id) && s.spend >= 20)
    .map(([id, s]) => { const s7 = s0(adW["7D"], id); return adRow(id, s, s7.spend, s.spend, s7.leads, s.leads); })
    .sort((a, b) => b.spend - a.spend);
  const ads7 = Object.entries(adW["7D"]).filter(([id, s]) => notAware(id) && s.spend > 0)
    .sort((a, b) => b[1].spend - a[1].spend).slice(0, 40)
    .map(([id, s]) => { const s14 = s0(adW["14D"], id); return adRow(id, s, s.spend, s14.spend, s.leads, s14.leads); });

  // ---------- Section 3: overview ----------
  const mrow = (s) => ({
    spend: r2(s.spend), leads: s.leads, whatsform_leads: s.form, website_leads: s.web, cpl: cpl(s.spend, s.leads),
    impressions: s.impressions, reach: s.reach, frequency: s.frequency ? Math.round(s.frequency * 10000) / 10000 : null,
    link_click: s.link_click, ctr_pct: s.impressions ? r2((s.link_click / s.impressions) * 100) : null,
    cpm: s.impressions ? r2((s.spend / s.impressions) * 1000) : null,
  });
  const metrics = Object.fromEntries(acctKeys.map((k) => [k, mrow(acct[k])]));
  const m7 = metrics["7D"], m14 = metrics["14D"], m30 = metrics["30D"];
  const cpc = (m) => (m.link_click ? m.spend / m.link_click : null);

  const types = {
    whatsform: { label: "WhatsFormSubmit", indicator: "conversions:offsite_conversion.fb_pixel_custom.WhatsFormSubmit", results: 0, spend: 0 },
    website_leads: { label: "Website leads", indicator: "actions:offsite_conversion.fb_pixel_lead", results: 0, spend: 0 },
  };
  let awareSpendYtd = 0;
  for (const [cid, s] of Object.entries(ytdCamp)) {
    if (awareIds.includes(cid)) { awareSpendYtd += s.spend; continue; }
    if (!s.leads) continue;
    types.whatsform.results += s.form;
    types.website_leads.results += s.web;
    types[s.web > s.form ? "website_leads" : "whatsform"].spend += s.spend;
  }
  const convTypes = Object.entries(types).map(([key, t]) => ({ key, label: t.label, indicator: t.indicator, results: t.results, spend: r2(t.spend), cpl: cpl(t.spend, t.results) }));
  const combRes = convTypes.reduce((a, t) => a + t.results, 0);
  const combSp = convTypes.reduce((a, t) => a + (t.spend || 0), 0);
  const sec3 = {
    metrics,
    total_this_year: {
      period: `${iso(ytd[0])}..${iso(ytd[1])}`,
      note: "Spend/impressions/reach/frequency = semua campaign (termasuk awareness), terus dari API. Lead = WhatsFormSubmit + Website leads sahaja (chat WhatsApp tidak dikira).",
      spend: r2(ytdAcct.spend), impressions: ytdAcct.impressions, reach: ytdAcct.reach, frequency: r2(ytdAcct.frequency),
      conversion_types: convTypes, combined: { results: combRes, spend: r2(combSp), cpl: cpl(combSp, combRes) },
      excluded_note: `Dikecualikan dari combined: kempen AWARENESS RM${money(awareSpendYtd)}.`,
    },
    cpl_basis: "CPL gabungan WhatsFormSubmit + Website leads, semua campaign lead-gen (excl. AWARENESS). Chat tidak dikira.",
    traffic_light_account_cpl: tlOld(m7.cpl, m7.spend || 0),
    trend_7D_vs_14D: {
      cpl: arrow(m7.cpl, m14.cpl), ctr: arrow(m7.ctr_pct, m14.ctr_pct), cpc: arrow(cpc(m7), cpc(m14)),
      cpm: arrow(m7.cpm, m14.cpm), cpl_vs_30D: arrow(m7.cpl, m30.cpl),
    },
    purpose: "Prestasi akaun mengikut window masa (excl. AWARENESS).",
  };

  // ---------- Section 4: trend ----------
  const days = { yesterday: 1, "3D": 3, "7D": 7, "14D": 14, "30D": 30 };
  const series = Object.fromEntries(WINS.map((k) => [k, { spend: metrics[k].spend, leads: metrics[k].leads, cpl: metrics[k].cpl }]));
  const lpd = Object.fromEntries(WINS.map((k) => [k, r2(metrics[k].leads / days[k])]));
  const slope = m7.cpl != null && m14.cpl != null ? r2(m7.cpl - m14.cpl) : null;
  const obs = (slope != null ? `CPL 7D ${slope > 0 ? "lebih tinggi" : "lebih rendah"} drpd 14D, slope RM${slope >= 0 ? "+" : ""}${fmt2(slope)}. ` : "") +
    `Leads/hari: semalam=${lpd.yesterday}, 7D=${lpd["7D"]}, 14D=${lpd["14D"]}, 30D=${lpd["30D"]}.`;
  const sec4 = {
    series, cpl_slope_7D_vs_14D: slope, leads_per_day_3D: lpd["3D"], leads_per_day_7D: lpd["7D"], leads_per_day_14D: lpd["14D"],
    leads_per_day_30D: lpd["30D"], observation: obs, note: "Window dikira hingga semalam (hari penuh terakhir, waktu Malaysia).",
    purpose: "Trend spend, leads & CPL merentas window masa.",
  };

  // ---------- Section 2: red flags ----------
  const flags = [];
  const activeLead = campRows.filter((x) => x.status === "ACTIVE");
  if (!activeLead.length)
    flags.push({
      priority: "P1", level: "HIGH", entity: "Akaun " + info.name, traffic_light: "🔴 RED",
      issue: "Tiada campaign lead-gen ACTIVE - lead baru tak masuk dari akaun ni.",
      evidence: { spend_yesterday: metrics.yesterday.spend || 0, leads_yesterday: metrics.yesterday.leads },
      suggested_action: "Sahkan dgn owner sama ada pause ni sengaja. Kalau tak, hidupkan semula campaign terbaik (perlu approval).",
    });
  for (const x of campRows) {
    const t = tlc(x.traffic_light);
    if (!(t === "red" || t === "yellow") || (x.spend["7D"] || 0) <= 0) continue;
    const act = x.status === "ACTIVE";
    const pr = t === "red" && act ? "P1" : t === "red" ? "P2" : act ? "P3" : "P4";
    const was = prevFlags[x.campaign];
    const tag = was ? (was.traffic_light === x.traffic_light ? "Kekal" : "Berubah") : "BARU";
    flags.push({
      priority: pr, level: t === "red" ? "HIGH" : "LOW", entity: x.campaign, traffic_light: x.traffic_light,
      issue: `${tag} ${t.toUpperCase()} - ${x.basis} (${x.status}, ${x.age_days} hari).`,
      evidence: { cpl_7D: x.cpl["7D"], cpl_14D: x.cpl["14D"], spend_14D: x.spend["14D"] }, suggested_action: x.action,
    });
  }
  for (const x of [...adsetRows].sort((a, b) => (b.spend["7D"] || 0) - (a.spend["7D"] || 0))) {
    if (tlc(x.traffic_light) === "red" && (x.spend["7D"] || 0) >= 100 && flags.length < 12)
      flags.push({
        priority: "P2", level: "HIGH", entity: x.adset, traffic_light: x.traffic_light,
        issue: `Ad set RED - ${x.trend} (${x.status}, ${x.age_days} hari).`,
        evidence: { cpl_7D: x.cpl["7D"], cpl_14D: x.cpl["14D"], spend_7D: x.spend["7D"] }, suggested_action: x.action,
      });
  }
  const order = { P1: 0, P2: 1, P3: 2, P4: 3 };
  flags.sort((a, b) => (order[a.priority] ?? 9) - (order[b.priority] ?? 9));
  for (const f of flags) f.evidence = Object.fromEntries(Object.entries(f.evidence).filter(([, v]) => v != null));
  const cur = new Set(flags.map((f) => f.entity));
  const resolved = Object.entries(prevFlags).filter(([e]) => !cur.has(e)).map(([e, f]) => ({
    entity: e, previous_traffic_light: f.traffic_light,
    current_traffic_light: (campRows.find((c) => c.campaign === e) || {}).traffic_light || "⚪ tiada data",
    note: "Tiada lagi dalam senarai flag run ni.",
  }));
  const statusChanges = campRows.filter((x) => prevCamp[x.campaign] && prevCamp[x.campaign].status !== x.status)
    .map((x) => ({ entity: x.campaign, from: prevCamp[x.campaign].status, to: x.status }));
  const sec2 = {
    flags, resolved_since_last_run: resolved, status_changes_since_last_run: statusChanges,
    note: prev._meta ? `${resolved.length} resolved, ${statusChanges.length} perubahan status berbanding run lepas.` : "Run pertama - tiada perbandingan.",
    purpose: "Senarai campaign/adset bermasalah (RED/YELLOW) + apa yang berubah berbanding run sebelum ni.",
  };

  // ---------- Section 1: budget ----------
  const activeAdsets = adsetRows.filter((a) => a.status === "ACTIVE");
  let budget = activeAdsets.reduce((a, x) => a + (x.daily_budget || 0), 0);
  for (const [cid, cm] of Object.entries(campaigns))
    if (cm.daily_budget && cm.effective_status === "ACTIVE" && !awareIds.includes(cid)) budget += Number(cm.daily_budget) / 100;
  budget = r2(budget);
  const sy = metrics.yesterday.spend || 0;
  const rr = { avg_daily_spend_3D: r2((metrics["3D"].spend || 0) / 3), avg_daily_spend_7D: r2((m7.spend || 0) / 7), avg_daily_spend_14D: r2((m14.spend || 0) / 14) };
  const pace = !budget ? "⚪ Tiada budget lead-gen ACTIVE" : rr.avg_daily_spend_7D > GUARDRAIL_MAX ? "🔴 Melebihi guardrail"
    : sy < budget * 0.5 ? "🟡 Underspend (spend semalam < 50% budget)" : "🟢 Dalam guardrail";
  const sec1 = {
    daily_budget_total_active_ABO: budget, spend_yesterday: r2(sy), run_rate_vs_budget_pct: budget ? r2((sy / budget) * 100) : null,
    guardrail_min: GUARDRAIL_MIN, guardrail_max: GUARDRAIL_MAX, recent_daily_run_rate: rr, pace_status: pace,
    purpose: "Ringkasan bajet harian akaun: spend semalam, jumlah budget aktif, run-rate vs budget, guardrail, dan trend run-rate 3D/7D/14D.",
    spend_yesterday_note: `Spend lead-gen semalam RM${money(sy)}` + (budget ? `, ${((sy / budget) * 100).toFixed(1)}% drpd budget aktif RM${money(budget)}.` : "."),
    daily_budget_note: `Total daily_budget ${activeAdsets.length} adset ACTIVE (excl. AWARENESS) = RM${money(budget)}.`,
    run_rate_vs_budget_note: `Purata spend harian: 3D RM${rr.avg_daily_spend_3D}, 7D RM${rr.avg_daily_spend_7D}, 14D RM${rr.avg_daily_spend_14D}.`,
  };

  // ---------- Section 8 & 9 (auto, tiada perubahan di Meta) ----------
  const lvl = { P1: "P1 · High", P2: "P2 · Med", P3: "P3 · Low", P4: "P4 · Low" };
  const evTxt = (ev) => Object.entries(ev).map(([k, v]) => `${k} ${/^(cpl|spend)/.test(k) ? "RM" + fmt2(v) : v}`).join(", ");
  const items = flags.slice(0, 6).map((f, i) => ({
    n: i + 1, level: f.level, priority: lvl[f.priority] || f.priority, needs_approval: true, entity: f.entity,
    diagnosis: `${f.traffic_light} - ${f.issue}`, evidence: evTxt(f.evidence), action: f.suggested_action,
    expected_impact: "Jika action diambil, CPL dijangka stabil/turun dlm 2-5 hari (anggaran, bukan jaminan).",
  }));
  const codeOf = (f) => (f.entity.startsWith("Akaun") ? "O" : f.issue.includes("PAUSED") ? "H" : f.level === "HIGH" ? "R" : "M");
  const checklist = flags.slice(0, 10).map((f) => ({
    action: f.suggested_action, entity: f.entity.slice(0, 40), reason: f.issue, code: codeOf(f),
    status: f.level === "HIGH" ? "PENDING - perlu approval" : "PENDING - pantau",
  }));
  for (const x of campRows)
    if (x.action_code === "S" && checklist.length < 12)
      checklist.push({ action: x.action, entity: x.campaign.slice(0, 40), reason: `CPL 7D RM${x.cpl["7D"]} (GREEN).`, code: "S", status: "PENDING - perlu approval" });
  const sec8 = { items, purpose: "Diagnosis + cadangan tindakan dijana automatik setiap pagi. Tiada perubahan automatik di Meta - semua tindakan perlu approval." };
  const sec9 = {
    codes: { M: "Monitor", S: "Scale", R: "Review/Optimize", H: "Hold/Pause-watch", O: "Owner confirm needed", C: "Consider kill/archive" },
    checklist, purpose: "Senarai tindakan untuk ditanda bila selesai.",
  };

  // ---------- Section 10 ----------
  const lm = metrics.last_month, tm = metrics.this_month;
  const dim = new Date(Date.UTC(Y.getUTCFullYear(), Y.getUTCMonth() + 1, 0)).getUTCDate();
  const elapsed = Math.round((Y - mStart) / DAY) + 1;
  const projLeads = Math.round((tm.leads / elapsed) * dim);
  const projSpend = r2(((tm.spend || 0) / elapsed) * dim);
  const dAbs = tm.cpl != null && lm.cpl != null ? r2(tm.cpl - lm.cpl) : null;
  const sec10 = {
    metrics: {
      last_month_full: { cpl: lm.cpl, whatsform_leads: lm.leads, spend_whatsform_campaigns: lm.spend },
      this_month_MTD: { cpl: tm.cpl, whatsform_leads: tm.leads, spend_whatsform_campaigns: tm.spend },
      this_month_projected_full: { whatsform_leads_proj: projLeads, spend_total_proj: projSpend, cpl_proj: tm.cpl },
    },
    delta: {
      cpl_abs: dAbs, cpl_pct: dAbs != null ? r2(pct(tm.cpl, lm.cpl)) : null,
      verdict: dAbs == null ? "⚪ Tiada data" : dAbs <= 0 ? "🟢 CPL turun/membaik" : "🔴 CPL naik/memburuk",
      context: `CPL MTD (${elapsed} hari) RM${tm.cpl} vs bulan lepas penuh RM${lm.cpl}. Unjuran bulan ni: ~${projLeads} leads, spend ~RM${projSpend}.`,
      recommendation: elapsed < 10 ? "Pantau trend beberapa hari lagi sebelum buat keputusan besar."
        : (dAbs || 0) > 0 ? "CPL bulan ni lebih tinggi - semak campaign RED di Section 2/3." : "CPL bulan ni lebih baik - kekalkan struktur, pertimbang scale yang GREEN.",
    },
    purpose: "Banding CPL bulan ini (MTD) vs bulan lepas penuh + unjuran akhir bulan.",
  };

  // ---------- _meta ----------
  const notes = [];
  if (!activeLead.length) notes.push("PERHATIAN: Tiada campaign lead-gen ACTIVE dalam akaun ni pada masa data ditarik.");
  const newRed = flags.filter((f) => f.issue.startsWith("BARU") && f.level === "HIGH").map((f) => f.entity);
  if (newRed.length) notes.push("RED flag BARU: " + newRed.slice(0, 3).join("; ") + ".");
  if (statusChanges.length) notes.push("Perubahan status: " + statusChanges.slice(0, 3).map((s) => `${s.entity} ${s.from}->${s.to}`).join("; ") + ".");
  notes.push("Data terus dari Meta Marketing API (auto setiap pagi). Lead = WhatsFormSubmit + Website leads (chat tidak dikira). AWARENESS dikecualikan dari CPL.");

  const generatedAt = new Date(now.getTime() + 8 * 3600000).toISOString().slice(0, 19) + "+08:00";
  const m = {
    dashboard: "Minda Optima — Pantas Baca Daily Monitoring (Minda Optima 2)", account_id: acc.replace("act_", ""),
    account_name: info.name, business_name: (info.business || {}).name || "", product: "Pantas Baca", currency: info.currency,
    tracking: "WhatsFormSubmit, Website leads", generated_at: generatedAt,
    data_source: `Meta Marketing API ${env.META_API_VERSION || "v23.0"} (Cloudflare Worker cron) - time_range tetap, zon Asia/Kuala_Lumpur`,
    date_windows: Object.fromEntries(Object.entries(ranges).map(([k, [a, b]]) => [k, iso(a) === iso(b) ? iso(a) : `${iso(a)}..${iso(b)}`])),
    IMPORTANT_NOTES: notes,
  };
  return {
    data: {
      _meta: { dashboard: "Minda Optima — Pantas Baca Daily Monitoring", generated_at: generatedAt, accounts_order: ["mo2"] },
      accounts: {
        mo2: {
          _meta: m, section_1_budget_card: sec1, section_2_red_flags: sec2, section_3_account_overview: sec3,
          section_4_performance_trend: sec4,
          section_5_campaign_summary: { campaigns: campRows, purpose: "Ringkasan performance per-campaign (excl. AWARENESS)." },
          section_6_adset_summary: {
            adsets: adsetRows, purpose: "Ringkasan prestasi adset ACTIVE + adset yang ada spend 14D (excl. AWARENESS) - window 3D/7D/14D.",
            note: "Traffic light: OLD (>=14 hari) ikut CPL 7D (fallback 14D); NEW ikut CPL kalau ada lead, kalau tiada ikut spend.",
          },
          section_7_ads_performance: { ads_14D: ads14, ads_7D_top: ads7, purpose: "Ad dgn spend >= RM20 (14D) dan top 40 spender (7D)." },
          section_8_diagnostic_recommendation: sec8, section_9_action_checklist: sec9, section_10_historical_comparison: sec10,
        },
      },
    },
    stats: { meta_calls: meta.calls(), campaigns: campRows.length, adsets: adsetRows.length, ads_14D: ads14.length, flags: flags.length },
  };
}

// ---------------- Data harian (untuk pemilih tarikh macam Ads Manager) ----------------
// Simpan baris harian setiap ad: [tarikh, ad_id, spend, impressions, link_click, whatsform, website_lead]
// Run pertama tarik 90 hari; run seterusnya tarik semula 28 hari terakhir (Meta kemas kini atribusi sehingga 28 hari)
// dan gabung dengan sejarah sedia ada (simpan maksimum 400 hari).
export async function buildDaily(env, prevDaily) {
  const meta = metaClient(env);
  let acc = env.META_AD_ACCOUNT_ID || "";
  if (!acc.startsWith("act_")) acc = "act_" + acc;
  const today = mytToday();
  const Y = addDays(today, -1);
  const hasPrev = prevDaily && Array.isArray(prevDaily.rows) && prevDaily.rows.length;
  const since = addDays(Y, hasPrev ? -27 : -89);
  const [campList, adsetList, adList, rows] = await Promise.all([
    meta.all(`${acc}/campaigns`, { fields: "id,name,effective_status,objective,created_time", limit: "200" }),
    meta.all(`${acc}/adsets`, { fields: "id,name,campaign_id,effective_status,daily_budget,created_time", limit: "500" }),
    meta.all(`${acc}/ads`, { fields: "id,name,adset_id,campaign_id,effective_status,created_time", limit: "500" }),
    meta.all(`${acc}/insights`, {
      level: "ad", time_increment: "1", time_range: JSON.stringify({ since: iso(since), until: iso(Y) }),
      fields: "ad_id,spend,impressions,inline_link_clicks,actions", limit: "500",
    }),
  ]);
  const fresh = rows.map((r) => {
    const s = stat(r);
    return [r.date_start, r.ad_id, r2(s.spend), s.impressions, s.link_click, s.form, s.web];
  }).filter((r) => r[2] > 0 || r[3] > 0 || r[5] > 0 || r[6] > 0);
  const cutoff = iso(addDays(Y, -399));
  const keep = hasPrev ? prevDaily.rows.filter((r) => r[0] < iso(since) && r[0] >= cutoff) : [];
  const all = [...keep, ...fresh].sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));

  // metadata entiti: gabung dgn lama supaya ad/campaign yang dah dipadam masih ada nama
  const pm = (hasPrev && prevDaily) || {};
  const campaigns = { ...(pm.campaigns || {}) }, adsets = { ...(pm.adsets || {}) }, ads = { ...(pm.ads || {}) };
  for (const c of campList) campaigns[c.id] = { n: c.name, st: c.effective_status, ct: (c.created_time || "").slice(0, 10), aw: isAwareness(c.name, c.objective) ? 1 : 0 };
  for (const a of adsetList) adsets[a.id] = { n: a.name, c: a.campaign_id, st: a.effective_status, b: a.daily_budget ? r2(Number(a.daily_budget) / 100) : null, ct: (a.created_time || "").slice(0, 10) };
  for (const a of adList) ads[a.id] = { n: a.name, s: a.adset_id, c: a.campaign_id, st: a.effective_status, ct: (a.created_time || "").slice(0, 10) };
  const generatedAt = new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 19) + "+08:00";
  return {
    generated_at: generatedAt,
    since: all.length ? all[0][0] : iso(since), until: iso(Y),
    columns: ["date", "ad_id", "spend", "impressions", "link_click", "whatsform", "website_lead"],
    note: "Baris harian setiap ad. Lead = whatsform + website_lead (chat tidak dikira). Kempen aw=1 ialah AWARENESS.",
    campaigns, adsets, ads, rows: all,
    stats: { meta_calls: meta.calls(), rows: all.length, refreshed_from: iso(since) },
  };
}
