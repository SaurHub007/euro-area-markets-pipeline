"""Render dashboard preview images for the README (docs/images/*.png)."""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

fact = pd.read_csv(ROOT / "data/processed/fact_market_monthly.csv")
fact["date"] = pd.to_datetime(fact["date_key"].astype(str))
wide = fact.pivot(index="date", columns="series_id", values="value")

BLUE, GOLD, GREEN, RED, PURPLE = "#003299", "#FFB400", "#1B7F5A", "#C0392B", "#5C6BC0"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.titleweight": "bold",
                     "axes.titlecolor": BLUE})


def fmt(ax):
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


fig, axes = plt.subplots(2, 2, figsize=(13, 7.5))
fig.suptitle("Euro Area Markets Dashboard  |  ECB Data Portal, 2015 – 2026",
             fontsize=14, fontweight="bold", color=BLUE, x=0.01, ha="left")

ax = axes[0, 0]
ax.step(wide.index, wide["dfr"], where="post", color=BLUE, lw=2, label="ECB Deposit Rate")
ax.plot(wide.index, wide["euribor3m"], color=GOLD, lw=1.4, label="Euribor 3M")
ax.plot(wide.index, wide["hicp"], color=RED, lw=1.4, ls="--", label="HICP inflation YoY")
ax.set_title("Policy rate vs inflation (%)"); ax.legend(frameon=False); fmt(ax)

ax = axes[0, 1]
s = wide["spread_2s10s"].dropna()
ax.fill_between(s.index, s, 0, where=s >= 0, color=GREEN, alpha=0.35, label="Normal")
ax.fill_between(s.index, s, 0, where=s < 0, color=RED, alpha=0.5, label="Inverted")
ax.plot(s.index, s, color="#374151", lw=1)
ax.axhline(0, color="#374151", lw=0.8)
ax.set_title("AAA yield curve slope 2s10s (bps)"); ax.legend(frameon=False); fmt(ax)

ax = axes[1, 0]
for sid, c, lab in [("spread_btp_bund", RED, "Italy – Germany"),
                    ("spread_bono_bund", GOLD, "Spain – Germany"),
                    ("spread_oat_bund", BLUE, "France – Germany")]:
    ax.plot(wide.index, wide[sid], color=c, lw=1.6, label=lab)
ax.set_title("10Y sovereign spreads vs Bund (bps)"); ax.legend(frameon=False); fmt(ax)

ax = axes[1, 1]
ax.plot(wide.index, wide["sx5e"], color=BLUE, lw=1.8, label="EURO STOXX 50")
ax.set_ylabel("Index", color=BLUE)
ax2 = ax.twinx()
ax2.plot(wide.index, wide["eurusd"], color=GOLD, lw=1.4, label="EUR/USD")
ax2.set_ylabel("EUR/USD", color=GOLD); ax2.grid(False); ax2.spines["top"].set_visible(False)
ax.set_title("Equity & FX"); fmt(ax)
lines = ax.get_lines() + ax2.get_lines()
ax.legend(lines, [l.get_label() for l in lines], frameon=False, loc="upper left")

fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(OUT / "dashboard_preview.png", dpi=130)

# KPI strip
kpi = pd.read_csv(ROOT / "data/processed/kpi_latest.csv").set_index("series_id")
cards = [("dfr", "ECB Deposit Rate", "{:.2f}%"), ("estr", "€STR", "{:.2f}%"),
         ("de10y", "Bund 10Y", "{:.2f}%"), ("spread_btp_bund", "BTP-Bund", "{:.0f} bps"),
         ("eurusd", "EUR/USD", "{:.3f}"), ("sx5e", "EURO STOXX 50", "{:,.0f}")]
fig, axes = plt.subplots(1, len(cards), figsize=(13, 1.7))
for ax, (sid, label, f) in zip(axes, cards):
    r = kpi.loc[sid]
    chg = r["mom_change"]
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0.02, 0.05), 0.96, 0.9, transform=ax.transAxes,
                               fc="#F3F6FC", ec="#D6DEEF", lw=1))
    ax.text(0.5, 0.75, label, ha="center", fontsize=10, color="#4B5563", transform=ax.transAxes)
    ax.text(0.5, 0.42, f.format(r["value"]), ha="center", fontsize=17, fontweight="bold",
            color=BLUE, transform=ax.transAxes)
    as_of = pd.to_datetime(str(int(r["date_key"]))).strftime("%b %Y")
    ax.text(0.5, 0.15, f"{'▲' if chg >= 0 else '▼'} {chg:+.3g} MoM · {as_of}", ha="center", fontsize=8.5,
            color=GREEN if chg >= 0 else RED, transform=ax.transAxes)
fig.tight_layout()
fig.savefig(OUT / "kpi_cards.png", dpi=130)
print("charts written to", OUT)
