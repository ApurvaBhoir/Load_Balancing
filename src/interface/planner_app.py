"""
Ritter Sport Production Load Balancing - Planner Interface

A decision support tool that helps production planners optimize weekly load distribution
across 5 production lines, replacing manual educated guesses with data-driven forecasting
and constraint-aware optimization.

Usage: streamlit run src/interface/planner_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import json
import os
import tempfile
from typing import Dict, List, Any, Optional

# Import our existing services
try:
    from .services import (
        load_historical_data,
        get_available_products,
        run_forecast,
        run_optimization,
        calculate_metrics,
        export_schedule
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from services import (
        load_historical_data,
        get_available_products,
        run_forecast,
        run_optimization,
        calculate_metrics,
        export_schedule,
        validate_input_requirements
    )


def init_session_state():
    """Initialize session state variables."""
    if 'planning_step' not in st.session_state:
        st.session_state.planning_step = 'input'
    if 'requirements' not in st.session_state:
        st.session_state.requirements = {}
    if 'constraints' not in st.session_state:
        st.session_state.constraints = {}
    if 'forecast_results' not in st.session_state:
        st.session_state.forecast_results = None
    if 'optimization_results' not in st.session_state:
        st.session_state.optimization_results = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False


def reset_processing_state():
    """Reset processing-related session state."""
    st.session_state.processing_complete = False
    st.session_state.forecast_results = None
    st.session_state.optimization_results = None
    st.session_state.metrics = None


def render_header():
    """Render the application header."""
    st.set_page_config(
        page_title="Ritter Sport Production Planner",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.title("Ritter Sport Production Planner")
    st.subheader("Decision Support Tool for Production Planners")
    
    # Progress indicator with clickable navigation
    steps = ["Input", "Forecast", "Optimize", "Results"]
    step_keys = ['input', 'forecast', 'optimize', 'results']
    current_step_idx = {'input': 0, 'forecast': 1, 'optimize': 1, 'results': 3}.get(
        st.session_state.planning_step, 0
    )
    
    cols = st.columns(4)
    for i, (col, step, step_key) in enumerate(zip(cols, steps, step_keys)):
        with col:
            if i == current_step_idx:
                st.markdown(f"**{step}**")
            elif i < current_step_idx:
                # Completed steps - make them clickable
                if step_key == 'input' and st.button(f"{step}", key=f"nav_{step_key}", help="Click to return to input"):
                    st.session_state.planning_step = 'input'
                    reset_processing_state()
                    st.rerun()
                elif step_key == 'results' and 'optimization_results' in st.session_state and st.button(f"{step}", key=f"nav_{step_key}", help="Click to view results"):
                    st.session_state.planning_step = 'results'
                    st.rerun()
                else:
                    st.markdown(f"{step}")
            else:
                # Future steps - not yet available
                st.markdown(f"{step}")


def render_input_forms():
    """Render the input forms for requirements and constraints."""
    st.header("Production Planning Input")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("A) Production Requirements")
        st.caption("Enter the production demands defined by managers for the upcoming week.")
        
        # Load historical data to get available products
        try:
            available_products = get_available_products()
        except Exception as e:
            st.error(f"Could not load historical data: {e}")
            available_products = ["100g Knusperkeks", "100g Waffel", "100g Marzipan", "Mini Knusperkeks", "Standard"]
        
        # Planning week selection
        st.write("**Planning Week**")
        planning_date = st.date_input(
            "Select Monday of the week to plan",
            value=date.today() + timedelta(days=(7 - date.today().weekday())),  # Next Monday
            help="Choose the Monday of the week you want to create a production plan for"
        )
        
        # Product requirements table
        st.write("**Product Demands**")
        
        # Create default dataframe for data editor
        default_products = available_products[:5] if len(available_products) >= 5 else available_products
        default_df = pd.DataFrame({
            'Product': default_products,
            'Quantity (hours)': [0.0] * len(default_products),
            'Priority': ['Medium'] * len(default_products),
            'Deadline': ['Friday'] * len(default_products)
        })
        
        # Editable dataframe for requirements - Streamlit automatically manages state via key
        requirements_df = st.data_editor(
            default_df,
            column_config={
                "Product": st.column_config.SelectboxColumn(
                    "Product Type",
                    help="Select the chocolate product to be produced",
                    options=available_products,
                    required=True,
                ),
                "Quantity (hours)": st.column_config.NumberColumn(
                    "Total Hours Required",
                    help="Total production hours needed for this product",
                    min_value=0.0,
                    max_value=120.0,  # 5 lines * 24h max
                    step=0.5,
                    format="%.1f h"
                ),
                "Priority": st.column_config.SelectboxColumn(
                    "Priority Level",
                    help="Production priority",
                    options=["High", "Medium", "Low"],
                    required=True,
                ),
                "Deadline": st.column_config.SelectboxColumn(
                    "Deadline",
                    help="Latest completion day",
                    options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    required=True,
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            key="requirements_editor"
        )
        
        # The st.data_editor already returns the edited DataFrame directly
        # No need to access session state - the return value IS the current edited data
        
        # Store for use by other components  
        st.session_state.requirements_df = requirements_df
        
        # Validation - calculate total and show early feedback
        # Handle case where DataFrame might be empty or missing columns
        if requirements_df is not None and not requirements_df.empty and 'Quantity (hours)' in requirements_df.columns:
            total_hours = requirements_df['Quantity (hours)'].sum()
        else:
            total_hours = 0.0
        
        # Capacity gauge calculation (will be updated after constraints are set)
        st.session_state.current_total_hours = total_hours
        
        # Store current requirements for validation
        current_requirements = {
            'total_hours': total_hours,
            'products': requirements_df.to_dict('records') if requirements_df is not None and not requirements_df.empty else [],
            'planning_date': datetime.now().date()
        }
        
        # Store current constraints (we'll get these from the second column)
        st.session_state.current_requirements = current_requirements
    
    with col2:
        st.subheader("B) Constraints & Factors")
        
        # Line availability
        st.write("**Line Availability**")
        line_availability = {}
        lines = ["hohl2", "hohl3", "hohl4", "massiv2", "massiv3"]
        
        for line in lines:
            line_availability[line] = st.checkbox(
                f"{line.capitalize()} available",
                value=True,
                help=f"Uncheck if {line} is down for maintenance"
            )
        
        # Constraint overrides
        st.write("**Constraint Settings**")
        
        enforce_idle_line = st.checkbox(
            "At least one line idle per day",
            value=True,
            help="Ensure at least one production line remains idle each day"
        )
        
        enforce_personnel_intensive = st.checkbox(
            "No simultaneous personnel-intensive sorts",
            value=True,
            help="Prevent multiple personnel-intensive products from running simultaneously"
        )
        
        max_daily_hours = st.number_input(
            "Max hours per line per day",
            min_value=8.0,
            max_value=24.0,
            value=24.0,
            step=0.5,
            help="Maximum operating hours for any single line per day"
        )
        
        # Additional factors
        st.write("**Additional Factors**")
        
        energy_consideration = st.checkbox(
            "Consider energy costs",
            value=False,
            help="Factor in peak energy cost periods (experimental)"
        )
        
        prefer_smooth_distribution = st.checkbox(
            "Prefer smooth daily distribution",
            value=True,
            help="Prioritize even load distribution across the week"
        )
        
        st.write("**Special Notes**")
        special_notes = st.text_area(
            "Additional planning considerations",
            placeholder="Any special requirements, customer deadlines, or other factors to consider...",
            height=100
        )
    
    # Store inputs in session state
    st.session_state.requirements = {
        'planning_date': planning_date,
        'products': requirements_df.to_dict('records'),
        'total_hours': total_hours
    }
    
    st.session_state.constraints = {
        'line_availability': line_availability,
        'enforce_idle_line': enforce_idle_line,
        'enforce_personnel_intensive': enforce_personnel_intensive,
        'max_daily_hours': max_daily_hours,
        'energy_consideration': energy_consideration,
        'prefer_smooth_distribution': prefer_smooth_distribution,
        'special_notes': special_notes
    }
    
    # Real-time validation
    if hasattr(st.session_state, 'current_requirements'):
        validation_result = validate_input_requirements(
            st.session_state.current_requirements, 
            st.session_state.constraints
        )
        
        # Display validation results
        if validation_result['errors']:
            st.error("🚨 **Input Issues Found**")
            for error in validation_result['errors']:
                st.error(f"**{error['message']}**\n\n💡 {error['suggestion']}")
        
        if validation_result['warnings']:
            st.warning("⚠️ **Recommendations**")
            for warning in validation_result['warnings']:
                st.warning(f"**{warning['message']}**\n\n💡 {warning['suggestion']}")
        
        if not validation_result['errors'] and not validation_result['warnings']:
            st.success("✅ **Input validation passed** - Ready for optimization!")
        
        # Store validation for later use
        st.session_state.input_validation = validation_result
    
    # Dynamic Capacity Gauge
    st.markdown("---")
    st.subheader("📊 Capacity Overview")
    
    if hasattr(st.session_state, 'current_total_hours'):
        total_hours = st.session_state.current_total_hours
        max_daily_hours = st.session_state.constraints.get('max_daily_hours', 24.0)
        
        # Calculate capacities based on constraints
        line_availability = st.session_state.constraints.get('line_availability', {})
        available_lines = sum(1 for available in line_availability.values() if available)
        enforce_idle = st.session_state.constraints.get('enforce_idle_line', True)
        
        # Effective lines per day (subtract 1 if idle line required)
        effective_lines_per_day = available_lines - (1 if enforce_idle else 0)
        max_weekly_capacity = effective_lines_per_day * max_daily_hours * 5  # 5 weekdays
        
        # Calculate utilization percentages
        weekly_utilization = (total_hours / max_weekly_capacity * 100) if max_weekly_capacity > 0 else 0
        
        # Personnel-intensive capacity check
        personnel_intensive_hours = 0
        for product in st.session_state.current_requirements.get('products', []):
            product_name = product.get('Product', '').lower()
            if any(term in product_name for term in ['knusper', 'waffel', 'crisp', 'nuss']):
                personnel_intensive_hours += product.get('Quantity (hours)', 0)
        
        max_personnel_capacity = max_daily_hours * 5  # 1 line * 5 days
        personnel_utilization = (personnel_intensive_hours / max_personnel_capacity * 100) if max_personnel_capacity > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Hours Requested", 
                f"{total_hours:.1f}h",
                help=f"Out of {max_weekly_capacity:.0f}h maximum weekly capacity"
            )
            
            # Weekly capacity gauge
            
            st.progress(min(weekly_utilization / 100, 1.0))
            st.caption(f"Weekly Capacity: {weekly_utilization:.1f}% used")
        
        with col2:
            st.metric(
                "Available Production Lines", 
                f"{available_lines}",
                help=f"Effective lines per day: {effective_lines_per_day} (1 kept idle)" if enforce_idle else f"All {available_lines} lines can be used"
            )
            
            # Line availability gauge
            line_utilization = (available_lines / 5 * 100)  # Out of 5 total lines
            st.progress(line_utilization / 100)
            st.caption(f"Line Availability: {line_utilization:.0f}% of total lines")
        
        with col3:
            if personnel_intensive_hours > 0:
                st.metric(
                    "Personnel-Intensive Hours", 
                    f"{personnel_intensive_hours:.1f}h",
                    help=f"Out of {max_personnel_capacity:.0f}h maximum (1 line constraint)"
                )
                
                # Personnel gauge
                
                st.progress(min(personnel_utilization / 100, 1.0))
                st.caption(f"Personnel Capacity: {personnel_utilization:.1f}% used")
            else:
                st.metric("Personnel-Intensive Hours", "0h", help="No personnel-intensive products detected")
                st.progress(0.0)
                st.caption("Personnel Capacity: 0% used")
        
        # Capacity warnings
        if weekly_utilization > 100:
            st.error(f"⚠️ **Capacity exceeded by {weekly_utilization - 100:.1f}%** - Reduce requirements or extend timeline")
        elif weekly_utilization > 85:
            st.warning(f"⚠️ **High utilization ({weekly_utilization:.1f}%)** - Consider adding buffer time")
        elif weekly_utilization > 0:
            st.success(f"✅ **Capacity utilization looks good ({weekly_utilization:.1f}%)**")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("Run Forecast & Optimization", type="primary", use_container_width=True):
            if total_hours == 0:
                st.error("Please enter at least one product requirement")
            else:
                # Reset processing state and move to forecast step
                reset_processing_state()
                st.session_state.planning_step = 'forecast'
                st.rerun()
    
    with col3:
        if st.button("Load Sample Scenario", use_container_width=True):
            load_sample_scenario()


def load_sample_scenario():
    """Load a sample planning scenario for demonstration."""
    # Sample data based on historical patterns
    sample_products = [
        {"Product": "100g Knusperkeks", "Quantity (hours)": 45.0, "Priority": "High", "Deadline": "Wednesday"},
        {"Product": "Standard", "Quantity (hours)": 60.0, "Priority": "Medium", "Deadline": "Thursday"},
        {"Product": "100g Waffel", "Quantity (hours)": 35.0, "Priority": "Medium", "Deadline": "Friday"},
        {"Product": "100g Marzipan", "Quantity (hours)": 25.0, "Priority": "Low", "Deadline": "Friday"},
    ]
    
    st.session_state.requirements_df = pd.DataFrame(sample_products)
    st.success("Sample scenario loaded. Review the requirements and click 'Run Forecast & Optimization'")
    st.rerun()


def render_processing():
    """Render the processing step with progress indicators."""
    st.header("Generating Forecast and Optimization")
    
    # Check if we should run processing
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    if not st.session_state.processing_complete:
        # Show processing in progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Load historical data and generate forecast
            status_text.text("Analyzing historical patterns...")
            progress_bar.progress(25)
            
            forecast_results = run_forecast(
                st.session_state.requirements,
                st.session_state.constraints
            )
            
            # Step 2: Run optimization
            status_text.text("Optimizing schedule with constraints...")
            progress_bar.progress(50)
            
            optimization_results = run_optimization(
                forecast_results,
                st.session_state.requirements,
                st.session_state.constraints
            )
            
            # Step 3: Calculate metrics
            status_text.text("Calculating performance metrics...")
            progress_bar.progress(75)
            
            metrics = calculate_metrics(forecast_results, optimization_results)
            
            # Step 4: Complete
            status_text.text("Processing complete")
            progress_bar.progress(100)
            
            # Store results
            st.session_state.forecast_results = forecast_results
            st.session_state.optimization_results = optimization_results
            st.session_state.metrics = metrics
            st.session_state.processing_complete = True
            
            # Force rerun to show results
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")
            st.exception(e)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔙 Back to Input", type="secondary"):
                    st.session_state.planning_step = 'input'
                    st.rerun()
            with col2:
                if st.button("🔄 Try Again"):
                    st.rerun()
    else:
        # Processing is complete, show results and navigation
        st.success("🎉 Optimization complete! Generated optimized schedule with constraint compliance.")
        
        if 'metrics' in st.session_state:
            metrics = st.session_state.metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Load Variance Reduction", f"{metrics.get('variance_reduction', 0):.1f}%")
            with col2:
                st.metric("Constraint Compliance", f"{metrics.get('constraint_compliance', 0):.0f}%")
            with col3:
                st.metric("Active Lines per Day", f"{metrics.get('avg_active_lines', 0):.1f}")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🔙 Back to Input", type="secondary"):
                st.session_state.planning_step = 'input'
                reset_processing_state()
                st.rerun()
        with col3:
            if st.button("📊 View Results", type="primary"):
                st.session_state.planning_step = 'results'
                st.rerun()


def render_results():
    """Render the results dashboard with visualizations and export options."""
    st.header("Optimized Production Schedule")
    
    if not st.session_state.optimization_results:
        st.error("No optimization results available. Please run the optimization first.")
        return
    
    # Action buttons at top
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Modify Inputs", type="secondary"):
            st.session_state.planning_step = 'input'
            reset_processing_state()
            st.rerun()
    with col2:
        if st.button("Re-run Optimization"):
            st.session_state.planning_step = 'forecast'
            reset_processing_state()
            st.rerun()
    
    # Forecast vs. Optimized Comparison
    st.subheader("Forecast vs. Optimized Comparison")
    st.caption("This shows how the optimization improved the initial forecast based on historical patterns")
    
    # Get both forecast and optimized data
    forecast_df = st.session_state.forecast_results['forecast_df']
    optimized_df = st.session_state.optimization_results['optimized_df']
    
    # Create comparison view
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Initial Forecast**")
        st.caption("Based on historical patterns + product requirements")
        
        # Forecast daily totals
        forecast_daily = forecast_df.groupby(['date', 'weekday'])['total_hours'].sum().reset_index()
        forecast_daily['date_str'] = pd.to_datetime(forecast_daily['date']).dt.strftime('%a %m/%d')
        
        fig_forecast = px.bar(
            forecast_daily,
            x='date_str',
            y='total_hours',
            title='Initial Forecast - Daily Load',
            labels={'total_hours': 'Hours', 'date_str': 'Day'},
            color='total_hours',
            color_continuous_scale='Oranges',
            height=300
        )
        fig_forecast.update_layout(showlegend=False)
        st.plotly_chart(fig_forecast, use_container_width=True)
        
        # Forecast stats
        forecast_variance = forecast_daily['total_hours'].var()
        forecast_max = forecast_daily['total_hours'].max()
        forecast_min = forecast_daily['total_hours'].min()
        st.metric("Daily Variance", f"{forecast_variance:.1f}")
        st.metric("Peak Day", f"{forecast_max:.1f}h")
        st.metric("Lowest Day", f"{forecast_min:.1f}h")
    
    with col2:
        st.write("**Optimized Schedule**")
        st.caption("After constraint-aware optimization")
        
        # Optimized daily totals
        optimized_daily = optimized_df.groupby(['date', 'weekday'])['total_hours'].sum().reset_index()
        optimized_daily['date_str'] = pd.to_datetime(optimized_daily['date']).dt.strftime('%a %m/%d')
        
        fig_optimized = px.bar(
            optimized_daily,
            x='date_str',
            y='total_hours',
            title='Optimized Schedule - Daily Load',
            labels={'total_hours': 'Hours', 'date_str': 'Day'},
            color='total_hours',
            color_continuous_scale='Blues',
            height=300
        )
        fig_optimized.update_layout(showlegend=False)
        st.plotly_chart(fig_optimized, use_container_width=True)
        
        # Optimized stats
        optimized_variance = optimized_daily['total_hours'].var()
        optimized_max = optimized_daily['total_hours'].max()
        optimized_min = optimized_daily['total_hours'].min()
        st.metric("Daily Variance", f"{optimized_variance:.1f}", delta=f"{optimized_variance - forecast_variance:.1f}")
        st.metric("Peak Day", f"{optimized_max:.1f}h", delta=f"{optimized_max - forecast_max:.1f}h")
        st.metric("Lowest Day", f"{optimized_min:.1f}h", delta=f"{optimized_min - forecast_min:.1f}h")
    
    # Side-by-side comparison chart
    st.write("**Side-by-Side Comparison**")
    
    # Combine data for comparison
    comparison_data = []
    for _, row in forecast_daily.iterrows():
        comparison_data.append({
            'Day': row['date_str'],
            'Hours': row['total_hours'],
            'Type': 'Initial Forecast'
        })
    for _, row in optimized_daily.iterrows():
        comparison_data.append({
            'Day': row['date_str'],
            'Hours': row['total_hours'],
            'Type': 'Optimized Schedule'
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    fig_comparison = px.bar(
        comparison_df,
        x='Day',
        y='Hours',
        color='Type',
        barmode='group',
        title='Load Distribution: Forecast vs. Optimized',
        color_discrete_map={
            'Initial Forecast': '#FFA500',
            'Optimized Schedule': '#1f77b4'
        },
        height=400
    )
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Optimization Summary
    st.subheader("What the Optimization Achieved")
    
    # Calculate improvements
    variance_improvement = forecast_variance - optimized_variance
    peak_reduction = forecast_max - optimized_max
    valley_increase = optimized_min - forecast_min
    
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.write("**Load Balancing Results**")
        
        if variance_improvement > 0:
            st.success(f"Reduced daily load variance by {variance_improvement:.1f} hours²")
        else:
            st.info("Load distribution was already well-balanced")
            
        if peak_reduction > 0:
            st.success(f"Reduced peak day load by {peak_reduction:.1f} hours")
        elif peak_reduction < 0:
            st.warning(f"Peak day increased by {abs(peak_reduction):.1f} hours")
        else:
            st.info("Peak day load unchanged")
            
        if valley_increase > 0:
            st.success(f"Increased minimum day load by {valley_increase:.1f} hours")
        elif valley_increase < 0:
            st.warning(f"Minimum day decreased by {abs(valley_increase):.1f} hours")
        else:
            st.info("Minimum day load unchanged")
    
    with summary_col2:
        st.write("**Overall Impact**")
        
        # Calculate overall smoothness score
        max_theoretical_daily = optimized_df['total_hours'].sum() / 5  # Perfect daily average
        forecast_deviation = abs(forecast_daily['total_hours'] - max_theoretical_daily).mean()
        optimized_deviation = abs(optimized_daily['total_hours'] - max_theoretical_daily).mean()
        smoothness_improvement = ((forecast_deviation - optimized_deviation) / forecast_deviation * 100) if forecast_deviation > 0 else 0
        
        if smoothness_improvement > 0:
            st.metric("Load Smoothness Improvement", f"+{smoothness_improvement:.1f}%", help="How much closer to perfect daily balance")
        else:
            st.metric("Load Smoothness", "Already optimal", help="Schedule was already well-balanced")
        
        # Show constraint compliance
        violations = st.session_state.optimization_results.get('constraint_violations', [])
        if len(violations) == 0:
            st.success("All constraints satisfied")
        else:
            st.error(f"{len(violations)} constraint violations - see detailed analysis below")
        
        # Show requirements fulfillment
        total_requirements = len(st.session_state.requirements.get('products', []))
        fulfilled_count = 0
        
        for req_product in st.session_state.requirements.get('products', []):
            product_name = req_product['Product']
            required_hours = req_product['Quantity (hours)']
            scheduled_data = optimized_df[optimized_df['product'] == product_name]
            scheduled_hours = scheduled_data['total_hours'].sum()
            
            if scheduled_hours >= required_hours * 0.9:  # 90% threshold
                fulfilled_count += 1
        
        fulfillment_rate = (fulfilled_count / total_requirements * 100) if total_requirements > 0 else 100
        st.metric("Requirements Fulfilled", f"{fulfillment_rate:.0f}%", help="Percentage of product requirements met")
    
    # Key metrics
    st.subheader("Performance Metrics")
    
    metrics = st.session_state.metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Load Variance Reduction",
            f"{metrics.get('variance_reduction', 0):.1f}%",
            delta=f"{metrics.get('variance_reduction', 0):.1f}%",
            help="Reduction in daily load variance compared to baseline"
        )
    
    with col2:
        st.metric(
            "Constraint Compliance",
            f"{metrics.get('constraint_compliance', 0):.0f}%",
            delta=None,
            help="Percentage of operational constraints satisfied"
        )
    
    with col3:
        st.metric(
            "Average Active Lines",
            f"{metrics.get('avg_active_lines', 0):.1f}",
            delta=f"+{metrics.get('active_lines_improvement', 0):.1f}",
            help="Average number of production lines active per day"
        )
    
    with col4:
        st.metric(
            "Total Production Hours",
            f"{metrics.get('total_hours', 0):.0f}h",
            delta=None,
            help="Total scheduled production hours for the week"
        )
    
    # Weekly Schedule Table
    st.subheader("Optimized Weekly Schedule")
    
    if 'schedule_df' in st.session_state.optimization_results:
        schedule_df = st.session_state.optimization_results['schedule_df']
        
        # Display the schedule table with formatting
        st.dataframe(
            schedule_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Add download buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV download
            csv_data = schedule_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"production_schedule_{st.session_state.requirements['planning_date']}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Excel download (simplified)
            if st.button("Generate Excel Report"):
                st.info("Excel export feature will be implemented in the next iteration")
        
        with col3:
            # Print-friendly view
            if st.button("Print View"):
                st.info("Print-friendly format will be implemented in the next iteration")
    
    # Product-Specific Analysis
    st.subheader("Product Production Schedule")
    
    if 'optimized_df' in st.session_state.optimization_results:
        optimized_df = st.session_state.optimization_results['optimized_df']
        
        # Show product distribution
        col1, col2 = st.columns(2)
        
        with col1:
            # Product completion timeline
            if 'product' in optimized_df.columns:
                product_summary = optimized_df[optimized_df['product'] != 'Idle'].groupby(['product', 'priority', 'deadline']).agg({
                    'total_hours': 'sum',
                    'date': ['min', 'max']
                }).reset_index()
                
                # Flatten column names
                product_summary.columns = ['Product', 'Priority', 'Deadline', 'Total Hours', 'Start Date', 'End Date']
                product_summary['Start Date'] = pd.to_datetime(product_summary['Start Date']).dt.strftime('%a %m/%d')
                product_summary['End Date'] = pd.to_datetime(product_summary['End Date']).dt.strftime('%a %m/%d')
                
                st.write("**Product Schedule Summary**")
                st.dataframe(
                    product_summary,
                    use_container_width=True,
                    hide_index=True
                )
        
        with col2:
            # Priority distribution
            priority_data = optimized_df[optimized_df['product'] != 'Idle'].groupby('priority')['total_hours'].sum().reset_index()
            if not priority_data.empty:
                fig_priority = px.pie(
                    priority_data,
                    values='total_hours',
                    names='priority',
                    title='Production Hours by Priority',
                    color_discrete_map={'High': '#ff4444', 'Medium': '#ffaa44', 'Low': '#44aa44'}
                )
                fig_priority.update_layout(height=300)
                st.plotly_chart(fig_priority, use_container_width=True)
        
        # Daily product schedule visualization
        st.subheader("Daily Product Distribution")
        
        # Create product timeline chart
        if 'product' in optimized_df.columns:
            # Prepare data for visualization
            daily_products = optimized_df[optimized_df['total_hours'] > 0].copy()
            daily_products['date_str'] = pd.to_datetime(daily_products['date']).dt.strftime('%a %m/%d')
            
            # Create stacked bar chart by product
            unique_products = daily_products['product'].unique()
            product_colors = px.colors.qualitative.Set3[:len(unique_products)]
            
            fig_products = go.Figure()
            
            for i, product in enumerate(unique_products):
                if product == 'Idle':
                    continue
                    
                product_data = daily_products[daily_products['product'] == product]
                product_daily = product_data.groupby('date_str')['total_hours'].sum().reset_index()
                
                fig_products.add_trace(go.Bar(
                    name=product,
                    x=product_daily['date_str'],
                    y=product_daily['total_hours'],
                    marker_color=product_colors[i % len(product_colors)]
                ))
            
            fig_products.update_layout(
                barmode='stack',
                title='Production Hours by Product and Day',
                xaxis_title='Day',
                yaxis_title='Hours',
                height=400
            )
            st.plotly_chart(fig_products, use_container_width=True)
        
        # Line utilization with product details
        st.subheader("Line Utilization by Product")
        
        # Create a detailed view showing which products are on which lines
        if 'product' in optimized_df.columns and 'line' in optimized_df.columns:
            line_product_detail = optimized_df[optimized_df['total_hours'] > 0].groupby(['date', 'line', 'product']).agg({
                'total_hours': 'sum'
            }).reset_index()
            
            line_product_detail['date_str'] = pd.to_datetime(line_product_detail['date']).dt.strftime('%a %m/%d')
            
            # Show as a detailed table
            line_schedule_pivot = line_product_detail.pivot_table(
                index=['date_str'],
                columns=['line'],
                values='product',
                aggfunc=lambda x: '\n'.join([f"{prod} ({optimized_df[(optimized_df['date'] == line_product_detail[line_product_detail['product'] == prod]['date'].iloc[0]) & (optimized_df['line'] == line_product_detail[line_product_detail['product'] == prod]['line'].iloc[0])]['total_hours'].sum():.1f}h)" for prod in x if prod != 'Idle']),
                fill_value='Idle'
            )
            
            # Simplified version for better readability - include ALL lines (even with 0 hours)
            # First, get all unique dates and lines from optimized_df
            all_combinations = optimized_df[['date', 'line']].drop_duplicates()
            
            # Create detailed view with all line-date combinations
            detailed_view = optimized_df.groupby(['date', 'line']).agg({
                'product': lambda x: ', '.join([p for p in x if p != 'Idle']) or 'Idle',
                'total_hours': 'sum'
            }).reset_index()
            
            # Include lines with 0 hours (these might be missing from groupby)
            all_lines = ['hohl2', 'hohl3', 'hohl4', 'massiv2', 'massiv3']
            all_dates = optimized_df['date'].unique()
            
            # Create a complete grid of all date-line combinations
            from itertools import product
            complete_combinations = pd.DataFrame(
                list(product(all_dates, all_lines)), 
                columns=['date', 'line']
            )
            
            # Merge to ensure all combinations are represented
            complete_view = pd.merge(complete_combinations, detailed_view, on=['date', 'line'], how='left')
            complete_view['product'] = complete_view['product'].fillna('Idle')
            complete_view['total_hours'] = complete_view['total_hours'].fillna(0.0)
            
            # Filter out lines that are truly not available (0 hours AND not in constraints)
            available_lines = st.session_state.constraints.get('line_availability', {})
            available_line_names = [line for line, available in available_lines.items() if available]
            
            # Only show available lines, but show them even if they have 0 hours
            filtered_view = complete_view[complete_view['line'].isin(available_line_names)]
            
            # Format for display (use .copy() to avoid SettingWithCopyWarning)
            filtered_view = filtered_view.copy()
            filtered_view['date_str'] = pd.to_datetime(filtered_view['date']).dt.strftime('%a %m/%d')
            filtered_view['line_product'] = (
                filtered_view['line'] + ': ' + 
                filtered_view['product'] + 
                ' (' + filtered_view['total_hours'].round(1).astype(str) + 'h)'
            )
            
            # Group by date to show all available lines for each day
            daily_line_summary = filtered_view.groupby('date_str')['line_product'].apply(
                lambda x: '\n'.join(sorted(x))  # Sort to ensure consistent ordering
            ).reset_index()
            daily_line_summary.columns = ['Day', 'Line Assignments']
            
            st.write("**Detailed Line-Product Assignments**")
            st.dataframe(
                daily_line_summary,
                use_container_width=True,
                hide_index=True,
                height=200
            )
    
    # Constraint Compliance & Requirements Analysis  
    st.subheader("Constraint Compliance & Requirements Check")
    
    violations = st.session_state.optimization_results.get('constraint_violations', [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Operational Constraints**")
        if len(violations) == 0:
            st.success("🎉 All operational constraints satisfied!")
            
            # Show compliance badges
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                st.success("Idle Line Constraint")
                st.success("Capacity Constraints")
            with subcol2:
                st.success("Personnel-Intensive Constraint")
                st.success("Line Availability")
        else:
            st.error(f"**{len(violations)} constraint violations found**")
            
            # Group violations by severity
            high_severity = [v for v in violations if v.get('severity') == 'high']
            medium_severity = [v for v in violations if v.get('severity') == 'medium']
            
            if high_severity:
                st.error("🚨 **Critical Issues**")
                for violation in high_severity:
                    date_str = pd.to_datetime(violation['date']).strftime('%A %m/%d')
                    st.error(f"**{date_str}**: {violation.get('description', 'Unknown issue')}")
                    st.info(f"💡 **Fix**: {violation.get('suggestion', 'No suggestion available')}")
            
            if medium_severity:
                st.warning("⚠️ **Warnings**")
                for violation in medium_severity:
                    date_str = pd.to_datetime(violation['date']).strftime('%A %m/%d')
                    st.warning(f"**{date_str}**: {violation.get('description', 'Unknown issue')}")
                    st.info(f"💡 **Fix**: {violation.get('suggestion', 'No suggestion available')}")
            
            # Show summary of how to resolve
            st.info("🔧 **How to resolve**: Adjust your input requirements (reduce hours, change deadlines) or modify constraints, then re-optimize.")
    
    with col2:
        st.write("**Requirements Fulfillment**")
        
        # Check if all products were scheduled by their deadlines
        if 'optimized_df' in st.session_state.optimization_results:
            optimized_df = st.session_state.optimization_results['optimized_df']
            requirements = st.session_state.requirements
            
            requirement_check = []
            for req_product in requirements.get('products', []):
                product_name = req_product['Product']
                required_hours = req_product['Quantity (hours)']
                deadline = req_product['Deadline']
                priority = req_product['Priority']
                
                # Find scheduled hours for this product
                scheduled_data = optimized_df[optimized_df['product'] == product_name]
                scheduled_hours = scheduled_data['total_hours'].sum()
                
                # Check deadline compliance
                deadline_order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
                deadline_idx = deadline_order.get(deadline, 5)
                
                scheduled_by_deadline = True
                if not scheduled_data.empty:
                    latest_day = pd.to_datetime(scheduled_data['date']).max()
                    latest_weekday = latest_day.strftime('%A')
                    latest_idx = deadline_order.get(latest_weekday, 5)
                    scheduled_by_deadline = latest_idx <= deadline_idx
                
                # Status determination
                if scheduled_hours >= required_hours and scheduled_by_deadline:
                    status = "Complete"
                elif scheduled_hours >= required_hours * 0.9:
                    status = "Mostly Complete"
                elif scheduled_hours > 0:
                    status = "Partial"
                else:
                    status = "Not Scheduled"
                
                requirement_check.append({
                    'Product': product_name,
                    'Required': f"{required_hours:.1f}h",
                    'Scheduled': f"{scheduled_hours:.1f}h",
                    'Deadline': deadline,
                    'Priority': priority,
                    'Status': status
                })
            
            if requirement_check:
                requirements_df = pd.DataFrame(requirement_check)
                st.dataframe(
                    requirements_df,
                    use_container_width=True,
                    hide_index=True,
                    height=200
                )
            else:
                st.info("No specific product requirements to check.")
    
    # Summary Statistics
    st.subheader("Planning Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Weekly Totals:**")
        if 'optimized_df' in st.session_state.optimization_results:
            optimized_df = st.session_state.optimization_results['optimized_df']
            
            # Calculate summary stats
            total_hours = optimized_df['total_hours'].sum()
            daily_avg = optimized_df.groupby('date')['total_hours'].sum().mean()
            daily_std = optimized_df.groupby('date')['total_hours'].sum().std()
            
            st.metric("Total Production Hours", f"{total_hours:.1f}h")
            st.metric("Daily Average", f"{daily_avg:.1f}h")
            st.metric("Daily Standard Deviation", f"{daily_std:.1f}h")
    
    with col2:
        st.write("**Optimization Transfers**")
        transfers = st.session_state.optimization_results.get('transfers', [])
        
        if transfers:
            st.metric("Optimization Transfers Applied", len(transfers))
            
            # Create detailed transfer log
            st.write("**Transfer Details**")
            transfer_details = []
            for i, transfer in enumerate(transfers, 1):
                # Extract transfer information (format varies based on implementation)
                if isinstance(transfer, dict):
                    peak_date = transfer.get('peak_date', 'Unknown')
                    valley_date = transfer.get('valley_date', 'Unknown')
                    line = transfer.get('line', 'Unknown')
                    hours = transfer.get('hours_to_transfer', transfer.get('hours', 0))
                    
                    # Format dates
                    if hasattr(peak_date, 'strftime'):
                        peak_str = peak_date.strftime('%a %m/%d')
                    else:
                        peak_str = str(peak_date)
                    if hasattr(valley_date, 'strftime'):
                        valley_str = valley_date.strftime('%a %m/%d')
                    else:
                        valley_str = str(valley_date)
                    
                    transfer_details.append({
                        'Transfer #': i,
                        'Hours Moved': f"{hours:.1f}h",
                        'From': f"{peak_str} ({line})",
                        'To': f"{valley_str} ({line})",
                        'Reason': 'Load balancing'
                    })
            
            if transfer_details:
                transfers_df = pd.DataFrame(transfer_details)
                st.dataframe(
                    transfers_df,
                    use_container_width=True,
                    hide_index=True,
                    height=min(200, len(transfer_details) * 35 + 50)
                )
            
            # Transfer impact summary
            st.write("**Transfer Impact**")
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                total_hours_moved = sum(t.get('hours_to_transfer', t.get('hours', 0)) for t in transfers if isinstance(t, dict))
                st.metric("Total Hours Redistributed", f"{total_hours_moved:.1f}h")
            with subcol2:
                unique_lines = len(set(t.get('line', '') for t in transfers if isinstance(t, dict) and t.get('line')))
                st.metric("Lines Optimized", unique_lines)
        else:
            st.info("No transfers were needed - the initial forecast was already well-balanced.")
    
    # Strategic Summary for Managers
    st.subheader("Executive Summary")
    st.info("Key takeaway: This optimization replaced manual scheduling guesswork with data-driven decisions.")
    
    summary_metrics = st.container()
    with summary_metrics:
        
        executive_col1, executive_col2, executive_col3 = st.columns(3)
        
        with executive_col1:
            st.write("**Business Value**")
            
            # Estimate cost savings (simplified calculation)
            total_hours = optimized_df['total_hours'].sum()
            if variance_improvement > 0:
                overtime_reduction_estimate = variance_improvement * 0.1  # Rough estimate
                st.success(f"Estimated overtime reduction: {overtime_reduction_estimate:.1f}h/week")
            
            if smoothness_improvement > 0:
                st.success(f"{smoothness_improvement:.1f}% improvement in load balance")
            
            st.success(f"{fulfillment_rate:.0f}% of requirements fulfilled")
        
        with executive_col2:
            st.write("**What Changed**")
            
            if len(transfers) > 0:
                st.write(f"• {len(transfers)} optimization transfers applied")
                total_hours_moved = sum(t.get('hours_to_transfer', t.get('hours', 0)) for t in transfers if isinstance(t, dict))
                st.write(f"• {total_hours_moved:.1f}h redistributed across the week")
                unique_lines = len(set(t.get('line', '') for t in transfers if isinstance(t, dict) and t.get('line')))
                st.write(f"• {unique_lines} production lines optimized")
            else:
                st.write("• No changes needed - initial forecast was optimal")
                st.write("• All constraints naturally satisfied")
            
            violation_count = len(st.session_state.optimization_results.get('constraint_violations', []))
            if violation_count == 0:
                st.write("• All operational constraints satisfied")
            else:
                st.write(f"• ⚠️ {violation_count} constraint issues to address")
        
        with executive_col3:
            st.write("**Next Steps**")
            
            if fulfillment_rate == 100 and len(violations) == 0:
                st.success("Ready to implement")
                st.write("• Download schedule for production")
                st.write("• Share with floor managers")
                st.write("• Monitor actual vs. planned")
            elif fulfillment_rate >= 90:
                st.warning("Minor adjustments needed")
                st.write("• Review partial requirements")
                st.write("• Consider constraint relaxation")
                st.write("• Implement with monitoring")
            else:
                st.error("Requires revision")
                st.write("• Adjust requirements or constraints")
                st.write("• Consider additional capacity")
                st.write("• Re-run optimization")
    
    # Future Vision Note
    st.markdown("---")
    st.info("""
    Future vision: In advanced implementations, the forecast will incorporate:
    • Machine learning predictions based on seasonality, orders, and market trends
    • Real-time capacity adjustments and material availability
    • Dynamic constraint optimization based on actual floor conditions
    • Multi-week planning horizons with rolling optimization
    
    This PoC demonstrates the foundation for that intelligent decision support system.
    """)


def main():
    """Main application entry point."""
    init_session_state()
    render_header()
    
    # Main navigation
    if st.session_state.planning_step == 'input':
        render_input_forms()
    elif st.session_state.planning_step == 'forecast':
        render_processing()
    elif st.session_state.planning_step == 'results':
        render_results()


if __name__ == "__main__":
    main()
