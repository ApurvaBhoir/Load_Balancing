import os
import re
import yaml
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any, Set

import pandas as pd


ColumnCandidates = {
    "start": ["start", "beginn", "von"],
    "end": ["end", "ende", "bis"],
    "minutes": ["min", "minuten"],
    "product": ["product", "produkt", "rezeptur", "sorte"],
    "line": ["anlage", "linie", "line"],
    "date": ["date", "datum", "tag", "day"],
}


def normalize_header(header: str) -> str:
    return str(header).strip().lower()


def detect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    mapping: Dict[str, Optional[str]] = {k: None for k in ColumnCandidates.keys()}
    normalized = {normalize_header(c): c for c in df.columns}
    for logical, candidates in ColumnCandidates.items():
        for cand in candidates:
            if cand in normalized:
                mapping[logical] = normalized[cand]
                break
    return mapping


def parse_datetime(value: Any) -> Optional[datetime]:
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    try:
        return pd.to_datetime(value, errors="coerce").to_pydatetime()  # type: ignore[attr-defined]
    except Exception:
        return None


def parse_minutes(value: Any) -> Optional[float]:
    if pd.isna(value):
        return None
    try:
        f = float(value)
        return f if f >= 0 else None
    except Exception:
        return None


def extract_date(row: Dict[str, Any], date_col: Optional[str], start_col: Optional[str]) -> Optional[date]:
    if date_col is not None and date_col in row:
        dt = parse_datetime(row.get(date_col))
        if dt is not None:
            return dt.date()
    if start_col is not None and start_col in row:
        dt = parse_datetime(row.get(start_col))
        if dt is not None:
            return dt.date()
    return None


_LINE_NORMALIZATION = {
    "hohl 2": "hohl2",
    "hohl2": "hohl2",
    "h2": "hohl2",
    "hohl 3": "hohl3",
    "hohl3": "hohl3",
    "h3": "hohl3",
    "hohl 4": "hohl4",
    "hohl4": "hohl4",
    "h4": "hohl4",
    "massiv 2": "massiv2",
    "massiv2": "massiv2",
    "m2": "massiv2",
    "massiv 3": "massiv3",
    "massiv3": "massiv3",
    "m3": "massiv3",
}


def normalize_line_value(value: Any) -> Optional[str]:
    if pd.isna(value):
        return None
    s = str(value).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return _LINE_NORMALIZATION.get(s)


def infer_area_from_path(path: str) -> Optional[str]:
    lowered = path.lower()
    if "h2_h3" in lowered:
        return "H2_H3"
    if os.sep + "h4" + os.sep in lowered or lowered.endswith(os.sep + "h4"):
        return "H4"
    if "m2_m3" in lowered:
        return "M2_M3"
    return None


def infer_line_from_area(area: Optional[str]) -> Optional[str]:
    if area == "H4":
        return "hohl4"
    return None  # multi-line areas require explicit line or will be unknown


def parse_source_type(filename: str) -> str:
    name = filename.lower()
    if "konzept" in name:
        return "Konzept"
    if "version" in name:
        return "Version1"
    return "unknown"


def load_personnel_config(config_path: Optional[str]) -> Tuple[Set[str], Dict[str, str]]:
    if not config_path or not os.path.exists(config_path):
        return set(), {}
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    terms = set([str(x).strip().lower() for x in (data.get("terms") or [])])
    aliases_raw = data.get("aliases") or {}
    aliases = {str(k).strip().lower(): str(v).strip().lower() for k, v in aliases_raw.items()}
    return terms, aliases


def is_personnel_intensive(product_value: Any, terms: Set[str], aliases: Dict[str, str]) -> bool:
    if not terms and not aliases:
        return False
    if pd.isna(product_value):
        return False
    s = str(product_value).strip().lower()
    tokens = {s}
    for alias, canon in aliases.items():
        if alias in s:
            tokens.add(canon)
    for term in terms:
        if term in s:
            return True
    for t in tokens:
        if t in terms:
            return True
    return False


def ensure_directories(paths: List[str]) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)


def kw_from_date(d: date) -> int:
    try:
        return int(pd.Timestamp(d).isocalendar().week)  # type: ignore[attr-defined]
    except Exception:
        return pd.Timestamp(d).week  # type: ignore[attr-defined]


def configure_logging(log_dir: str, log_level: str) -> Tuple[logging.Logger, str]:
    ensure_directories([log_dir])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"ingest_{ts}.log")
    logger = logging.getLogger("etl.ingest")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers = []
    fh = logging.FileHandler(log_path, encoding="utf-8")
    ch = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger, log_path
