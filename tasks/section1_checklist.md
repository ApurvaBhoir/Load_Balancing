# Section 1 – Data Ingestion Checklist

- [ ] Create folders: `data/processed/`, `data/reports/`, `logs/`, `config/`, `docs/`, `src/etl/`
- [ ] Draft `config/personnel_intensive.yml` with terms & aliases
- [ ] Select 8–12 sample files (record in `docs/data_sample_list.md`)
- [ ] Implement column detection helpers (`src/etl/utils.py`)
- [ ] Implement parser & duration calc (`src/etl/ingest.py`)
- [ ] Implement line inference and mapping
- [ ] Aggregate to day×line and compute `weekday`, `kw`
- [ ] Implement validation checks and capping
- [ ] Implement personnel‑intensive tagging
- [ ] Emit `normalized_daily.csv` and optional `.parquet`
- [ ] Generate JSON report and human‑readable logs
- [ ] Write `docs/data_dictionary.md`
- [ ] Manual QA on 2 files/area (5 rows each)
- [ ] Sign‑off: acceptance criteria met

Owner: __________  |  Due: __________
