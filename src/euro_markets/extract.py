"""Extract: pull raw observations from the ECB Data Portal API."""
from __future__ import annotations

import io
import logging
import time
from pathlib import Path

import pandas as pd
import requests

from .config import ECB_API, SERIES, START_PERIOD

log = logging.getLogger(__name__)


def fetch_series(series_id: str, start: str = START_PERIOD, retries: int = 3) -> pd.DataFrame:
    """Download one ECB series and return a long frame: series_id, period, value."""
    key = SERIES[series_id]["key"]
    url = f"{ECB_API}/{key}"
    params = {"format": "csvdata", "startPeriod": start, "detail": "dataonly"}

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            log.warning("%s attempt %d/%d failed: %s", series_id, attempt, retries, exc)
            if attempt == retries:
                raise
            time.sleep(2 * attempt)

    raw = pd.read_csv(io.StringIO(resp.text))
    df = raw[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"TIME_PERIOD": "period", "OBS_VALUE": "value"})
    df["series_id"] = series_id
    log.info("%-10s %5d rows  %s -> %s", series_id, len(df), df["period"].min(), df["period"].max())
    return df[["series_id", "period", "value"]]


def extract_all(start: str = START_PERIOD) -> pd.DataFrame:
    """Fetch every configured series (a failing series is logged and skipped)."""
    frames = []
    for sid in SERIES:
        try:
            frames.append(fetch_series(sid, start))
        except Exception as exc:  # noqa: BLE001 - keep the run alive
            log.error("Skipping %s: %s", sid, exc)
    return pd.concat(frames, ignore_index=True)


def load_snapshot(path: Path) -> pd.DataFrame:
    """Offline mode: read the committed monthly snapshot (wide) into long format."""
    wide = pd.read_csv(path)
    long = wide.melt(id_vars="month", var_name="series_id", value_name="value").dropna()
    return long.rename(columns={"month": "period"})[["series_id", "period", "value"]]
