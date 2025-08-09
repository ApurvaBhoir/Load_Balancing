# 🚀 Quick Start Guide - Load Balancing PoC

## ⚡ 30-Second Reproduction

```bash
# 1. Validate setup
python validate_setup.py

# 2. Run complete analysis (one command)
./run_full_analysis.sh

# 3. View results
open dashboard.html
```

## 📋 What You Get

After running the analysis, you'll have:

### 🔢 **Data Outputs**
- `normalized_daily.csv` - Clean historical production data
- `forecast_baseline.csv` - Future workload predictions  
- `forecast_smoothed.csv` - Optimized production schedule
- `dashboard.html` - Interactive visualization

### 📊 **Key Insights**
- **Load Distribution**: How work varies across weekdays
- **Capacity Utilization**: Which lines are over/under-used
- **Constraint Compliance**: Personnel conflicts, capacity violations
- **Forecasting Accuracy**: Historical vs predicted patterns

### 🎯 **Business Value**
- **Identify bottlenecks** in current planning
- **Predict future workload** using historical patterns  
- **Optimize scheduling** to smooth daily variations
- **Monitor compliance** with operational constraints

## 🔍 Understanding the Results

### Dashboard Sections

**📈 Timeline Chart**
- Blue line = Historical actual hours
- Dashed line = Forecast predictions
- Look for: Seasonal patterns, day-to-day variability

**📅 Weekday Patterns**  
- Compares historical vs forecast by weekday
- Red bars = Historical averages
- Blue bars = Predicted averages
- Look for: Monday peaks, Friday valleys

**🏭 Line Utilization**
- Radar chart showing capacity usage per line
- Look for: Underutilized lines, capacity bottlenecks

**📋 Summary Table**
- Detailed weekday comparison
- Shows differences between historical and forecast
- Look for: Consistent patterns, unexpected changes

### Key Metrics to Watch

**✅ Good Signs:**
- Low daily variance (< 3 hours std dev)
- No capacity violations (all lines ≤ 24h/day)
- Consistent weekday patterns
- High forecast confidence

**⚠️ Warning Signs:**
- High daily variance (> 5 hours std dev)  
- Multiple capacity violations
- Erratic weekday patterns
- Low forecast confidence

## 🛠️ Troubleshooting

### Common Issues

**"No files found"**
```bash
# Check data structure
ls -la data/2024/H2_H3/*.xlsx
```

**"Module not found"**
```bash
# Install dependencies
pip install pandas openpyxl pyyaml
```

**"No header row found"**
```bash
# Excel files may have different format
# Check with schema probe:
python -m src.etl.schema_probe --areas H2_H3 --per-area-limit 1
```

### Getting Help

1. **Run validation first**: `python validate_setup.py`
2. **Check logs**: Look in `logs/` directory for detailed error messages
3. **Verify data**: Ensure Excel files match expected matrix layout
4. **Check outputs**: Validate intermediate CSV files are reasonable

## 📚 Next Steps

### Expand Analysis
```bash
# Process more weeks of data
python -m src.etl.ingest --max-files 20

# Generate longer forecast
python -m src.forecast.baseline --weeks 8

# Try more aggressive smoothing
python -m src.smooth.greedy --max-transfers 10
```

### Monitor in Production
- Set up automated daily runs
- Add constraint violation alerts
- Create weekly summary reports
- Monitor forecast accuracy over time

## 🎯 Success Criteria

Your reproduction is successful if:

- ✅ Dashboard loads without errors
- ✅ Charts show meaningful data patterns
- ✅ No capacity violations in forecast
- ✅ Weekday patterns make business sense
- ✅ Historical vs forecast alignment is reasonable

## 📞 Support

If you encounter issues:

1. **Check prerequisites**: Python 3.8+, dependencies installed
2. **Validate data format**: Excel files should have matrix layout
3. **Review logs**: Error messages usually point to the root cause
4. **Compare with reference**: Expected outputs are documented

---

*The PoC demonstrates feasibility and provides a foundation for production deployment. Results should be validated with domain experts before operational use.*
