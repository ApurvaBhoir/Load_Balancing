# Section 1 – Data Ingestion (Light) Plan

## Objectives
- Build a small, robust pipeline to ingest a handful of weekly Excel files, normalize them to a day×line table, and tag personnel‑intensive sorts.
- Produce clean outputs, validation checks, and clear logs to support downstream forecast/scheduling and make the PoC easy to evaluate.

## Deliverables
- `src/etl/ingest.py`: CLI to load Excel files, normalize, validate, and export.
- `data/processed/normalized_daily.csv` and `.parquet` (optional).
- `data/reports/ingest_summary_<timestamp>.json`.
- `logs/ingest_<timestamp>.log` (user‑friendly logging).
- `docs/data_dictionary.md` (schema) and `docs/data_sample_list.md`.

## Data sampling
- Select 3–5 files each from `2024/H2_H3/`, `2024/H4/`, `2024/M2_M3/`; optionally 1–2 from `2025/`.
- Prefer KW28–35. Record choices in `docs/data_sample_list.md` with rationale.

## Normalized schema (target)
Required:
- `date` (YYYY‑MM‑DD)
- `weekday` (Mon..Fri)
- `kw` (int)
- `line` (hohl2|hohl3|hohl4|massiv2|massiv3|unknown)
- `total_hours` (float)

Helpful:
- `source_file`, `source_type` (Konzept|Version1|unknown)
- `num_segments` (int)
- `personnel_intensive_flag` (bool)
- `notes` (short text)

## Personnel‑intensive sorts tagging
- Config file: `config/personnel_intensive.yml`
- Canonical terms: ["100g Knusperkeks", "100g Waffel", "100g Marzipan", "Mini Knusperkeks", "Schokowürfel"]
- Aliases: e.g., {"SW": "Schokowürfel", "Mini KK": "Mini Knusperkeks"}
- Rule: any segment matching terms/aliases → flag day×line as true.

## Parsing rules (Excel → segments)
- Sheet: default first visible; allow `--sheet` override.
- Column mapping (case/locale tolerant):
  - start: [start, Start, Beginn, von]
  - end: [end, Ende, bis]
  - minutes: [min, Minuten]
  - product: [product, Produkt, Rezeptur, Sorte]
  - line: [Anlage, Linie, Line]
- Duration: if start/end present, duration = max(0, end − start); else use minutes/60.0
- Skip rows without both time window and minutes.
- `source_type` from filename containing "Konzept" or "Version".

## Line inference
- From directory: `H2_H3`→{hohl2, hohl3}, `H4`→{hohl4}, `M2_M3`→{massiv2, massiv3}
- If line column missing and multi‑line area:
  - POC: `line=unknown`; include in daily totals, exclude from line‑level KPIs; warn + note.
- If line column exists: normalize values with tolerant mapping (e.g., "Hohl 2"→hohl2).

## Aggregation to day×line
- Group by `date`, `line`; sum `duration_hours` as `total_hours`.
- Derive `weekday`, `kw` from `date`.
- `personnel_intensive_flag` = any match across segments.
- `num_segments` = count of segments aggregated.

## Validation checks
- Schema presence: ≥80% rows have [start/end] or [minutes].
- Time sanity: end ≥ start; duration ≤ 24h per segment; negatives → 0 with warning.
- Overlaps: warn if overlapping segments per day×line (informational).
- Day totals: if per day×line > 24, cap at 24 with warning (POC safeguard).
- Missing line: log; mark `line=unknown`; report % unknown per file.
- Output invariants: required cols non‑null; `total_hours ≥ 0`.

## CLI & UX
Example:
```
python -m src.etl.ingest \
  --input-root anlage_data/2024 \
  --years 2024 2025 \
  --areas H2_H3 H4 M2_M3 \
  --max-files 12 \
  --out data/processed/normalized_daily.csv \
  --save-parquet \
  --report-path data/reports/ingest_summary.json \
  --personnel-config config/personnel_intensive.yml \
  --log-level INFO
```

## Logging & reporting
- Human‑readable logs with counts and clear decisions.
- JSON report with per‑file stats: detected columns, unknown line %, personnel‑intensive hits, dropped rows.

## File layout to create
- `src/etl/ingest.py`, `src/etl/utils.py`
- `config/personnel_intensive.yml`
- `data/processed/`, `data/reports/`, `logs/`
- `docs/data_dictionary.md`, `docs/data_sample_list.md`

## Acceptance criteria
- 8–12 files processed; JSON report generated.
- ≥90% usable rows with valid `date` and non‑unknown `line` (H4 fully known; ≤20% unknown for others).
- No NaNs in required columns; sensible hours.
- Personnel‑intensive tagging verified on ≥3 examples.
- Clear end‑of‑run summary.

## Timeboxing (2–3 days)
- Day 1: sampling, scaffolding, parsing helpers; duration calc.
- Day 2: line inference, aggregation, validation, tagging.
- Day 3: reporting polish, docs, small fixes.

## Manual QA checklist
- Cross‑check 2 files/area vs normalized output (5 rows each).
- Verify a tagged personnel‑intensive day×line.
- Totals align directionally with `production-analysis.html` for sampled weeks.

## Risks & mitigations
- Column drift → tolerant matching + explicit mapping log.
- Missing line in multi‑line areas → mark unknown; quantify; avoid risky heuristics.
- Dirty time data → cap durations; visible warnings in report.
