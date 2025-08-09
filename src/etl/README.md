# ETL Module (PoC)

This folder will contain a minimal Excel ingestion and normalization pipeline for the PoC.

Planned files
- `ingest.py` – CLI for parsing, validation, aggregation, and export
- `utils.py` – Column detection, parsing helpers, and line mapping

Outputs
- `../../data/processed/normalized_daily.csv`
- `../../data/reports/ingest_summary_<timestamp>.json`
- Logs: `../../logs/ingest_<timestamp>.log`
