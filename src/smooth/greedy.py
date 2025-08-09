"""
Greedy load smoothing algorithm for production planning.

Takes forecast data and redistributes work across weekdays to:
1. Reduce daily variability in total hours
2. Respect capacity constraints (≤24h per line per day)
3. Ensure at least one line idle per day
4. Avoid simultaneous personnel-intensive production

Simple greedy approach:
- Identify peak days (high total hours)
- Find valley days (low total hours) 
- Transfer work from peaks to valleys respecting constraints
"""

import argparse
import json
import os
from copy import deepcopy
from datetime import datetime
from typing import Dict, List, Any, Tuple, Set

import pandas as pd


def load_forecast_data(csv_path: str) -> pd.DataFrame:
    """Load forecast data."""
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def load_personnel_config(config_path: str) -> Tuple[Set[str], Dict[str, str]]:
    """Load personnel-intensive configuration for constraint checking."""
    import yaml
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        terms = set(config.get('personnel_intensive_terms', []))
        aliases = config.get('aliases', {})
        
        return terms, aliases
    except (FileNotFoundError, yaml.YAMLError):
        print(f"Warning: Could not load personnel config from {config_path}")
        return set(), {}


def calculate_daily_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate total hours per day across all lines."""
    daily_totals = df.groupby('date').agg(
        total_hours=('predicted_hours', 'sum'),
        active_lines=('predicted_hours', lambda x: (x > 0).sum()),
        max_line_hours=('predicted_hours', 'max'),
        personnel_intensive_count=('personnel_intensive_pred', 'sum'),
    ).reset_index()
    
    daily_totals['weekday'] = daily_totals['date'].dt.strftime('%a')
    
    return daily_totals


def check_constraints(df: pd.DataFrame, date: pd.Timestamp) -> Dict[str, bool]:
    """Check if a specific day meets all constraints."""
    day_data = df[df['date'] == date]
    
    # Constraint 1: No line exceeds 24h
    max_line_hours = day_data['predicted_hours'].max()
    capacity_ok = max_line_hours <= 24.0
    
    # Constraint 2: At least one line idle (< 1h considered idle)
    idle_lines = (day_data['predicted_hours'] < 1.0).sum()
    idle_ok = idle_lines >= 1
    
    # Constraint 3: No simultaneous personnel-intensive (only one line can have personnel-intensive)
    personnel_count = day_data['personnel_intensive_pred'].sum()
    personnel_ok = personnel_count <= 1
    
    return {
        'capacity_ok': capacity_ok,
        'idle_ok': idle_ok, 
        'personnel_ok': personnel_ok,
        'all_ok': capacity_ok and idle_ok and personnel_ok,
        'max_line_hours': max_line_hours,
        'idle_lines': idle_lines,
        'personnel_count': personnel_count,
    }


def find_transfer_opportunities(df: pd.DataFrame, target_variance_reduction: float = 0.1) -> List[Dict[str, Any]]:
    """Find opportunities to transfer work from peak to valley days."""
    daily_totals = calculate_daily_totals(df)
    
    # Calculate current variance
    current_variance = daily_totals['total_hours'].var()
    mean_daily = daily_totals['total_hours'].mean()
    
    # Identify peaks (above mean + 0.5*std) and valleys (below mean - 0.5*std)
    std_daily = daily_totals['total_hours'].std()
    peak_threshold = mean_daily + 0.5 * std_daily
    valley_threshold = mean_daily - 0.5 * std_daily
    
    peaks = daily_totals[daily_totals['total_hours'] > peak_threshold]['date'].tolist()
    valleys = daily_totals[daily_totals['total_hours'] < valley_threshold]['date'].tolist()
    
    opportunities = []
    
    for peak_date in peaks:
        for valley_date in valleys:
            # Skip if same weekday (would just shift problem)
            peak_wd = pd.to_datetime(peak_date).strftime('%a')
            valley_wd = pd.to_datetime(valley_date).strftime('%a')
            if peak_wd == valley_wd:
                continue
            
            # Find transferable work on peak day
            peak_data = df[df['date'] == peak_date]
            valley_data = df[df['date'] == valley_date]
            
            # Look for work that can be moved (prefer non-personnel-intensive first)
            transferable = peak_data[
                (peak_data['predicted_hours'] > 4) &  # Minimum viable transfer
                (~peak_data['personnel_intensive_pred'])  # Prefer non-personnel work
            ].copy()
            
            if len(transferable) == 0:
                # Try personnel-intensive if no other options
                transferable = peak_data[peak_data['predicted_hours'] > 4].copy()
            
            for _, work in transferable.iterrows():
                line = work['line']
                hours_to_transfer = min(work['predicted_hours'] * 0.3, 6)  # Transfer up to 30% or 6h
                
                # Check if valley day can accept this work
                valley_line = valley_data[valley_data['line'] == line]
                if len(valley_line) == 0:
                    continue
                
                new_valley_hours = valley_line.iloc[0]['predicted_hours'] + hours_to_transfer
                new_peak_hours = work['predicted_hours'] - hours_to_transfer
                
                # Check constraints
                if new_valley_hours > 24 or new_peak_hours < 1:
                    continue
                
                opportunities.append({
                    'peak_date': peak_date,
                    'valley_date': valley_date,
                    'line': line,
                    'hours_to_transfer': round(hours_to_transfer, 2),
                    'peak_before': round(work['predicted_hours'], 2),
                    'peak_after': round(new_peak_hours, 2),
                    'valley_before': round(valley_line.iloc[0]['predicted_hours'], 2),
                    'valley_after': round(new_valley_hours, 2),
                    'personnel_intensive': work['personnel_intensive_pred'],
                })
    
    # Sort by potential variance reduction (prioritize larger transfers)
    opportunities.sort(key=lambda x: x['hours_to_transfer'], reverse=True)
    
    return opportunities


def apply_smoothing(df: pd.DataFrame, max_transfers: int = 5) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Apply greedy smoothing algorithm."""
    smoothed = df.copy()
    applied_transfers = []
    
    for iteration in range(max_transfers):
        # Find current opportunities
        opportunities = find_transfer_opportunities(smoothed)
        
        if not opportunities:
            print(f"No more transfer opportunities found after {iteration} iterations")
            break
        
        # Apply the best opportunity
        best = opportunities[0]
        
        # Update the dataframe
        peak_mask = (smoothed['date'] == best['peak_date']) & (smoothed['line'] == best['line'])
        valley_mask = (smoothed['date'] == best['valley_date']) & (smoothed['line'] == best['line'])
        
        smoothed.loc[peak_mask, 'predicted_hours'] = best['peak_after']
        smoothed.loc[valley_mask, 'predicted_hours'] = best['valley_after']
        
        # Check constraints after transfer
        peak_constraints = check_constraints(smoothed, best['peak_date'])
        valley_constraints = check_constraints(smoothed, best['valley_date'])
        
        if not peak_constraints['all_ok'] or not valley_constraints['all_ok']:
            print(f"Transfer would violate constraints, skipping: {best}")
            # Revert the change
            smoothed.loc[peak_mask, 'predicted_hours'] = best['peak_before']
            smoothed.loc[valley_mask, 'predicted_hours'] = best['valley_before']
            continue
        
        applied_transfers.append({
            **best,
            'iteration': iteration + 1,
            'peak_constraints': peak_constraints,
            'valley_constraints': valley_constraints,
        })
        
        print(f"Applied transfer {iteration + 1}: {best['hours_to_transfer']:.1f}h from {best['peak_date']} to {best['valley_date']} on {best['line']}")
    
    return smoothed, applied_transfers


def calculate_improvement_metrics(original: pd.DataFrame, smoothed: pd.DataFrame) -> Dict[str, Any]:
    """Calculate metrics showing improvement from smoothing."""
    
    orig_daily = calculate_daily_totals(original)
    smooth_daily = calculate_daily_totals(smoothed)
    
    metrics = {
        'variance_reduction': {
            'original_variance': round(orig_daily['total_hours'].var(), 2),
            'smoothed_variance': round(smooth_daily['total_hours'].var(), 2),
            'reduction_pct': round(100 * (1 - smooth_daily['total_hours'].var() / orig_daily['total_hours'].var()), 1),
        },
        'daily_range': {
            'original_range': round(orig_daily['total_hours'].max() - orig_daily['total_hours'].min(), 2),
            'smoothed_range': round(smooth_daily['total_hours'].max() - smooth_daily['total_hours'].min(), 2),
            'reduction': round((orig_daily['total_hours'].max() - orig_daily['total_hours'].min()) - 
                             (smooth_daily['total_hours'].max() - smooth_daily['total_hours'].min()), 2),
        },
        'constraint_violations': {
            'original': sum(1 for date in orig_daily['date'] if not check_constraints(original, date)['all_ok']),
            'smoothed': sum(1 for date in smooth_daily['date'] if not check_constraints(smoothed, date)['all_ok']),
        },
        'weekday_comparison': {}
    }
    
    # Per-weekday comparison
    for weekday in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
        orig_wd = orig_daily[orig_daily['weekday'] == weekday]['total_hours']
        smooth_wd = smooth_daily[smooth_daily['weekday'] == weekday]['total_hours']
        
        if len(orig_wd) > 0 and len(smooth_wd) > 0:
            metrics['weekday_comparison'][weekday] = {
                'original_avg': round(orig_wd.mean(), 2),
                'smoothed_avg': round(smooth_wd.mean(), 2),
                'change': round(smooth_wd.mean() - orig_wd.mean(), 2),
            }
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Apply greedy smoothing to production forecast")
    parser.add_argument("--input", default="data/processed/forecast_baseline.csv", 
                       help="Input forecast CSV file")
    parser.add_argument("--output", default="data/processed/forecast_smoothed.csv", 
                       help="Output smoothed CSV")
    parser.add_argument("--report", default="data/reports/smoothing_report.json", 
                       help="Output report JSON")
    parser.add_argument("--max-transfers", type=int, default=5, 
                       help="Maximum number of transfers to apply")
    parser.add_argument("--personnel-config", default="config/personnel_intensive.yml", 
                       help="Personnel-intensive config file")
    
    args = parser.parse_args()
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    
    print(f"Loading forecast data from {args.input}")
    forecast = load_forecast_data(args.input)
    print(f"Loaded {len(forecast)} forecast records")
    
    print("Analyzing current load distribution...")
    daily_totals = calculate_daily_totals(forecast)
    print(f"Daily total hours: mean={daily_totals['total_hours'].mean():.1f}, std={daily_totals['total_hours'].std():.1f}")
    
    print(f"Applying greedy smoothing (max {args.max_transfers} transfers)...")
    smoothed, transfers = apply_smoothing(forecast, args.max_transfers)
    
    print("Calculating improvement metrics...")
    metrics = calculate_improvement_metrics(forecast, smoothed)
    
    # Save smoothed forecast
    smoothed.to_csv(args.output, index=False)
    print(f"Saved smoothed forecast to {args.output}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'input_file': args.input,
            'max_transfers': args.max_transfers,
        },
        'applied_transfers': transfers,
        'improvement_metrics': metrics,
        'outputs': {
            'smoothed_csv': args.output,
            'report_json': args.report,
        }
    }
    
    with open(args.report, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Saved report to {args.report}")
    
    # Print summary
    print("\n=== SMOOTHING RESULTS ===")
    print(f"Applied {len(transfers)} transfers")
    print(f"Variance reduction: {metrics['variance_reduction']['reduction_pct']}%")
    print(f"Daily range reduction: {metrics['daily_range']['reduction']:.1f} hours")
    print(f"Constraint violations: {metrics['constraint_violations']['original']} → {metrics['constraint_violations']['smoothed']}")
    
    if len(transfers) > 0:
        print("\nTransfers applied:")
        for t in transfers:
            print(f"  {t['iteration']}: {t['hours_to_transfer']}h from {t['peak_date']} to {t['valley_date']} on {t['line']}")
    else:
        print("No transfers were applied (no opportunities found or constraints prevented transfers)")


if __name__ == "__main__":
    main()
