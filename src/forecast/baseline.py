"""
Baseline forecasting for production load balancing.

Simple weekday average approach:
- Calculate historical average hours per weekday per line
- Use this as prediction for future weeks
- Handle personnel-intensive flagging with historical rates
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

import pandas as pd


def load_normalized_data(csv_path: str) -> pd.DataFrame:
    """Load and validate normalized daily data."""
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Validate required columns
    required_cols = ['date', 'weekday', 'line', 'total_hours', 'personnel_intensive_flag']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return df


def calculate_weekday_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate average hours per weekday per line."""
    # Group by weekday and line, calculate statistics
    averages = df.groupby(['weekday', 'line']).agg(
        avg_hours=('total_hours', 'mean'),
        std_hours=('total_hours', 'std'),
        count_days=('total_hours', 'count'),
        personnel_intensive_rate=('personnel_intensive_flag', 'mean'),
        min_hours=('total_hours', 'min'),
        max_hours=('total_hours', 'max'),
    ).reset_index()
    
    # Fill NaN std with 0 (happens when only 1 observation)
    averages['std_hours'] = averages['std_hours'].fillna(0)
    
    return averages


def generate_forecast(averages: pd.DataFrame, start_date: str, num_weeks: int = 4) -> pd.DataFrame:
    """Generate forecast for future weeks using weekday averages."""
    start_dt = pd.to_datetime(start_date)
    
    # Generate date range
    dates = pd.date_range(start=start_dt, periods=num_weeks * 5, freq='D')
    # Filter to weekdays only
    weekdays = dates[dates.dayofweek < 5]  # Monday=0, Friday=4
    
    forecast_records = []
    
    for date in weekdays:
        weekday = date.strftime('%a')  # Mon, Tue, Wed, Thu, Fri
        
        # Get predictions for each line on this weekday
        day_averages = averages[averages['weekday'] == weekday]
        
        for _, row in day_averages.iterrows():
            line = row['line']
            predicted_hours = row['avg_hours']
            personnel_prob = row['personnel_intensive_rate']
            
            # Simple rule: if personnel rate > 50%, predict True
            personnel_intensive_pred = personnel_prob > 0.5
            
            forecast_records.append({
                'date': date.date(),
                'weekday': weekday,
                'kw': date.isocalendar()[1],  # ISO week number
                'line': line,
                'predicted_hours': round(predicted_hours, 2),
                'personnel_intensive_pred': personnel_intensive_pred,
                'personnel_intensive_rate': round(personnel_prob, 3),
                'confidence': 'high' if row['count_days'] >= 3 else 'low',
                'historical_std': round(row['std_hours'], 2),
                'historical_count': int(row['count_days']),
            })
    
    return pd.DataFrame(forecast_records)


def validate_forecast(forecast: pd.DataFrame) -> Dict[str, Any]:
    """Run basic validation checks on forecast."""
    validation = {
        'total_forecast_days': len(forecast['date'].unique()),
        'lines_covered': sorted(forecast['line'].unique().tolist()),
        'avg_daily_total_hours': forecast.groupby('date')['predicted_hours'].sum().mean(),
        'max_daily_total_hours': forecast.groupby('date')['predicted_hours'].sum().max(),
        'min_daily_total_hours': forecast.groupby('date')['predicted_hours'].sum().min(),
        'days_over_capacity': 0,  # Will check line-level capacity
        'personnel_intensive_days': forecast.groupby('date')['personnel_intensive_pred'].any().sum(),
    }
    
    # Check for line-level capacity violations (>24h per day per line)
    line_daily = forecast.groupby(['date', 'line'])['predicted_hours'].sum()
    over_capacity = line_daily[line_daily > 24]
    validation['days_over_capacity'] = len(over_capacity)
    validation['capacity_violations'] = over_capacity.to_dict() if len(over_capacity) > 0 else {}
    
    return validation


def create_comparison_summary(historical: pd.DataFrame, forecast: pd.DataFrame) -> Dict[str, Any]:
    """Compare historical patterns with forecast predictions."""
    # Historical weekday patterns
    hist_weekday = historical.groupby('weekday')['total_hours'].agg(['mean', 'std', 'count'])
    
    # Forecast weekday patterns  
    forecast_weekday = forecast.groupby('weekday')['predicted_hours'].agg(['mean', 'std', 'count'])
    
    comparison = {
        'historical_period': {
            'start_date': historical['date'].min().strftime('%Y-%m-%d'),
            'end_date': historical['date'].max().strftime('%Y-%m-%d'),
            'total_days': len(historical),
            'unique_days': len(historical['date'].unique()),
        },
        'forecast_period': {
            'start_date': forecast['date'].min().strftime('%Y-%m-%d'),
            'end_date': forecast['date'].max().strftime('%Y-%m-%d'),
            'total_days': len(forecast),
            'unique_days': len(forecast['date'].unique()),
        },
        'weekday_comparison': {}
    }
    
    for weekday in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
        if weekday in hist_weekday.index and weekday in forecast_weekday.index:
            comparison['weekday_comparison'][weekday] = {
                'historical_avg': round(hist_weekday.loc[weekday, 'mean'], 2),
                'forecast_avg': round(forecast_weekday.loc[weekday, 'mean'], 2),
                'historical_std': round(hist_weekday.loc[weekday, 'std'], 2),
                'historical_count': int(hist_weekday.loc[weekday, 'count']),
            }
    
    return comparison


def main():
    parser = argparse.ArgumentParser(description="Generate baseline forecast using weekday averages")
    parser.add_argument("--input", default="data/processed/normalized_daily.csv", 
                       help="Input normalized CSV file")
    parser.add_argument("--start-date", required=True, 
                       help="Forecast start date (YYYY-MM-DD)")
    parser.add_argument("--weeks", type=int, default=4, 
                       help="Number of weeks to forecast")
    parser.add_argument("--output", default="data/processed/forecast_baseline.csv", 
                       help="Output forecast CSV")
    parser.add_argument("--report", default="data/reports/forecast_baseline.json", 
                       help="Output report JSON")
    
    args = parser.parse_args()
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    
    print(f"Loading historical data from {args.input}")
    historical = load_normalized_data(args.input)
    print(f"Loaded {len(historical)} historical records from {historical['date'].min()} to {historical['date'].max()}")
    
    print("Calculating weekday averages...")
    averages = calculate_weekday_averages(historical)
    print(f"Calculated averages for {len(averages)} weekday×line combinations")
    
    print(f"Generating {args.weeks}-week forecast starting {args.start_date}...")
    forecast = generate_forecast(averages, args.start_date, args.weeks)
    print(f"Generated forecast with {len(forecast)} predictions")
    
    print("Running validation...")
    validation = validate_forecast(forecast)
    
    print("Creating comparison summary...")
    comparison = create_comparison_summary(historical, forecast)
    
    # Save forecast
    forecast.to_csv(args.output, index=False)
    print(f"Saved forecast to {args.output}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'input_file': args.input,
            'start_date': args.start_date,
            'forecast_weeks': args.weeks,
        },
        'weekday_averages': averages.to_dict('records'),
        'validation': validation,
        'comparison': comparison,
        'outputs': {
            'forecast_csv': args.output,
            'report_json': args.report,
        }
    }
    
    with open(args.report, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Saved report to {args.report}")
    
    # Print summary
    print("\n=== FORECAST SUMMARY ===")
    print(f"Forecast period: {comparison['forecast_period']['start_date']} to {comparison['forecast_period']['end_date']}")
    print(f"Average daily total: {validation['avg_daily_total_hours']:.1f} hours")
    print(f"Personnel-intensive days: {validation['personnel_intensive_days']}")
    print(f"Capacity violations: {validation['days_over_capacity']}")
    
    if validation['capacity_violations']:
        print("⚠️  Capacity violations detected:")
        for (date, line), hours in validation['capacity_violations'].items():
            print(f"  {date} {line}: {hours:.1f}h > 24h")
    else:
        print("✅ No capacity violations detected")


if __name__ == "__main__":
    main()
