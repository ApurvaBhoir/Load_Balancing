# Ritter Sport Production Planner - User Guide

## 🎯 Overview

The Ritter Sport Production Load Balancing Decision Support Tool helps production planners create optimized weekly schedules. Instead of manual planning based on experience, the tool uses historical data and constraint-aware optimization to generate balanced production plans.

## 🚀 Quick Start

### Launch the Application
```bash
# From the project directory
python run_planner_interface.py
```
Or manually:
```bash
conda activate py310
streamlit run src/interface/planner_app.py
```

The application will open in your browser at `http://localhost:8501`

## 📋 How to Use

### Step 1: Input Production Requirements

1. **Select Planning Week**: Choose the Monday of the week you want to plan
2. **Enter Product Demands**: Fill in the table with:
   - Product types (select from dropdown)
   - Total hours required for each product
   - Priority level (High/Medium/Low)
   - Deadline (Monday through Friday)
3. **Use "Load Sample Scenario"** for demonstration purposes

### Step 2: Configure Constraints

1. **Line Availability**: Uncheck any lines that are down for maintenance
2. **Constraint Settings**:
   - ✅ At least one line idle per day (recommended)
   - ✅ No simultaneous personnel-intensive sorts (recommended)
   - Set maximum hours per line per day (default: 24h)
3. **Additional Factors**: Optional energy considerations and distribution preferences

### Step 3: Generate Optimized Schedule

1. Click **"🔮 Generate Forecast & Optimize"**
2. Wait for processing (typically <30 seconds)
3. View the optimization results and performance metrics

### Step 4: Review and Export Results

1. **Review the schedule**: Check the weekly calendar and line utilization
2. **Verify constraints**: Ensure all operational rules are satisfied
3. **Download results**: Click "📥 Download CSV" to export the schedule
4. **Make adjustments**: Use "🔙 Modify Inputs" to change requirements if needed

## 📊 Understanding the Results

### Key Metrics
- **Load Variance Reduction**: How much more balanced the schedule is compared to manual planning
- **Constraint Compliance**: Percentage of operational rules satisfied (aim for 100%)
- **Average Active Lines**: How many production lines are working per day
- **Total Production Hours**: Sum of all scheduled production for the week

### Visualizations
- **Daily Load Chart**: Shows production hours for each day of the week
- **Line Utilization**: Stacked bars showing which lines are working when
- **Constraint Compliance**: Green checkmarks for satisfied constraints

### Schedule Table
The main output showing:
- Date and weekday
- Hours assigned to each production line (hohl2, hohl3, hohl4, massiv2, massiv3)
- Daily totals and active line counts

## ⚙️ Configuration Options

### Line Availability
- Check/uncheck boxes to indicate which lines are available for production
- Unavailable lines will have zero hours assigned

### Constraint Settings
- **Idle Line Constraint**: Ensures at least one line remains idle each day for maintenance/flexibility
- **Personnel-Intensive Constraint**: Prevents multiple personnel-intensive products from running simultaneously
- **Max Daily Hours**: Caps the maximum operating hours for any single line per day

## 🎯 Best Practices

### Input Guidelines
1. **Realistic Requirements**: Enter achievable production targets based on historical capacity
2. **Clear Priorities**: Use High priority for critical customer orders
3. **Reasonable Deadlines**: Allow sufficient time for production completion
4. **Check Totals**: Verify total hours don't exceed capacity (typically <120h/day across all lines)

### Interpreting Results
1. **Variance Reduction**: Look for 10-20% improvement over manual planning
2. **Constraint Violations**: Address any violations before implementing the schedule
3. **Line Balance**: Ensure no single line is consistently overloaded
4. **Daily Distribution**: Aim for relatively even distribution across the week

### Implementation Tips
1. **Export Schedule**: Always download the CSV for implementation
2. **Review with Team**: Share results with floor managers before implementation
3. **Monitor Performance**: Track actual vs. planned hours during execution
4. **Iterate**: Use feedback to improve future planning sessions

## 🛠️ Troubleshooting

### Common Issues

**"Total hours exceed capacity"**
- Reduce product quantities or extend deadlines
- Check if all lines are marked as available

**"No optimization improvement"**
- Requirements may already be well-balanced
- Try adjusting priorities or deadlines for more flexibility

**"Constraint violations detected"**
- Review personnel-intensive product combinations
- Adjust line availability or daily hour limits

**App won't start**
- Ensure conda py310 environment is activated
- Check that all required data files exist in `data/processed/`

### Getting Help
1. Check the logs in the `logs/` directory
2. Review the data quality report in `data/reports/`
3. Verify all input files are properly formatted
4. Contact the technical team for persistent issues

## 📈 Success Metrics

### What to Expect
- **15-20% reduction** in daily load variance
- **100% constraint compliance** for operational rules
- **<5 minutes** to complete planning workflow
- **Actionable schedules** that floor managers can implement

### Measuring Impact
- Compare overtime hours before/after implementation
- Track employee satisfaction with more balanced workloads
- Monitor equipment utilization improvements
- Measure planning time reduction

---

*This tool is a Proof of Concept focused on demonstrating value through core features. Additional functionality will be added based on user feedback and business requirements.*
