import argparse
import glob
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from .utils import (
    detect_columns,
    parse_datetime,
    parse_minutes,
    extract_date,
    normalize_line_value,
    infer_area_from_path,
    infer_line_from_area,
    parse_source_type,
    load_personnel_config,
    is_personnel_intensive,
    ensure_directories,
    kw_from_date,
    configure_logging,
    deduplicate_records,
)
from .matrix_parser import normalize_matrix_file


def find_excel_files(input_roots: List[str], years: List[str], areas: List[str], max_files: int) -> List[str]:
    patterns: List[str] = []
    for root in input_roots:
        for y in years:
            for a in areas:
                # Fixed: search under data/<year>/<area>/
                patterns.append(os.path.join(root, "data", y, a, "*.xlsx"))
    files: List[str] = []
    for p in patterns:
        files.extend(glob.glob(p))
    # Fallback: recursive search under data/year dirs if nothing found
    if not files:
        for root in input_roots:
            for y in years:
                recursive_pattern = os.path.join(root, "data", y, "**", "*.xlsx")
                files.extend(glob.glob(recursive_pattern, recursive=True))
    files = sorted(files)[: max_files if max_files > 0 else None]
    return files


def normalize_file(path: str, personnel_terms: set, personnel_aliases: dict, logger) -> pd.DataFrame:
    try:
        # default first sheet
        df = pd.read_excel(path)
    except Exception as e:
        logger.warning(f"Failed to read file {path}: {e}")
        return pd.DataFrame()

    columns = detect_columns(df)
    start_col = columns.get("start")
    end_col = columns.get("end")
    minutes_col = columns.get("minutes")
    product_col = columns.get("product")
    line_col = columns.get("line")
    date_col = columns.get("date")

    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()

        d = extract_date(row_dict, date_col, start_col)
        if d is None:
            # cannot assign a day; skip
            continue

        start_dt = parse_datetime(row_dict.get(start_col)) if start_col else None
        end_dt = parse_datetime(row_dict.get(end_col)) if end_col else None
        minutes = parse_minutes(row_dict.get(minutes_col)) if minutes_col else None

        duration_h: Optional[float] = None
        if start_dt and end_dt and end_dt >= start_dt:
            duration_h = (end_dt - start_dt).total_seconds() / 3600.0
        elif minutes is not None:
            duration_h = minutes / 60.0
        else:
            # insufficient info
            continue

        # basic guards
        if duration_h < 0:
            duration_h = 0.0
        if duration_h > 24:
            # segment sanity cap; detailed capping happens at aggregation
            duration_h = 24.0

        product_val = row_dict.get(product_col) if product_col else None
        personnel_flag = is_personnel_intensive(product_val, personnel_terms, personnel_aliases)

        line_norm: Optional[str] = None
        if line_col:
            line_norm = normalize_line_value(row_dict.get(line_col))
        if not line_norm:
            # try area inference
            area = infer_area_from_path(path)
            line_norm = infer_line_from_area(area)

        records.append({
            "date": d,
            "line": line_norm or "unknown",
            "duration_h": float(duration_h),
            "personnel_flag": bool(personnel_flag),
            "source_file": os.path.basename(path),
            "source_type": parse_source_type(os.path.basename(path)),
        })

    if not records:
        return pd.DataFrame()

    seg = pd.DataFrame.from_records(records)

    # Aggregate to day×line
    grouped = seg.groupby(["date", "line"], dropna=False).agg(
        total_hours=("duration_h", "sum"),
        personnel_intensive_flag=("personnel_flag", "max"),
        num_segments=("duration_h", "count"),
        source_file=("source_file", lambda x: ",".join(sorted(set(x)))),
        source_type=("source_type", lambda x: ",".join(sorted(set(x)))),
    ).reset_index()

    # Cap at 24h per day×line
    grouped["capped"] = grouped["total_hours"] > 24.0
    grouped.loc[grouped["capped"] == True, "total_hours"] = 24.0

    grouped["weekday"] = grouped["date"].apply(lambda d: pd.Timestamp(d).day_name()[:3])
    grouped["kw"] = grouped["date"].apply(kw_from_date)

    # Reorder columns
    grouped = grouped[[
        "date", "weekday", "kw", "line", "total_hours",
        "personnel_intensive_flag", "num_segments", "source_file", "source_type", "capped",
    ]]

    # Replace NaN line with unknown string
    grouped["line"] = grouped["line"].fillna("unknown")

    return grouped


def main():
    parser = argparse.ArgumentParser(description="POC ETL: Normalize weekly Excel files to daily line hours")
    parser.add_argument("--input-root", default=os.getcwd(), help="Root path containing year/area folders")
    parser.add_argument("--years", nargs="*", default=["2024"], help="Years to include (e.g. 2024 2025)")
    parser.add_argument("--areas", nargs="*", default=["H2_H3", "H4", "M2_M3"], help="Areas to include")
    parser.add_argument("--max-files", type=int, default=12, help="Max number of Excel files to process")
    parser.add_argument("--out", default="data/processed/normalized_daily.csv", help="Output CSV path")
    parser.add_argument("--save-parquet", action="store_true", help="Also save Parquet next to CSV")
    parser.add_argument("--report-path", default="data/reports/ingest_summary.json", help="JSON report path")
    parser.add_argument("--personnel-config", default="config/personnel_intensive.yml", help="Personnel terms config")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--matrix", action="store_true", default=True, help="Use matrix parser (default)")

    args = parser.parse_args()

    ensure_directories([
        os.path.dirname(args.out) or ".",
        os.path.dirname(args.report_path) or ".",
        "logs",
    ])

    logger, log_path = configure_logging("logs", args.log_level)

    files = find_excel_files([args.input_root], args.years, args.areas, args.max_files)
    logger.info(f"Found {len(files)} files to process")

    terms, aliases = load_personnel_config(args.personnel_config)
    if terms:
        logger.info(f"Loaded {len(terms)} personnel-intensive terms and {len(aliases)} aliases")

    all_rows: List[pd.DataFrame] = []
    per_file_stats: List[Dict[str, Any]] = []

    for f in files:
        logger.info(f"Processing: {f}")
        out_df = normalize_matrix_file(f, terms, aliases, logger)
        if out_df.empty:
            logger.warning(f"No usable rows from file: {f}")
            per_file_stats.append({
                "file": f,
                "rows": 0,
                "unknown_line_pct": None,
                "capped_rows": 0,
            })
            continue
        all_rows.append(out_df)
        total = len(out_df)
        unknown = (out_df["line"] == "unknown").sum()
        capped = (out_df["capped"]).sum()
        per_file_stats.append({
            "file": f,
            "rows": int(total),
            "unknown_line_pct": float(unknown) / float(total) if total else 0.0,
            "capped_rows": int(capped),
        })

    if not all_rows:
        logger.error("No data produced. Aborting.")
        return 2

    combined = pd.concat(all_rows, ignore_index=True)

    # Apply deduplication strategy for same day×line combinations
    logger.info("Applying deduplication strategy...")
    before_dedup = len(combined)
    combined = deduplicate_records(combined)
    after_dedup = len(combined)
    dedup_removed = before_dedup - after_dedup
    if dedup_removed > 0:
        logger.info(f"Removed {dedup_removed} duplicate day×line records")

    # Required columns invariant
    required = ["date", "weekday", "kw", "line", "total_hours"]
    for c in required:
        if combined[c].isna().any():
            logger.warning(f"NaN detected in required column {c}; filling with defaults")
            if c == "line":
                combined[c] = combined[c].fillna("unknown")
            elif c == "weekday":
                combined[c] = combined["date"].apply(lambda d: pd.Timestamp(d).day_name()[:3])
            elif c == "kw":
                combined[c] = combined["date"].apply(kw_from_date)
            else:
                combined[c] = combined[c].fillna(0)

    # Save outputs
    combined_sorted = combined.sort_values(["date", "line"]).reset_index(drop=True)
    out_csv = args.out
    combined_sorted.to_csv(out_csv, index=False)
    logger.info(f"Wrote CSV: {out_csv} ({len(combined_sorted)} rows)")

    if args.save_parquet:
        out_parquet = os.path.splitext(out_csv)[0] + ".parquet"
        combined_sorted.to_parquet(out_parquet, index=False)
        logger.info(f"Wrote Parquet: {out_parquet}")

    # Report
    summary: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "files_processed": len(per_file_stats),
        "rows_total": int(len(combined_sorted)),
        "unknown_line_pct_overall": float((combined_sorted["line"] == "unknown").sum()) / float(len(combined_sorted)),
        "capped_rows_total": int((combined_sorted["capped"]).sum()),
        "per_file": per_file_stats,
        "outputs": {
            "csv": out_csv,
            "parquet": (os.path.splitext(out_csv)[0] + ".parquet") if args.save_parquet else None,
            "log": log_path,
        },
    }

    report_path = args.report_path
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote report: {report_path}")

    # End-of-run recap
    logger.info("Run summary:")
    logger.info(f"  Files processed: {summary['files_processed']}")
    logger.info(f"  Total rows: {summary['rows_total']}")
    logger.info(f"  Unknown line % (overall): {summary['unknown_line_pct_overall']:.1%}")
    logger.info(f"  Capped rows: {summary['capped_rows_total']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
