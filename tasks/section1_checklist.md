# Section 1 – Data Ingestion Checklist

- [x] Create folders: `data/processed/`, `data/reports/`, `logs/`, `config/`, `docs/`, `src/etl/`
- [x] Draft `config/personnel_intensive.yml` with terms & aliases
- [x] Select 8–12 sample files (record in `docs/data_sample_list.md`) - 9 H2_H3 files processed
- [x] Implement column detection helpers (`src/etl/utils.py`)
- [x] Implement parser & duration calc (`src/etl/ingest.py` + `src/etl/matrix_parser.py`)
- [x] Implement line inference and mapping - Matrix layout parser with 2-row headers
- [x] Aggregate to day×line and compute `weekday`, `kw`
- [x] Implement validation checks and capping
- [x] Implement personnel‑intensive tagging
- [x] Emit `normalized_daily.csv` and optional `.parquet`
- [x] Generate JSON report and human‑readable logs
- [x] Write `docs/data_dictionary.md`
- [x] Manual QA on 2 files/area (5 rows each) - 317 records, 0% unknown lines, 0 capped rows
- [x] Sign‑off: acceptance criteria met ✅

**✅ COMPLETED** | Owner: AI Agent | Due: 2025-08-09 | **Status: PoC-Ready**

## Achievements
- 317 normalized day×line records from 9 Excel files
- Perfect line detection (0% unknown)
- Matrix layout parser handles complex 2-row headers
- Personnel-intensive tagging working correctly
- All quality gates passed

## Next: Section 2 - Baseline Forecasting
