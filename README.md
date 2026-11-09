# Euro Area Markets Pipeline + Power BI

An end-to-end data pipeline that pulls **euro-area rates, sovereign yields, FX, equity and inflation data** from the **ECB Data Portal API**, validates it, models it as a **star schema**, and feeds a **Power BI dashboard** that refreshes automatically.

**Skills shown:** Python (pandas, NumPy) · SQL · Power BI (DAX, Power Query) · statistics (lead-lag correlation, OLS regression, z-scores) · ETL & data-quality checks · GitHub Actions automation · interactive Chart.js dashboard

### 🔴 Live dashboard: **[saurhub007.github.io/euro-area-markets-pipeline](https://saurhub007.github.io/euro-area-markets-pipeline/)**
Click through 4 pages, change the period slicer and hover any chart. It reads the latest pipeline output from this repo, so it updates every time the monthly refresh runs.

### Dashboard walkthrough
![Dashboard walkthrough](docs/images/dashboard_walkthrough.gif)

▶ **[Full HD video (MP4, 87 s)](docs/dashboard_walkthrough.mp4)**: KPI cards, period slicer, rates & yield curve, sovereign spreads, FX & equity.
*The walkthrough shows an HTML replica of the report built on the same star schema and measures as the Power BI model in [`powerbi/`](powerbi).*

![KPI cards](docs/images/kpi_cards.png)
![Dashboard preview](docs/images/dashboard_preview.png)

---

## Why this project
Frankfurt is home to the ECB, Deutsche Börse and Germany's biggest banks. Rates desks, treasury, risk and MIS teams there track the same handful of numbers every day: the ECB policy rate, €STR / Euribor, Bund yields, periphery spreads, the curve slope and EUR FX. This project automates that daily market monitor, from raw API data to a decision-ready dashboard.

## Architecture
```
ECB Data Portal API (SDMX REST, 14 series)
        │  extract.py   – retry logic, one request per series
        ▼
Raw daily / monthly observations
        │  transform.py – monthly roll-up (mean / month-end), derived spreads
        │  quality.py   – range checks, staleness checks, duplicate checks
        ▼
Star schema ──► data/processed/*.csv  ──► Power BI (Power Query from GitHub raw URLs)
            └─► data/euro_markets.db  ──► SQL analysis (sql/analysis_queries.sql)

GitHub Actions (monthly cron, 10th) re-runs the pipeline, commits fresh data
and posts a monthly report (reports/YYYY-MM.md) as a GitHub issue
```

## Data covered (Jan 2015 → latest)
| Category | Series |
|---|---|
| Policy & money market | ECB Deposit Facility Rate, €STR, Euribor 3M |
| Sovereign yields | Germany, France, Italy, Spain 10Y |
| Yield curve | Euro AAA curve 2Y & 10Y |
| FX | EUR/USD, EUR/GBP, EUR/INR |
| Equity | EURO STOXX 50 |
| Inflation | HICP headline YoY |
| **Derived** | 2s10s slope, BTP-Bund / OAT-Bund / Bono-Bund spreads (bps), real deposit rate |

## Data model
```
dim_date (date_key, month_start, year, quarter, month_name …)
     1
     │
     * 
fact_market_monthly (date_key, series_id, value, mom_change, yoy_change, mom_pct, yoy_pct)
     *
     │
     1
dim_series (series_id, series_name, category, unit, ecb_key, is_derived)
```
`kpi_latest.csv` holds the latest reading per series for KPI cards.

## Key insights from the data
- **Hiking cycle:** the ECB moved the deposit rate from **-0.50% to 4.00%** between Jul 2022 and Sep 2023, its fastest tightening on record, then cut back to 2.00% by mid-2025.
- **2026 re-tightening:** after a year on hold at 2.00%, the energy-price shock pushed the ECB to hike again, to **2.25% (Jun 2026)** and **2.50% (Sep 2026)**, then hold in Oct 2026.
- **Curve inversion:** the AAA 2s10s slope was **inverted from late 2022 to mid-2024** (low around **-54 bps**), a classic late-cycle signal.
- **Periphery risk:** the BTP-Bund spread peaked at **~308 bps (Nov 2018)** during the Italian budget standoff and has since compressed to **~80 bps**. By Sep 2026 the **OAT-Bund spread (~97 bps) is above BTP-Bund (~89 bps)**, showing how much French risk has been repriced.
- **Real rates:** the real deposit rate (DFR − HICP) was negative in **106 of 132 months** since 2015.
- **Equities:** EURO STOXX 50 roughly **doubled** from its 2020 Covid low to above 6,000 in 2026.

## Statistical analysis
[`stats_analysis.py`](stats_analysis.py) answers three questions a rates / risk desk would ask, and re-runs every month. Full, auto-updated results: [`reports/stats_summary.md`](reports/stats_summary.md).

- **Inflation leads policy:** 12-month changes in HICP inflation line up best with the deposit rate **~15 months later** (r ≈ 0.88, vs ≈ -0.2 with no lag): the ECB reacts with a long delay.
- **Bund drivers:** an OLS of the 10Y Bund on the deposit rate and inflation gives **R² ≈ 0.82**; each 1 pp of policy rate goes with ~65 bps on the 10Y yield.
- **Spread risk:** the OAT-Bund spread is at a **z-score of ~+2.9** (highest since 2015), while BTP-Bund and Bono-Bund sit below their long-run average.

![Lead-lag](docs/images/stats_leadlag.png)
![Spread z-scores](docs/images/stats_spreads.png)

## Run it
```bash
git clone https://github.com/SaurHub007/euro-area-markets-pipeline.git
cd euro-area-markets-pipeline
pip install -r requirements.txt

python run_pipeline.py            # live pull from the ECB API
python run_pipeline.py --offline  # rebuild from the committed snapshot (no internet)
python make_charts.py             # regenerate README images
python stats_analysis.py          # lead-lag, regression, spread z-scores
pytest -q                         # unit tests
sqlite3 data/euro_markets.db < sql/analysis_queries.sql
```

## Power BI
Everything needed to build the report is in [`powerbi/`](powerbi):
- `power_query.m` – M queries that load the CSVs straight from this repo (so refresh works in Power BI Service)
- `measures.dax` – 25+ measures: latest value, MoM / YoY, 3M average, YTD return, `Curve Status`, `Policy Stance`, conditional-format colours
- `euro_markets_theme.json` – report theme
- `DASHBOARD_GUIDE.md` – page-by-page layout (Executive Overview, Rates & Curve, Sovereign Spreads, FX & Equity)

## Project structure
```
├── run_pipeline.py          # orchestrator (extract → transform → DQ → load)
├── make_charts.py           # dashboard preview images
├── src/euro_markets/
│   ├── config.py            # series catalogue (ECB keys, units, aggregation rule)
│   ├── extract.py           # ECB API client
│   ├── transform.py         # monthly roll-up, spreads, star schema
│   ├── quality.py           # data-quality checks
│   └── load.py              # CSV + SQLite writer
├── data/raw/                # monthly snapshot (enables offline runs)
├── data/processed/          # fact & dimension tables for Power BI
├── sql/analysis_queries.sql # CTEs, window functions, rankings
├── powerbi/                 # M, DAX, theme, build guide
├── tests/                   # pytest unit tests
└── .github/workflows/       # scheduled refresh
```

## Notes
- Source: [ECB Data Portal](https://data.ecb.europa.eu/) – free, no API key.
- HICP headline: the ECB discontinued its old `ICP` dataset in Feb 2026 (last value Dec 2025). The pipeline now reads the new `HICP` dataset and splices the old series in for earlier history (`fallback_keys` in `config.py`).
- The current month is dropped by default because it is still incomplete (use `--include-current-month` to keep it). The refresh runs on the 10th so last month's bond yields are already published.
- Rates are monthly averages; the ECB deposit rate uses the month-end level.

## Tech stack
| Tool / library | Used for | Where |
|---|---|---|
| **pandas** | cleaning, daily → monthly roll-up, pivot/melt, spreads, MoM / YoY changes | `transform.py`, `extract.py` |
| **requests** | calling the ECB Data Portal REST API with retries | `extract.py` |
| **sqlite3** (standard library) | loading the star schema into a SQL database | `load.py` |
| **matplotlib** | README charts and KPI cards | `make_charts.py` |
| **pytest** | unit tests for aggregation, spreads and quality checks | `tests/` |
| **SQL** (SQLite) | CTEs, window functions (`ROW_NUMBER`, rolling averages) | `sql/analysis_queries.sql` |
| **Power BI** | Power Query M, 25+ DAX measures, star-schema model | `powerbi/` |
| **Chart.js** (JavaScript) | interactive web dashboard on GitHub Pages | `docs/index.html` |
| **GitHub Actions** | monthly scheduled refresh + tests | `.github/workflows/` |

---
**Author:** Saurabh Khamkar – Data Analyst, capital markets · [GitHub](https://github.com/SaurHub007)
