import os
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Set

import pandas as pd

from .utils import (
    load_personnel_config,
    is_personnel_intensive,
    kw_from_date,
    parse_source_type,
)

# Weekday tokens for robust row detection
WEEKDAY_TOKENS = {"mo", "di", "mi", "do", "fr", "montag", "dienstag", "mittwoch", "donnerstag", "freitag"}
TIME_REGEX = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b")


def detect_header_row(df: pd.DataFrame, max_scan: int = 20, debug: bool = False) -> Optional[int]:
    """Find the row containing 'Tag', 'Datum' - headers are split across two rows."""
    for r in range(min(max_scan, len(df))):
        # Check current row for tag/datum
        row_vals = []
        for c in range(df.shape[1]):
            val = df.iat[r, c]
            if not pd.isna(val):
                row_vals.append(str(val).lower().strip())
        
        has_tag = any("tag" in val for val in row_vals)
        has_datum = any("datum" in val for val in row_vals)
        
        # Check next row for time headers
        has_time = False
        if r + 1 < len(df):
            next_row_vals = []
            for c in range(df.shape[1]):
                val = df.iat[r + 1, c]
                if not pd.isna(val):
                    next_row_vals.append(str(val).lower().strip())
            has_time = any(val in ["start", "ende", "min", "soll"] for val in next_row_vals)
        
        if debug and (has_tag or has_datum or has_time):
            print(f"Row {r}: tag={has_tag}, datum={has_datum}, time={has_time}, vals={row_vals[:8]}")
        
        # The header row is the one with Tag/Datum; time headers are on the next row
        if has_tag and has_datum and has_time:
            return r
    return None


def detect_blocks(df: pd.DataFrame, header_row: int) -> List[Dict[str, Any]]:
    """Detect line blocks from two-row header structure."""
    blocks: List[Dict[str, Any]] = []
    
    # Row structure:
    # header_row: Tag, Datum, [Line Name], ..., Tag, Datum, [Line Name], ...
    # header_row+1: Start, Ende, Min, Soll, Rezeptur, Produkt, Start, Ende, Min, Soll, Rezeptur, Produkt
    
    header_vals = [str(df.iat[header_row, c]).strip() for c in range(df.shape[1])]
    time_row = header_row + 1
    time_vals = [str(df.iat[time_row, c]).strip() for c in range(df.shape[1])] if time_row < len(df) else []
    
    # Find blocks by scanning for "Tag" positions
    for c in range(df.shape[1]):
        h = header_vals[c].lower()
        if h == "tag":
            # Found a potential block start
            block = {"tag_col": c, "line_name": "unknown"}
            
            # Look for line name in the same row (usually +2 position from Tag)
            for offset in range(5):  # Check next few columns for line name
                col_idx = c + offset
                if col_idx < len(header_vals):
                    candidate = header_vals[col_idx].lower()
                    if "hohl 2" in candidate:
                        block["line_name"] = "hohl2"
                        break
                    elif "hohl 3" in candidate:
                        block["line_name"] = "hohl3"
                        break
                    elif "hohl 4" in candidate:
                        block["line_name"] = "hohl4"
                        break
                    elif "massiv 2" in candidate:
                        block["line_name"] = "massiv2"
                        break
                    elif "massiv 3" in candidate:
                        block["line_name"] = "massiv3"
                        break
            
            # Map columns based on expected layout:
            # Tag(c), Datum(c+1), then time headers start usually at c or c+2
            block["tag_col"] = c
            block["datum_col"] = c + 1 if c + 1 < df.shape[1] else None
            
            # Find start of time headers by looking for "Start" in time_vals
            time_start = None
            for offset in range(8):  # Check reasonable range
                col_idx = c + offset
                if col_idx < len(time_vals) and time_vals[col_idx].lower() == "start":
                    time_start = col_idx
                    break
            
            if time_start is not None:
                # Map time columns relative to start position
                for i, field in enumerate(["start", "ende", "min", "soll", "rezeptur", "produkt"]):
                    col_idx = time_start + i
                    if col_idx < df.shape[1]:
                        block[f"{field}_col"] = col_idx
            
            blocks.append(block)
    
    return blocks


def parse_date_with_year(date_str: str, year: int) -> Optional[date]:
    """Parse DD.MM. format with provided year."""
    if not date_str or pd.isna(date_str):
        return None
    
    s = str(date_str).strip()
    # Match DD.MM. pattern
    match = re.match(r"(\d{1,2})\.(\d{1,2})\.", s)
    if match:
        try:
            day, month = int(match.group(1)), int(match.group(2))
            return date(year, month, day)
        except ValueError:
            pass
    return None


def parse_time_duration(start_str: Any, end_str: Any, min_str: Any) -> Optional[float]:
    """Parse time duration from start/end times or minutes."""
    if start_str and end_str and not pd.isna(start_str) and not pd.isna(end_str):
        start_s = str(start_str).strip()
        end_s = str(end_str).strip()
        
        # Parse HH:MM format
        start_match = re.search(r"(\d{1,2}):(\d{2})", start_s)
        end_match = re.search(r"(\d{1,2}):(\d{2})", end_s)
        
        if start_match and end_match:
            try:
                start_h = int(start_match.group(1))
                start_m = int(start_match.group(2))
                end_h = int(end_match.group(1))
                end_m = int(end_match.group(2))
                
                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m
                
                # Handle overnight spans
                if end_minutes < start_minutes:
                    end_minutes += 24 * 60
                
                duration_minutes = end_minutes - start_minutes
                return duration_minutes / 60.0
            except ValueError:
                pass
    
    # Fallback to min column
    if min_str and not pd.isna(min_str):
        try:
            return float(min_str) / 60.0
        except (ValueError, TypeError):
            pass
    
    return None


def infer_year_from_path(path: str) -> int:
    """Extract year from file path or name."""
    # Try to find year in path segments
    parts = path.split(os.sep)
    for part in parts:
        if part.isdigit() and len(part) == 4 and part.startswith("20"):
            return int(part)
    
    # Try filename patterns like KW_02_24
    basename = os.path.basename(path)
    year_match = re.search(r"(\d{2})(?:\.xlsx)?$", basename)
    if year_match:
        year_suffix = int(year_match.group(1))
        # Assume 20XX
        return 2000 + year_suffix
    
    # Default fallback
    return 2024


def normalize_matrix_file(path: str, personnel_terms: Set[str], personnel_aliases: Dict[str, str], logger) -> pd.DataFrame:
    """Parse matrix-layout Excel file with proper block detection."""
    try:
        # Read file and detect best sheet
        xl = pd.ExcelFile(path)
        sheet_name = xl.sheet_names[0]  # Use first sheet for now
        df = pd.read_excel(path, sheet_name=sheet_name, header=None)
        logger.info(f"  Sheet: {sheet_name}, shape: {df.shape}")
    except Exception as e:
        logger.warning(f"Failed to read file {path}: {e}")
        return pd.DataFrame()
    
    # Detect header row and blocks
    header_row = detect_header_row(df, debug=False)
    if header_row is None:
        logger.warning(f"  No header row found in {path}")
        return pd.DataFrame()
    
    blocks = detect_blocks(df, header_row)
    if not blocks:
        logger.warning(f"  No valid blocks found in {path}")
        return pd.DataFrame()
    
    logger.info(f"  Found {len(blocks)} blocks at header row {header_row}")
    for i, block in enumerate(blocks):
        logger.info(f"    Block {i}: {block['line_name']} at col {block['tag_col']}")
    
    # Extract year for date parsing
    year = infer_year_from_path(path)
    source_type = parse_source_type(os.path.basename(path))
    
    # Parse data rows
    records: List[Dict[str, Any]] = []
    data_start = header_row + 2  # Skip header row and time header row
    
    for r in range(data_start, min(data_start + 100, len(df))):  # Scan up to 100 rows
        for block in blocks:
            tag_col = block.get("tag_col")
            if tag_col is None:
                continue
                
            # Check if this row has data for this block
            tag_val = df.iat[r, tag_col] if tag_col < df.shape[1] else None
            if pd.isna(tag_val) or str(tag_val).strip() == "":
                continue
            
            tag_str = str(tag_val).strip().lower()
            if tag_str not in WEEKDAY_TOKENS:
                continue
            
            # Extract date
            datum_col = block.get("datum_col")
            datum_val = df.iat[r, datum_col] if datum_col and datum_col < df.shape[1] else None
            parsed_date = parse_date_with_year(datum_val, year)
            if parsed_date is None:
                continue
            
            # Extract times and duration
            start_col = block.get("start_col")
            end_col = block.get("ende_col") 
            min_col = block.get("min_col")
            
            start_val = df.iat[r, start_col] if start_col and start_col < df.shape[1] else None
            end_val = df.iat[r, end_col] if end_col and end_col < df.shape[1] else None
            min_val = df.iat[r, min_col] if min_col and min_col < df.shape[1] else None
            
            duration = parse_time_duration(start_val, end_val, min_val)
            if duration is None or duration <= 0:
                continue
            
            # Cap extremely long durations
            if duration > 24:
                duration = 24.0
            
            # Extract product info
            produkt_col = block.get("produkt_col")
            produkt_val = df.iat[r, produkt_col] if produkt_col and produkt_col < df.shape[1] else None
            
            # Check for personnel-intensive
            personnel_flag = is_personnel_intensive(produkt_val, personnel_terms, personnel_aliases)
            
            records.append({
                "date": parsed_date,
                "line": block["line_name"],
                "duration_h": duration,
                "personnel_flag": personnel_flag,
                "source_file": os.path.basename(path),
                "source_type": source_type,
                "product": str(produkt_val) if produkt_val and not pd.isna(produkt_val) else "",
            })
    
    if not records:
        logger.warning(f"  No valid data rows found in {path}")
        return pd.DataFrame()
    
    # Convert to DataFrame and aggregate
    seg_df = pd.DataFrame.from_records(records)
    logger.info(f"  Extracted {len(seg_df)} segments from {path}")
    
    # Aggregate to day×line
    grouped = seg_df.groupby(["date", "line"], dropna=False).agg(
        total_hours=("duration_h", "sum"),
        personnel_intensive_flag=("personnel_flag", "max"),
        num_segments=("duration_h", "count"),
        source_file=("source_file", lambda x: ",".join(sorted(set(x)))),
        source_type=("source_type", lambda x: ",".join(sorted(set(x)))),
    ).reset_index()
    
    # Cap at 24h per day×line
    grouped["capped"] = grouped["total_hours"] > 24.0
    capped_count = grouped["capped"].sum()
    if capped_count > 0:
        logger.warning(f"  Capped {capped_count} day×line totals exceeding 24h")
        grouped.loc[grouped["capped"], "total_hours"] = 24.0
    
    # Add derived fields
    grouped["weekday"] = grouped["date"].apply(lambda d: pd.Timestamp(d).day_name()[:3])
    grouped["kw"] = grouped["date"].apply(kw_from_date)
    
    # Reorder columns
    grouped = grouped[[
        "date", "weekday", "kw", "line", "total_hours",
        "personnel_intensive_flag", "num_segments", "source_file", "source_type", "capped",
    ]]
    
    logger.info(f"  Produced {len(grouped)} day×line records from {path}")
    
    return grouped
