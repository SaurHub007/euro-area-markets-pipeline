"""Data-quality checks run before anything is loaded."""
from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)

# Plausible ranges - anything outside is flagged as a probable data error
BOUNDS = {
    "dfr": (-1, 10), "estr": (-1, 10), "euribor3m": (-1, 10),
    "de10y": (-2, 15), "fr10y": (-2, 15), "it10y": (-2, 15), "es10y": (-2, 15),
    "yc2y": (-2, 15), "yc10y": (-2, 15),
    "eurusd": (0.5, 2.0), "eurgbp": (0.5, 1.2), "eurinr": (40, 200),
    "sx5e": (1000, 10000), "hicp": (-5, 20),
}


def run_checks(wide: pd.DataFrame, max_stale_months: int = 3) -> list[str]:
    """Return a list of issues (empty list = all good)."""
    issues: list[str] = []

    if wide.index.duplicated().any():
        issues.append("duplicate months in monthly table")

    for sid, (lo, hi) in BOUNDS.items():
        if sid not in wide:
            issues.append(f"{sid}: missing entirely")
            continue
        s = wide[sid].dropna()
        bad = s[(s < lo) | (s > hi)]
        if not bad.empty:
            issues.append(f"{sid}: {len(bad)} value(s) outside [{lo}, {hi}]")
        last = s.index.max()
        lag = (wide.index.max().year - last.year) * 12 + wide.index.max().month - last.month
        if lag > max_stale_months:
            issues.append(f"{sid}: stale - last observation {last:%Y-%m} ({lag} months behind)")

    for msg in issues:
        log.warning("DQ: %s", msg)
    if not issues:
        log.info("DQ: all checks passed")
    return issues
