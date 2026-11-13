# MO2 Monitor (Minda Optima 2)

Dashboard baru, berasingan dari Dashboard-MO-v3. Data terus dari Meta Marketing API.

- `index.html` baca `data.json` + `config.json` (fail statik, tiada token dalam pelayar).
- `scripts/build_dashboard_data.py` jana `data.json` (30 hari harian, kempen & ad 7 hari).
- Hasil = Lead + WhatsFormSubmit. Chat WhatsApp tidak dikira.
- Kemas kini manual: `python3 scripts/build_dashboard_data.py` kemudian commit `dashboard/data.json`.
- Kemas kini harian automatik: `.github/workflows/refresh-dashboard.yml`. Perlu GitHub Secrets
  `META_ACCESS_TOKEN` dan `META_AD_ACCOUNT_ID` (Settings > Secrets and variables > Actions).
- Buka melalui http(s) (GitHub Pages). Double-click fail tidak berfungsi kerana `fetch()`.
