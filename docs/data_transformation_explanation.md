Let me explain the `normalized_daily.csv` and why this transformation was absolutely critical for the load balancing project.

## What is `normalized_daily.csv`?

The `normalized_daily.csv` is our **clean, structured dataset** that transforms chaotic Excel planning files into a consistent format suitable for data science and optimization. Each row represents:

**One day × one production line** with aggregated production hours

Here's what each column means:
- `date`: ISO date (2024-01-08)
- `weekday`: Mon/Tue/Wed/Thu/Fri  
- `kw`: Calendar week number
- `line`: Standardized line name (hohl2, hohl3, hohl4, massiv2, massiv3)
- `total_hours`: Total production hours for that day×line (aggregated from multiple segments)
- `personnel_intensive_flag`: Whether personnel-intensive products were produced
- `num_segments`: How many production runs were combined
- `source_file`: Original Excel file for traceability
- `source_type`: Konzept (planned) vs Version1 (actual)
- `capped`: Whether we had to cap hours at 24h/day limit

## Why Did We Extract Data This Way?

### The Original Excel Problem
The raw `.xlsx` files were **completely unusable** for analysis because:

1. **Matrix Layout**: Each file had a complex 2-row header structure:
   ```
   Row 4: Tag | Datum | Hohl 2 | Tag | Datum | Hohl 3
   Row 5: Start | Ende | Min | Soll | Rezeptur | Produkt | Start | Ende | ...
   ```

2. **Side-by-Side Data Blocks**: Multiple production lines crammed into the same sheet horizontally

3. **Inconsistent Naming**: "Hohl 2", "hohl2", "H2" all meaning the same line

4. **Time Segments**: Each day had multiple production runs that needed aggregation

5. **Mixed Data Types**: Times, durations, product codes, dates all mixed together

6. **No Standard Schema**: Different files had slightly different layouts

### What We Accomplished

**From this chaos:**
```
[Excel Matrix Layout]
Tag | Datum | Hohl 2                    | Tag | Datum | Hohl 3
    | Start | Ende | Min | Produkt |     | Start | Ende | Min | Produkt
Mo  | 08.01 | 06:00| 14:30| 510 | Nuss| Mo  | 08.01 | 14:30| 22:30| 480 | Vollmilch
Mo  | 08.01 | 14:30| 22:30| 480 | Edel| ...
```

**To this clean format:**
```csv
date,weekday,kw,line,total_hours,personnel_intensive_flag,num_segments,source_file,source_type,capped
2024-01-08,Mon,2,hohl2,22.5,True,4,WP_H2+H3_KW 02 Konzept.xlsx,Konzept,False
2024-01-08,Mon,2,hohl3,24.0,False,4,WP_H2+H3_KW 02 Konzept.xlsx,Konzept,False
```

## What We'll Use This Data For

### 1. **Forecasting** (Next PoC Step)
- **Weekday Patterns**: "Mondays typically need 22h on Hohl2, 24h on Hohl3"
- **Seasonal Trends**: Production intensity by calendar week
- **Personnel-Intensive Prediction**: Which days need special staffing

### 2. **Load Balancing Optimization**
- **Current State Analysis**: How uneven is the current workload?
- **Constraint Modeling**: Ensure we don't exceed 24h/day per line
- **Personnel Conflicts**: Prevent simultaneous personnel-intensive production
- **Line Utilization**: Identify underused lines for redistribution

### 3. **Smoothing Algorithms**
- **Daily Variability**: Current: some days 15h, others 24h → Target: more consistent load
- **Weekly Patterns**: Smooth Monday peaks by shifting to Tuesday/Wednesday
- **Cross-Line Balancing**: Move work from overloaded lines to idle ones

### 4. **Business Intelligence**
- **KPI Tracking**: Average utilization, peak days, idle time
- **Plan vs Actual**: Compare Konzept (planned) vs Version1 (actual) files
- **Constraint Violations**: Days where we exceeded capacity or rules

## The Power of This Transformation

**Before**: 
- 9 chaotic Excel files
- Manual analysis impossible
- No pattern recognition
- Can't feed into algorithms

**After**: 
- 317 clean, analyzable records
- Ready for pandas/sklearn/optimization libraries
- Consistent schema for all future data
- Perfect input for forecasting models

This normalized dataset is the **foundation** that makes everything else in the PoC possible. Without it, we'd still be staring at Excel matrices trying to manually spot patterns. Now we can build forecasting models, run optimization algorithms, and create dashboards that actually provide insights.

The 2-week PoC timeline was only possible because we invested in getting this data extraction right from the start! [[memory:714207]]