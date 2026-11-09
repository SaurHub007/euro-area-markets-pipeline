"""Statistical analysis on top of the monthly star schema.

    python stats_analysis.py     # writes reports/stats_summary.md + 2 charts in docs/images/

Three questions a rates / risk desk would ask:
  1. Lead-lag: how many months after inflation moves does the ECB move its rate?
  2. Drivers: how much of the Bund 10Y yield is explained by the policy rate and inflation?
  3. Risk: how stretched are the sovereign spreads versus their own history (z-score)?
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
IMAGES = ROOT / "docs" / "images"
SPREADS = {"spread_btp_bund": "BTP-Bund (Italy)", "spread_oat_bund": "OAT-Bund (France)",
           "spread_bono_bund": "Bono-Bund (Spain)"}


def load_wide() -> pd.DataFrame:
    fact = pd.read_csv(PROCESSED / "fact_market_monthly.csv")
    dates = pd.read_csv(PROCESSED / "dim_date.csv", parse_dates=["month_start"])
    fact = fact.merge(dates[["date_key", "month_start"]], on="date_key")
    return fact.pivot_table(index="month_start", columns="series_id", values="value").sort_index()


def lead_lag(leader: pd.Series, follower: pd.Series, max_lag: int = 24) -> pd.Series:
    """Correlation of 12-month changes: leader at t vs follower at t+lag."""
    a, b = leader.diff(12), follower.diff(12)
    return pd.Series({lag: a.corr(b.shift(-lag)) for lag in range(max_lag + 1)}, name="corr")


def ols(y: pd.Series, X: pd.DataFrame) -> tuple[pd.Series, float, int]:
    """Plain least squares with an intercept. Returns coefficients, R² and n."""
    data = pd.concat([y, X], axis=1).dropna()
    yv = data.iloc[:, 0].to_numpy()
    Xv = np.column_stack([np.ones(len(data)), data.iloc[:, 1:].to_numpy()])
    beta, *_ = np.linalg.lstsq(Xv, yv, rcond=None)
    resid = yv - Xv @ beta
    r2 = 1 - (resid @ resid) / ((yv - yv.mean()) @ (yv - yv.mean()))
    return pd.Series(beta, index=["intercept", *X.columns]), float(r2), len(data)


def zscore_latest(s: pd.Series) -> tuple[float, float, float, pd.Timestamp]:
    s = s.dropna()
    z = (s.iloc[-1] - s.mean()) / s.std()
    pct = (s <= s.iloc[-1]).mean() * 100
    return float(s.iloc[-1]), float(z), float(pct), s.index[-1]


def make_charts(ll: pd.Series, wide: pd.DataFrame) -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    best = int(ll.idxmax())

    fig, ax = plt.subplots(figsize=(8, 3.6))
    colors = ["#2b6cb0" if lag == best else "#a0aec0" for lag in ll.index]
    ax.bar(ll.index, ll.values, color=colors)
    ax.set_xlabel("Months after the inflation change")
    ax.set_ylabel("Correlation")
    ax.set_title(f"Inflation leads the ECB deposit rate – strongest at {best} months")
    ax.set_xticks(ll.index)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMAGES / "stats_leadlag.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.6))
    for sid, label in SPREADS.items():
        s = wide[sid].dropna()
        ax.plot(s.index, (s - s.mean()) / s.std(), label=label, linewidth=1.6)
    ax.axhline(0, color="#718096", linewidth=0.8)
    for lvl in (-2, 2):
        ax.axhline(lvl, color="#e53e3e", linewidth=0.8, linestyle="--")
    ax.set_ylabel("z-score vs 2015+ history")
    ax.set_title("Sovereign spreads vs their own history")
    ax.legend(frameon=False, ncol=3, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMAGES / "stats_spreads.png", dpi=150)
    plt.close(fig)


def build_summary(wide: pd.DataFrame) -> str:
    ll = lead_lag(wide["hicp"], wide["dfr"])
    best = int(ll.idxmax())
    beta, r2, n = ols(wide["de10y"], wide[["dfr", "hicp"]])
    make_charts(ll, wide)

    lines = [
        f"# Statistical analysis – data to {wide.index.max():%b %Y}",
        "",
        "## 1. Does inflation lead ECB policy?",
        f"Correlation of 12-month changes in HICP inflation vs the deposit rate, shifted forward 0–24 months. "
        f"The link is strongest when the rate is taken **{best} months later** (r = {ll[best]:.2f}, "
        f"vs r = {ll[0]:.2f} with no lag): the ECB reacts to inflation with a delay.",
        "",
        "![Lead-lag](../docs/images/stats_leadlag.png)",
        "",
        "## 2. What drives the Bund 10Y yield?",
        f"OLS on {n} monthly observations: `Bund 10Y = {beta['intercept']:.2f} + {beta['dfr']:.2f} × DFR "
        f"+ {beta['hicp']:.2f} × HICP`, **R² = {r2:.2f}**. "
        f"Each 1 pp on the deposit rate goes with about {beta['dfr'] * 100:.0f} bps on the 10Y Bund; "
        f"policy rate and inflation together explain {r2:.0%} of the variation in the yield.",
        "",
        "## 3. How stretched are sovereign spreads?",
        "| Spread | Latest | Value (bps) | z-score | Percentile since 2015 |",
        "|---|---|---|---|---|",
    ]
    for sid, label in SPREADS.items():
        val, z, pct, last = zscore_latest(wide[sid])
        flag = " ⚠️" if abs(z) >= 2 else ""
        lines.append(f"| {label} | {last:%b %Y} | {val:.0f} | {z:+.2f}{flag} | {pct:.0f}% |")
    lines += [
        "",
        "![Spread z-scores](../docs/images/stats_spreads.png)",
        "",
        "_Method notes: monthly data from the ECB Data Portal; correlations use 12-month changes to remove "
        "level trends; z-scores use the full 2015+ history. Correlation is not causation._",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    wide = load_wide()
    REPORTS.mkdir(exist_ok=True)
    text = build_summary(wide)
    (REPORTS / "stats_summary.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
