"""Transform: clean, resample to monthly, derive spreads and build a star schema."""
from __future__ import annotations

import pandas as pd

from .config import DERIVED, SERIES


def to_monthly(raw: pd.DataFrame) -> pd.DataFrame:
    """Roll daily/business-day observations up to calendar months.

    Returns a wide frame indexed by month_start with one column per series.
    """
    df = raw.copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["month_start"] = pd.to_datetime(df["period"].astype(str).str[:7] + "-01")

    parts = []
    for sid, grp in df.groupby("series_id"):
        agg = SERIES.get(sid, {}).get("aggregation", "mean")
        grp = grp.sort_values("period")
        monthly = grp.groupby("month_start")["value"].agg(agg).rename(sid)
        parts.append(monthly)
    wide = pd.concat(parts, axis=1).sort_index()
    wide.index.name = "month_start"
    return wide


def add_derived(wide: pd.DataFrame) -> pd.DataFrame:
    """Spreads in basis points and the real policy rate."""
    out = wide.copy()
    out["spread_2s10s"] = (out["yc10y"] - out["yc2y"]) * 100
    out["spread_btp_bund"] = (out["it10y"] - out["de10y"]) * 100
    out["spread_oat_bund"] = (out["fr10y"] - out["de10y"]) * 100
    out["spread_bono_bund"] = (out["es10y"] - out["de10y"]) * 100
    out["real_dfr"] = out["dfr"] - out["hicp"]
    return out.round(4)


def build_fact(wide: pd.DataFrame) -> pd.DataFrame:
    """Long fact table with month-on-month and year-on-year changes."""
    fact = wide.rename_axis("month_start").reset_index().melt(id_vars="month_start", var_name="series_id", value_name="value")
    fact = fact.dropna(subset=["value"]).sort_values(["series_id", "month_start"])

    g = fact.groupby("series_id")["value"]
    fact["mom_change"] = g.diff(1)
    fact["yoy_change"] = g.diff(12)
    # % changes only make sense for levels (FX, equity), not for rates
    level_series = {"eurusd", "eurgbp", "eurinr", "sx5e"}
    is_level = fact["series_id"].isin(level_series)
    fact["mom_pct"] = (g.pct_change(1, fill_method=None) * 100).where(is_level)
    fact["yoy_pct"] = (g.pct_change(12, fill_method=None) * 100).where(is_level)

    fact["date_key"] = fact["month_start"].dt.strftime("%Y%m%d").astype(int)
    cols = ["date_key", "series_id", "value", "mom_change", "yoy_change", "mom_pct", "yoy_pct"]
    return fact[cols].round(4).reset_index(drop=True)


def build_dim_date(wide: pd.DataFrame) -> pd.DataFrame:
    d = pd.DataFrame({"month_start": wide.index})
    d["date_key"] = d["month_start"].dt.strftime("%Y%m%d").astype(int)
    d["year"] = d["month_start"].dt.year
    d["quarter"] = "Q" + d["month_start"].dt.quarter.astype(str)
    d["month_num"] = d["month_start"].dt.month
    d["month_name"] = d["month_start"].dt.strftime("%b")
    d["year_month"] = d["month_start"].dt.strftime("%Y-%m")
    d["month_start"] = d["month_start"].dt.date
    return d[["date_key", "month_start", "year", "quarter", "month_num", "month_name", "year_month"]]


def build_dim_series() -> pd.DataFrame:
    rows = [
        {"series_id": k, "series_name": v["name"], "category": v["category"], "unit": v["unit"],
         "ecb_key": v["key"], "is_derived": False}
        for k, v in SERIES.items()
    ] + [
        {"series_id": k, "series_name": v["name"], "category": v["category"], "unit": v["unit"],
         "ecb_key": "derived", "is_derived": True}
        for k, v in DERIVED.items()
    ]
    return pd.DataFrame(rows)


def build_kpi_latest(fact: pd.DataFrame, dim_series: pd.DataFrame) -> pd.DataFrame:
    """Latest available reading per series - handy for KPI cards."""
    latest = fact.sort_values("date_key").groupby("series_id").tail(1)
    return latest.merge(dim_series[["series_id", "series_name", "category", "unit"]], on="series_id")
