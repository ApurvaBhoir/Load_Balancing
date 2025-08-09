# 🔄 Load Balancing PoC - Reproduction Guide

This guide provides step-by-step instructions to reproduce the Ritter Sport production load balancing analysis from scratch.

## 📋 Prerequisites

- **Python 3.8+** with `pip` and `venv`
- **Excel files** in the expected directory structure
- **Terminal/Command Line** access
- **Web browser** (for viewing dashboard)

## 🗂️ Data Structure Expected

```
anlage_data/
├── data/
│   ├── 2024/
│   │   ├── H2_H3/
│   │   │   ├── WP_H2+H3_KW 02 Konzept.xlsx
│   │   │   ├── WP_H2+H3_KW 02 Version 1.xlsx
│   │   │   └── ... (more Excel files)
│   │   ├── H4/
│   │   │   └── ... (H4 Excel files)
│   │   └── M2_M3/
│   │       └── ... (M2_M3 Excel files)
│   └── 2025/
│       └── ... (similar structure)
```

## 🚀 Step-by-Step Reproduction

### Step 1: Environment Setup

```bash
# Clone or create project directory
mkdir anlage_data
cd anlage_data

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install pandas openpyxl pyyaml
```

### Step 2: Project Structure Setup

```bash
# Create directory structure
mkdir -p src/etl src/forecast src/smooth src/viz
mkdir -p data/processed data/reports logs config docs tasks planning

# Create __init__.py files
touch src/__init__.py src/etl/__init__.py src/forecast/__init__.py src/smooth/__init__.py src/viz/__init__.py
```

### Step 3: Configuration Files

**Create `config/personnel_intensive.yml`:**
```yaml
personnel_intensive_terms:
  - "Nuss"
  - "Haselnuss" 
  - "Edelbitter"
  - "Edel"
  - "Ganze"

aliases:
  "Hasel": "Haselnuss"
  "Edel-Bitter": "Edelbitter"
  "Ganz": "Ganze"
```

### Step 4: Copy Source Code

Copy the following Python modules from this PoC:

**Required files to copy:**
```bash
# ETL modules
src/etl/utils.py          # Helper functions
src/etl/ingest.py         # Main ingestion script  
src/etl/matrix_parser.py  # Excel matrix parser
src/etl/schema_probe.py   # Excel structure analyzer

# Forecasting
src/forecast/baseline.py  # Weekday average forecasting

# Smoothing
src/smooth/greedy.py      # Load redistribution algorithm

# Visualization  
src/viz/dashboard.py      # HTML dashboard generator
```

*Note: All source code is available in the PoC repository. Copy these files exactly as they contain the matrix parsing logic specific to the Excel layout.*

### Step 5: Data Ingestion

**Analyze Excel structure (optional):**
```bash
# Probe Excel files to understand their structure
python -m src.etl.schema_probe \
  --root . \
  --years 2024 \
  --areas H2_H3 H4 M2_M3 \
  --per-area-limit 2 \
  --out data/reports/schema_probe.json
```

**Run data ingestion:**
```bash
# Process Excel files into normalized CSV
python -m src.etl.ingest \
  --input-root . \
  --years 2024 \
  --areas H2_H3 H4 M2_M3 \
  --max-files 12 \
  --out data/processed/normalized_daily.csv \
  --save-parquet \
  --report-path data/reports/ingest_summary.json \
  --personnel-config config/personnel_intensive.yml \
  --log-level INFO
```

**Expected output:**
- `data/processed/normalized_daily.csv` (~300-500 rows)
- `data/processed/normalized_daily.parquet`
- `data/reports/ingest_summary.json` 
- `logs/ingest_<timestamp>.log`

### Step 6: Baseline Forecasting

```bash
# Generate 4-week forecast starting April 1st, 2024
python -m src.forecast.baseline \
  --input data/processed/normalized_daily.csv \
  --start-date 2024-04-01 \
  --weeks 4 \
  --output data/processed/forecast_baseline.csv \
  --report data/reports/forecast_baseline.json
```

**Expected output:**
- `data/processed/forecast_baseline.csv` (~20-40 rows)
- `data/reports/forecast_baseline.json`

### Step 7: Load Smoothing

```bash
# Apply greedy smoothing algorithm
python -m src.smooth.greedy \
  --input data/processed/forecast_baseline.csv \
  --output data/processed/forecast_smoothed.csv \
  --report data/reports/smoothing_report.json \
  --max-transfers 5 \
  --personnel-config config/personnel_intensive.yml
```

**Expected output:**
- `data/processed/forecast_smoothed.csv`
- `data/reports/smoothing_report.json`

### Step 8: Dashboard Generation

```bash
# Create interactive HTML dashboard
python -m src.viz.dashboard \
  --historical data/processed/normalized_daily.csv \
  --forecast data/processed/forecast_baseline.csv \
  --smoothed data/processed/forecast_smoothed.csv \
  --output dashboard.html
```

**Expected output:**
- `dashboard.html` (interactive visualization)

### Step 9: View Results

```bash
# Open dashboard in browser
open dashboard.html  # On macOS
# Or: start dashboard.html  # On Windows
# Or: xdg-open dashboard.html  # On Linux
```

## 📊 Expected Results

### Data Quality Metrics
- **Historical records**: ~300-500 normalized day×line entries
- **Unknown line rate**: <5% (ideally 0% for H2_H3)
- **Capped rows**: 0 (no duration anomalies)
- **Date coverage**: January-March 2024 (depending on files)

### Forecast Quality
- **Prediction period**: 4 weeks from start date
- **Daily consistency**: Low variance (σ < 2 hours)
- **Constraint compliance**: 0 capacity violations
- **Personnel-intensive rate**: ~30-70% depending on historical data

### Dashboard Features
- **Timeline chart**: Historical vs forecast comparison
- **Weekday patterns**: Average hours by day of week
- **Line utilization**: Radar chart showing capacity usage
- **Metrics table**: Key statistics and improvements

## 🔧 Troubleshooting

### Common Issues

**1. "No files found" error:**
```bash
# Check file paths
ls -la data/2024/H2_H3/*.xlsx
# Ensure Excel files are in correct directory structure
```

**2. "No header row found" error:**
```bash
# Excel files may have different layout
# Run schema probe to analyze structure:
python -m src.etl.schema_probe --root . --areas H2_H3 --per-area-limit 1
```

**3. Import errors:**
```bash
# Ensure all dependencies installed
pip install pandas openpyxl pyyaml

# Check Python path
export PYTHONPATH=.
```

**4. Empty forecast results:**
```bash
# Check date range - ensure start date is after historical data
# Verify weekday patterns exist in historical data
head -10 data/processed/normalized_daily.csv
```

### Data Validation

**Check normalized data quality:**
```bash
# Row count and basic stats
wc -l data/processed/normalized_daily.csv
head -5 data/processed/normalized_daily.csv

# Check for required columns
head -1 data/processed/normalized_daily.csv | tr ',' '\n' | cat -n
```

**Verify forecast reasonableness:**
```bash
# Check forecast date range and values
head -5 data/processed/forecast_baseline.csv
tail -5 data/processed/forecast_baseline.csv
```

## 📈 Interpretation Guide

### Key Success Indicators

**✅ Data Ingestion Success:**
- Ingestion summary shows >90% usable rows
- No critical errors in logs
- Personnel-intensive tagging working (>0% rate)
- Date parsing successful (valid ISO dates)

**✅ Forecasting Success:**
- Forecast covers requested period completely
- Daily totals are reasonable (20-60 hours typical)
- No capacity violations (line hours ≤24)
- Confidence levels mostly "high"

**✅ Load Balancing Success:**
- Dashboard loads without errors
- Charts display meaningful data
- Historical vs forecast patterns are consistent
- Weekday distribution makes business sense

### Business Insights

**Look for these patterns:**
- **Monday peaks**: Often highest production days
- **Friday drops**: Typically lower utilization
- **Line utilization**: Should be <24h per day per line
- **Personnel bottlenecks**: Days with multiple personnel-intensive jobs

**Red flags:**
- Extremely high variance (>5 hours std dev)
- Capacity violations (>24h per day per line)
- Missing weekday patterns (all days identical)
- Unrealistic forecasts (0 or >100 hours/day)

## 🎯 Next Steps

After successful reproduction:

1. **Expand data coverage**: Add more weeks/areas
2. **Constraint tuning**: Adjust smoothing parameters
3. **Model improvement**: Try advanced forecasting methods
4. **Production deployment**: Set up automated pipeline
5. **Monitoring**: Regular constraint violation alerts

## 📞 Support

If reproduction fails, check:
1. Excel file format matches expected matrix layout
2. All Python dependencies installed correctly
3. Directory structure follows the expected pattern
4. Date ranges are appropriate for your data

The PoC was designed to be robust, but Excel file variations may require minor adjustments to the matrix parser configuration.

---

*Generated: 2025-08-09 | Ritter Sport Load Balancing PoC v1.0*
