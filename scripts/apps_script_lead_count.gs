/**
 * Lead Count API — Minda Optima (Google Apps Script, Web App)
 * Kira lead SEBENAR dari Google Sheet "FORM LEADS" (tab "lead monitor") ikut tarikh, jam & keyword.
 * TIADA data peribadi (nama / no. telefon) keluar — hanya bilangan.
 *
 * Pasang: Buka Sheet "FORM LEADS" -> Extensions -> Apps Script -> paste fail ni (ganti semua)
 *         -> tukar CONFIG.KEY kepada perkataan rawak -> Deploy -> New deployment
 *         -> Web app, Execute as: Me, Who has access: Anyone -> salin URL Web app.
 * Uji:    <URL>?key=<KEY>   (mesti keluar JSON {"ok":true,...})
 */
const CONFIG = {
  KEY: 'TUKAR-KUNCI-RAHSIA-NI',          // tukar kepada perkataan rawak, bagi Claude sekali dengan URL
  TZ: 'Asia/Kuala_Lumpur',
  DAYS: 40,                               // berapa hari ke belakang
  SOURCES: [
    // Satu baris untuk setiap tab lead. Nama kolum mesti SAMA dengan baris tajuk (baris 1) dalam tab.
    { sheet: 'lead monitor', colTime: 'TIME', colKeyword: 'KEYWORD', colPhone: 'PHONE', source: 'form' },
  ],
  // Optional: kolum status sales (biar '' kalau tiada). Nilai yang dikira booking / enroll:
  COL_STATUS: '',
  BOOKING_WORDS: ['BOOKING', 'BOOKED', 'TRIAL'],
  ENROLL_WORDS: ['ENROLL', 'DAFTAR', 'PAID'],
};

function doGet(e) {
  if (!e || !e.parameter || e.parameter.key !== CONFIG.KEY) return out_({ ok: false, error: 'unauthorized' });
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const since = new Date(Date.now() - CONFIG.DAYS * 864e5);
  const agg = {};      // "date|hour|keyword|source" -> [total, unique, booking, enroll]
  const seen = {};     // "date|source|phone" -> true (buang duplicate dalam hari yang sama)
  const missing = [];

  CONFIG.SOURCES.forEach(function (src) {
    const sh = ss.getSheetByName(src.sheet);
    if (!sh) { missing.push('tab:' + src.sheet); return; }
    const data = sh.getDataRange().getValues();
    const head = data.shift().map(function (h) { return String(h).trim(); });
    const iT = head.indexOf(src.colTime), iK = head.indexOf(src.colKeyword), iP = head.indexOf(src.colPhone);
    const iS = CONFIG.COL_STATUS ? head.indexOf(CONFIG.COL_STATUS) : -1;
    if (iT < 0) { missing.push(src.sheet + ':' + src.colTime); return; }
    if (iK < 0) missing.push(src.sheet + ':' + src.colKeyword);

    data.forEach(function (r) {
      const t = r[iT] instanceof Date ? r[iT] : new Date(r[iT]);
      if (isNaN(t) || t < since) return;
      const d = Utilities.formatDate(t, CONFIG.TZ, 'yyyy-MM-dd');
      const h = Number(Utilities.formatDate(t, CONFIG.TZ, 'H'));
      const kw = iK >= 0 ? String(r[iK]).trim().toUpperCase().replace(/\s+/g, ' ') : '';
      const k = [d, h, kw, src.source].join('|');
      const a = agg[k] || (agg[k] = [0, 0, 0, 0]);
      a[0]++;
      const phone = iP >= 0 ? String(r[iP]).replace(/\D/g, '').replace(/^60/, '0') : '';
      const sk = d + '|' + src.source + '|' + phone;
      if (!phone || !seen[sk]) { a[1]++; if (phone) seen[sk] = true; }
      if (iS >= 0) {
        const st = String(r[iS]).toUpperCase();
        if (CONFIG.BOOKING_WORDS.some(function (w) { return st.indexOf(w) >= 0; })) a[2]++;
        if (CONFIG.ENROLL_WORDS.some(function (w) { return st.indexOf(w) >= 0; })) a[3]++;
      }
    });
  });

  const rows = Object.keys(agg).sort().map(function (k) {
    const p = k.split('|');
    return [p[0], Number(p[1]), p[2], p[3]].concat(agg[k]);
  });
  return out_({
    ok: true,
    generated_at: Utilities.formatDate(new Date(), CONFIG.TZ, "yyyy-MM-dd'T'HH:mm:ssXXX"),
    columns: ['date', 'hour', 'keyword', 'source', 'total', 'unique', 'booking', 'enroll'],
    rows: rows,
    missing: missing,
  });
}

function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
