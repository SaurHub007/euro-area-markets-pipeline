"""Run the Euro Area Markets pipeline end to end.

    python run_pipeline.py              # live pull from the ECB Data Portal
    python run_pipeline.py --offline    # rebuild from the committed snapshot
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from euro_markets import extract, load, quality, transform  # noqa: E402

RAW_SNAPSHOT = ROOT / "data" / "raw" / "ecb_monthly_snapshot.csv"
OUT_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "euro_markets.db"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="use data/raw snapshot instead of the API")
    parser.add_argument("--start", default="2015-01-01", help="first period to download (live mode)")
    parser.add_argument("--strict", action="store_true", help="exit non-zero if any DQ check fails")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    log = logging.getLogger("pipeline")

    # 1. Extract
    if args.offline:
        log.info("Extract: offline snapshot %s", RAW_SNAPSHOT.name)
        raw = extract.load_snapshot(RAW_SNAPSHOT)
    else:
        log.info("Extract: ECB Data Portal API")
        raw = extract.extract_all(args.start)

    # 2. Transform
    wide = transform.to_monthly(raw)
    if not args.offline:  # refresh the snapshot so the offline mode stays current
        wide.reset_index().assign(month=lambda d: d["month_start"].dt.strftime("%Y-%m")) \
            .drop(columns="month_start").set_index("month").reset_index() \
            .to_csv(RAW_SNAPSHOT, index=False)

    # 3. Quality gate
    issues = quality.run_checks(wide)
    if issues and args.strict:
        log.error("Stopping: %d data-quality issue(s)", len(issues))
        return 1

    wide = transform.add_derived(wide)
    dim_series = transform.build_dim_series()
    fact = transform.build_fact(wide)
    tables = {
        "fact_market_monthly": fact,
        "dim_date": transform.build_dim_date(wide),
        "dim_series": dim_series,
        "kpi_latest": transform.build_kpi_latest(fact, dim_series),
    }

    # 4. Load
    load.write_outputs(tables, OUT_DIR, DB_PATH)
    log.info("Done. %d series, %d fact rows, months %s -> %s",
             fact["series_id"].nunique(), len(fact), wide.index.min().date(), wide.index.max().date())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
