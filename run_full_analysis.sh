#!/bin/bash
# 🚀 One-command reproduction script for Load Balancing PoC
# 
# Usage: ./run_full_analysis.sh
# 
# This script runs the complete analysis pipeline from Excel files to dashboard.

set -e  # Exit on any error

echo "🔄 Load Balancing PoC - Full Analysis Pipeline"
echo "=============================================="

# Validate setup first
echo "Step 1: Validating setup..."
python validate_setup.py
if [ $? -ne 0 ]; then
    echo "❌ Setup validation failed. Please fix issues before proceeding."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

echo ""
echo "Step 2: Data Ingestion..."
echo "-------------------------"
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

echo "📊 Data quality check after deduplication..."
python -c "
import pandas as pd
df = pd.read_csv('data/processed/normalized_daily.csv')
daily_totals = df.groupby('date')['total_hours'].sum()
print(f'✅ Historical daily mean: {daily_totals.mean():.1f}h (should be ~40-50h for 2 lines)')
print(f'✅ Historical daily std: {daily_totals.std():.1f}h (should be <10h)')
print(f'✅ Unique days: {len(daily_totals)} (should be much less than total rows)')
print(f'✅ Date range: {daily_totals.index.min()} to {daily_totals.index.max()}')
"

if [ $? -ne 0 ]; then
    echo "❌ Data ingestion failed"
    exit 1
fi

echo ""
echo "Step 3: Baseline Forecasting..."
echo "-------------------------------"
python -m src.forecast.baseline \
    --input data/processed/normalized_daily.csv \
    --start-date 2024-04-01 \
    --weeks 4 \
    --output data/processed/forecast_baseline.csv \
    --report data/reports/forecast_baseline.json

if [ $? -ne 0 ]; then
    echo "❌ Forecasting failed"
    exit 1
fi

echo ""
echo "Step 4: Load Smoothing..."
echo "-------------------------"
python -m src.smooth.greedy \
    --input data/processed/forecast_baseline.csv \
    --output data/processed/forecast_smoothed.csv \
    --report data/reports/smoothing_report.json \
    --max-transfers 5 \
    --personnel-config config/personnel_intensive.yml

if [ $? -ne 0 ]; then
    echo "❌ Smoothing failed"
    exit 1
fi

echo ""
echo "Step 5: Dashboard Generation..."
echo "-------------------------------"
python -m src.viz.dashboard \
    --historical data/processed/normalized_daily.csv \
    --forecast data/processed/forecast_baseline.csv \
    --smoothed data/processed/forecast_smoothed.csv \
    --output dashboard.html

if [ $? -ne 0 ]; then
    echo "❌ Dashboard generation failed"
    exit 1
fi

echo ""
echo "🎉 Analysis Complete!"
echo "===================="
echo ""
echo "📊 Generated Files:"
echo "  • data/processed/normalized_daily.csv     - Cleaned historical data"
echo "  • data/processed/forecast_baseline.csv    - Future predictions"  
echo "  • data/processed/forecast_smoothed.csv    - Optimized schedule"
echo "  • dashboard.html                          - Interactive visualization"
echo ""
echo "📈 Key Reports:"
echo "  • data/reports/ingest_summary.json        - Data quality metrics"
echo "  • data/reports/forecast_baseline.json     - Forecasting analysis"
echo "  • data/reports/smoothing_report.json      - Optimization results"
echo ""
echo "🌐 View Results:"
echo "  Open dashboard.html in your web browser to see the interactive analysis"
echo ""

# Try to open dashboard automatically
if command -v open &> /dev/null; then
    echo "🚀 Opening dashboard..."
    open dashboard.html
elif command -v start &> /dev/null; then
    start dashboard.html
elif command -v xdg-open &> /dev/null; then
    xdg-open dashboard.html
else
    echo "💡 Manually open 'dashboard.html' in your web browser"
fi

echo "✅ Full analysis pipeline completed successfully!"
