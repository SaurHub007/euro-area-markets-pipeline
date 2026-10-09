"""Load: write the star schema to CSV (for Power BI) and SQLite (for SQL analysis)."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


def write_outputs(tables: dict[str, pd.DataFrame], out_dir: Path, db_path: Path | None = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        path = out_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        log.info("wrote %-22s %6d rows", path.name, len(df))

    if db_path is not None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as con:
            for name, df in tables.items():
                df.to_sql(name, con, if_exists="replace", index=False)
        log.info("wrote SQLite database %s", db_path)
