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


def fetch_key(key: str, start: str = START_PERIOD, retries: int = 3) -> pd.DataFrame:
    """Download one ECB series key and return a frame: period, value."""
    url = f"{ECB_API}/{key}"
    params = {"format": "csvdata", "startPeriod": start, "detail": "dataonly"}

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            log.warning("%s attempt %d/%d failed: %s", key, attempt, retries, exc)
            if attempt == retries:
                raise
            time.sleep(2 * attempt)

    raw = pd.read_csv(io.StringIO(resp.text))
    return raw[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"TIME_PERIOD": "period", "OBS_VALUE": "value"})


def splice(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Combine the same series from several keys; earlier frames win on overlapping periods."""
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.dropna(subset=["value"]).drop_duplicates(subset="period", keep="first")
    return combined.sort_values("period").reset_index(drop=True)


def fetch_series(series_id: str, start: str = START_PERIOD, retries: int = 3) -> pd.DataFrame:
    """Download one series (primary key + any fallback keys) as: series_id, period, value."""
    meta = SERIES[series_id]
    keys = [meta["key"], *meta.get("fallback_keys", [])]
    frames = []
    for key in keys:
        try:
            frames.append(fetch_key(key, start, retries))
        except Exception as exc:  # noqa: BLE001 - try the next key
            log.warning("%s: key %s unavailable (%s)", series_id, key, exc)
    if not frames:
        raise RuntimeError(f"{series_id}: no key returned data")
    df = splice(frames)
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
