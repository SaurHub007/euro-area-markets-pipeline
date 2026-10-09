# Power BI Dashboard – Build Guide

Rebuild the report in ~30 minutes from the files in this folder.

## 1. Load data
1. Power BI Desktop → **Transform data** → **Manage Parameters** → new parameter `BaseUrl` (Text):
   `https://raw.githubusercontent.com/SaurHub007/euro-area-markets-pipeline/main/data/processed/`
2. **New Source → Blank Query → Advanced Editor**, paste each query from `power_query.m`
   (`fact_market_monthly`, `dim_date`, `dim_series`). Close & Apply.
   *(Offline alternative: Get Data → Text/CSV → `data/processed/*.csv`.)*

## 2. Model (star schema)
| From | To | Cardinality |
|---|---|---|
| `fact_market_monthly[date_key]` | `dim_date[date_key]` | Many → One |
| `fact_market_monthly[series_id]` | `dim_series[series_id]` | Many → One |

- Mark `dim_date` as date table on `month_start`.
- Sort `dim_date[month_name]` by `month_num`.
- Create an empty table `_Measures` and paste measures from `measures.dax`.
- View → Themes → Browse → `euro_markets_theme.json`.

## 3. Report pages

### Page 1 – Executive Overview
- **KPI cards (row):** ECB Deposit Rate %, €STR %, Bund 10Y %, BTP-Bund Spread bps, EURUSD, EURO STOXX 50 – each with `MoM Change` as the subtitle and `KPI Colour` conditional formatting.
- **Line chart:** DFR vs €STR vs Euribor 3M vs HICP (filter `dim_series[series_id]`), X = `month_start`.
- **Card:** `Policy Stance`, `Curve Status`, `Last Refreshed`.
- **Slicer:** `dim_date[year]` (between).

### Page 2 – Rates & Yield Curve
- Line: Euro AAA 2Y vs 10Y; area chart: `2s10s Slope` with a 0 constant line (inversion shading).
- Column chart: `Months Real Rate Negative` by year; line: Real Deposit Rate.

### Page 3 – Sovereign Spreads
- Line: DE / FR / IT / ES 10Y yields.
- Line: BTP-Bund, OAT-Bund, Bono-Bund spreads (bps) – annotate 2018 Italian budget and 2022 hiking cycle.
- Table: series_name, Latest Value, MoM Change, YoY Change, Max/Min Since 2015.

### Page 4 – FX & Equity
- Line: EUR/USD with `Value 3M Avg`; small multiples for EUR/GBP, EUR/INR.
- Line: EURO STOXX 50 + `YTD Return %` card.

## 4. Publish & refresh
- Publish to Power BI Service; dataset credentials → *Anonymous* for `raw.githubusercontent.com`.
- Schedule refresh (daily). The GitHub Action in `.github/workflows/refresh.yml` re-runs the
  pipeline monthly and commits fresh CSVs, so the report stays current with zero manual work.
- Save the report as `powerbi/Euro_Area_Markets.pbix` and commit it.
