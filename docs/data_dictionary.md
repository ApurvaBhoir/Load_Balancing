# Data Dictionary – Normalized Daily Table

Fields
- `date` (string, YYYY‑MM‑DD): Production date
- `weekday` (string): Mon..Fri
- `kw` (int): Calendar week number
- `line` (string): hohl2|hohl3|hohl4|massiv2|massiv3|unknown
- `total_hours` (float): Total production hours for the date×line
- `personnel_intensive_flag` (bool): True if any segment matched configured terms
- `source_type` (string): Konzept|Version1|unknown
- `num_segments` (int): Count of contributing segments
- `source_file` (string): Origin file name
- `notes` (string): Short notes about corrections/anomalies

Notes
- If `line=unknown`, include in daily totals but exclude from line‑specific KPIs.
- Durations are capped at 24 hours per day×line in PoC for robustness.
