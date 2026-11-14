# Dashboard MO2 (Minda Optima 2 — Pantas Baca Daily Monitoring)

Salinan Dashboard-MO-v3 (10 seksyen + Gabungan), khusus Minda Optima 2, data terus dari Meta Marketing API.
Dashboard lama tidak disentuh: remark & checklist disimpan berasingan (tidak sync ke Firebase dashboard lama).

- `index.html` — dashboard (baca `data.json`).
- `data.json` — dijana oleh `scripts/build_dashboard_data.py`.
- Lead = WhatsFormSubmit + Website leads. Chat WhatsApp tidak dikira. AWARENESS dikecualikan dari CPL.
- Kemas kini automatik setiap hari 8:23 pagi (MYT) oleh `.github/workflows/refresh-dashboard.yml`
  (perlu GitHub Secrets `META_ACCESS_TOKEN` dan `META_AD_ACCOUNT_ID`).
- Kemas kini manual: Actions → Refresh MO2 dashboard data → Run workflow.
