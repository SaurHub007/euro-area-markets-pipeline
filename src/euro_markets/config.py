"""Series catalogue for the Euro Area Markets pipeline.

Every series comes from the ECB Data Portal (SDMX REST API, no API key needed):
https://data.ecb.europa.eu/help/api/overview
"""

ECB_API = "https://data-api.ecb.europa.eu/service/data"
START_PERIOD = "2015-01-01"

# series_id -> metadata
#   key          : ECB "<dataflow>/<series key>"
#   aggregation  : how daily data is rolled up to a month ("mean" or "last")
SERIES = {
    # --- Policy & money-market rates -----------------------------------
    "dfr": {
        "name": "ECB Deposit Facility Rate",
        "category": "Policy Rates",
        "unit": "%",
        "key": "FM/D.U2.EUR.4F.KR.DFR.LEV",
        "aggregation": "last",
    },
    "estr": {
        "name": "€STR (Euro Short-Term Rate)",
        "category": "Money Market",
        "unit": "%",
        "key": "EST/B.EU000A2X2A25.WT",
        "aggregation": "mean",
    },
    "euribor3m": {
        "name": "Euribor 3M",
        "category": "Money Market",
        "unit": "%",
        "key": "FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA",
        "aggregation": "mean",
    },
    # --- Sovereign bond yields -----------------------------------------
    "de10y": {"name": "Germany 10Y Bund Yield", "category": "Sovereign Yields", "unit": "%",
              "key": "IRS/M.DE.L.L40.CI.0000.EUR.N.Z", "aggregation": "mean"},
    "fr10y": {"name": "France 10Y OAT Yield", "category": "Sovereign Yields", "unit": "%",
              "key": "IRS/M.FR.L.L40.CI.0000.EUR.N.Z", "aggregation": "mean"},
    "it10y": {"name": "Italy 10Y BTP Yield", "category": "Sovereign Yields", "unit": "%",
              "key": "IRS/M.IT.L.L40.CI.0000.EUR.N.Z", "aggregation": "mean"},
    "es10y": {"name": "Spain 10Y Bono Yield", "category": "Sovereign Yields", "unit": "%",
              "key": "IRS/M.ES.L.L40.CI.0000.EUR.N.Z", "aggregation": "mean"},
    # --- AAA euro-area yield curve -------------------------------------
    "yc2y": {"name": "Euro AAA Curve 2Y", "category": "Yield Curve", "unit": "%",
             "key": "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y", "aggregation": "mean"},
    "yc10y": {"name": "Euro AAA Curve 10Y", "category": "Yield Curve", "unit": "%",
              "key": "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y", "aggregation": "mean"},
    # --- FX --------------------------------------------------------------
    "eurusd": {"name": "EUR/USD", "category": "FX", "unit": "USD per EUR",
               "key": "EXR/M.USD.EUR.SP00.A", "aggregation": "mean"},
    "eurgbp": {"name": "EUR/GBP", "category": "FX", "unit": "GBP per EUR",
               "key": "EXR/M.GBP.EUR.SP00.A", "aggregation": "mean"},
    "eurinr": {"name": "EUR/INR", "category": "FX", "unit": "INR per EUR",
               "key": "EXR/M.INR.EUR.SP00.A", "aggregation": "mean"},
    # --- Equity & inflation ---------------------------------------------
    "sx5e": {"name": "EURO STOXX 50 Index", "category": "Equity", "unit": "Index points",
             "key": "FM/M.U2.EUR.DS.EI.DJES50I.HSTA", "aggregation": "mean"},
    "hicp": {"name": "HICP Inflation (YoY)", "category": "Inflation", "unit": "%",
             "key": "ICP/M.U2.N.000000.4.ANR", "aggregation": "mean"},
}

# Derived analytics series built in transform.py
DERIVED = {
    "spread_2s10s": {"name": "2s10s Curve Slope", "category": "Spreads", "unit": "bps"},
    "spread_btp_bund": {"name": "BTP-Bund Spread (IT-DE 10Y)", "category": "Spreads", "unit": "bps"},
    "spread_oat_bund": {"name": "OAT-Bund Spread (FR-DE 10Y)", "category": "Spreads", "unit": "bps"},
    "spread_bono_bund": {"name": "Bono-Bund Spread (ES-DE 10Y)", "category": "Spreads", "unit": "bps"},
    "real_dfr": {"name": "Real Deposit Rate (DFR - HICP)", "category": "Policy Rates", "unit": "%"},
}
