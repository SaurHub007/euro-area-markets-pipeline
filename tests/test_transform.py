import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from euro_markets import quality, transform  # noqa: E402


@pytest.fixture
def raw_daily():
    rows = []
    for d, v in [("2024-01-02", 4.0), ("2024-01-31", 4.0), ("2024-02-15", 3.75), ("2024-02-29", 3.5)]:
        rows.append({"series_id": "dfr", "period": d, "value": v})  # aggregation = last
    for d, v in [("2024-01-02", 3.0), ("2024-01-31", 4.0), ("2024-02-15", 2.0), ("2024-02-29", 2.0)]:
        rows.append({"series_id": "estr", "period": d, "value": v})  # aggregation = mean
    return pd.DataFrame(rows)


def test_monthly_aggregation_rules(raw_daily):
    wide = transform.to_monthly(raw_daily)
    assert list(wide.index.strftime("%Y-%m")) == ["2024-01", "2024-02"]
    assert wide.loc["2024-02-01", "dfr"] == 3.5     # last observation
    assert wide.loc["2024-01-01", "estr"] == 3.5    # monthly mean


def test_spreads_in_bps():
    wide = pd.DataFrame(
        {"yc2y": [2.0], "yc10y": [2.5], "it10y": [3.8], "de10y": [2.6], "fr10y": [3.3],
         "es10y": [3.2], "dfr": [2.0], "hicp": [2.2]},
        index=pd.to_datetime(["2025-01-01"]),
    )
    out = transform.add_derived(wide)
    assert out["spread_2s10s"].iloc[0] == pytest.approx(50)
    assert out["spread_btp_bund"].iloc[0] == pytest.approx(120)
    assert out["real_dfr"].iloc[0] == pytest.approx(-0.2)


def test_fact_yoy_change():
    idx = pd.date_range("2023-01-01", periods=13, freq="MS")
    wide = pd.DataFrame({"eurusd": [1.0] * 12 + [1.1]}, index=idx)
    fact = transform.build_fact(wide)
    last = fact.iloc[-1]
    assert last["yoy_change"] == pytest.approx(0.1)
    assert last["yoy_pct"] == pytest.approx(10.0)


def test_quality_flags_out_of_range():
    idx = pd.date_range("2025-01-01", periods=2, freq="MS")
    wide = pd.DataFrame({"eurusd": [1.1, 9.9]}, index=idx)
    issues = quality.run_checks(wide)
    assert any("eurusd" in i and "outside" in i for i in issues)
