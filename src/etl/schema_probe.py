import argparse
import glob
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


COLUMN_CANDIDATES: Dict[str, List[str]] = {
    "start": ["start", "beginn", "von"],
    "end": ["end", "ende", "bis"],
    "minutes": ["min", "minuten"],
    "product": ["product", "produkt", "rezeptur", "sorte"],
    "line": ["anlage", "linie", "line"],
    "date": ["date", "datum", "tag", "day"],
}

WEEKDAY_TOKENS = {"mo", "di", "mi", "do", "fr", "montag", "dienstag", "mittwoch", "donnerstag", "freitag"}
TIME_REGEX = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b")


def normalize_header(h: Any) -> str:
    return str(h).strip().lower()


def detect_columns(columns: List[Any]) -> Dict[str, Optional[str]]:
    mapping: Dict[str, Optional[str]] = {k: None for k in COLUMN_CANDIDATES.keys()}
    normalized = {normalize_header(c): str(c) for c in columns}
    for logical, candidates in COLUMN_CANDIDATES.items():
        for cand in candidates:
            if cand in normalized:
                mapping[logical] = normalized[cand]
                break
    return mapping


def choose_best_sheet(xls_path: str, sheet_names: List[str]) -> Tuple[Optional[str], Dict[str, Any]]:
    best_sheet: Optional[str] = None
    best_score: int = -1
    best_columns: List[str] = []

    for s in sheet_names:
        try:
            df = pd.read_excel(xls_path, sheet_name=s, nrows=10)
        except Exception:
            continue
        cols = list(df.columns)
        mapping = detect_columns(cols)
        # scoring: count detected logical columns + number of non-empty column names
        detected = sum(1 for v in mapping.values() if v is not None)
        non_empty = sum(1 for c in cols if str(c).strip() != "")
        score = detected * 10 + non_empty
        if score > best_score:
            best_score = score
            best_sheet = s
            best_columns = [str(c) for c in cols]

    return best_sheet, {"score": best_score, "columns": best_columns}


def find_files(root: str, year: str, area: str, limit: int) -> List[str]:
    base = os.path.join(root, "data", year, area)
    files = glob.glob(os.path.join(base, "*.xlsx"))
    if not files:
        files = glob.glob(os.path.join(base, "**", "*.xlsx"), recursive=True)
    return sorted(files)[:limit]


def sample_cells(xls_path: str, sheet_name: str, max_rows: int = 40, max_cols: int = 25, max_samples: int = 50) -> Dict[str, Any]:
    try:
        df = pd.read_excel(xls_path, sheet_name=sheet_name, header=None, nrows=max_rows)
    except Exception as e:
        return {"error": str(e)}

    samples: List[Dict[str, Any]] = []
    weekday_hits = 0
    time_hits = 0

    for r in range(min(max_rows, df.shape[0])):
        for c in range(min(max_cols, df.shape[1])):
            val = df.iat[r, c]
            if pd.isna(val):
                continue
            s = str(val).strip()
            if s == "":
                continue
            lower = s.lower()
            if any(tok in lower for tok in WEEKDAY_TOKENS):
                weekday_hits += 1
            if TIME_REGEX.search(s):
                time_hits += 1
            if len(samples) < max_samples:
                samples.append({"r": r, "c": c, "v": s[:80]})

    return {
        "shape": [int(df.shape[0]), int(df.shape[1])],
        "weekday_token_hits": weekday_hits,
        "time_token_hits": time_hits,
        "samples": samples,
    }


def probe(root: str, years: List[str], areas: List[str], per_area_limit: int) -> Dict[str, Any]:
    report: Dict[str, Any] = {"years": years, "areas": areas, "files": []}

    for y in years:
        for a in areas:
            files = find_files(root, y, a, per_area_limit)
            for f in files:
                entry: Dict[str, Any] = {"file": f, "year": y, "area": a}
                try:
                    xls = pd.ExcelFile(f)
                    entry["sheets"] = xls.sheet_names
                    chosen, meta = choose_best_sheet(f, xls.sheet_names)
                    entry["chosen_sheet"] = chosen
                    entry["columns"] = meta.get("columns")
                    entry["detected"] = detect_columns(meta.get("columns") or [])
                    if chosen:
                        entry["content_sample"] = sample_cells(f, chosen)
                except Exception as e:
                    entry["error"] = str(e)
                report["files"].append(entry)
    return report


def main():
    parser = argparse.ArgumentParser(description="Probe Excel schemas across areas and years")
    parser.add_argument("--root", default=os.getcwd(), help="Repository root (contains data/<year>/<area>)")
    parser.add_argument("--years", nargs="*", default=["2024"], help="Years to scan")
    parser.add_argument("--areas", nargs="*", default=["H2_H3", "H4", "M2_M3"], help="Areas to scan")
    parser.add_argument("--per-area-limit", type=int, default=4, help="Max files per area to inspect")
    parser.add_argument("--out", default="data/reports/schema_probe.json", help="Output JSON path")

    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    report = probe(args.root, args.years, args.areas, args.per_area_limit)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print concise summary
    total = len(report.get("files", []))
    print(f"Probed {total} files. Output: {args.out}")
    by_area: Dict[str, int] = {}
    for e in report.get("files", []):
        by_area[e.get("area", "?")] = by_area.get(e.get("area", "?"), 0) + 1
    print("Files per area:", by_area)


if __name__ == "__main__":
    main()
