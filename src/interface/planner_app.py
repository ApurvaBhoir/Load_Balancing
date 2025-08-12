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
        export_schedule
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
        page_icon="🍫",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.title("🍫 Ritter Sport Production Load Balancing")
    st.subheader("Decision Support Tool for Production Planners")
    
    # Progress indicator with clickable navigation
    steps = ["📝 Input", "🔮 Forecast", "⚖️ Optimize", "📊 Results"]
    step_keys = ['input', 'forecast', 'optimize', 'results']
    current_step_idx = {'input': 0, 'forecast': 1, 'optimize': 1, 'results': 3}.get(
        st.session_state.planning_step, 0
    )
    
    cols = st.columns(4)
    for i, (col, step, step_key) in enumerate(zip(cols, steps, step_keys)):
        with col:
            if i == current_step_idx:
                st.markdown(f"**{step}** ✨")
            elif i < current_step_idx:
                # Completed steps - make them clickable
                if step_key == 'input' and st.button(f"{step} ✅", key=f"nav_{step_key}", help="Click to return to input"):
                    st.session_state.planning_step = 'input'
                    reset_processing_state()
                    st.rerun()
                elif step_key == 'results' and 'optimization_results' in st.session_state and st.button(f"{step} ✅", key=f"nav_{step_key}", help="Click to view results"):
                    st.session_state.planning_step = 'results'
                    st.rerun()
                else:
                    st.markdown(f"{step} ✅")
            else:
                # Future steps - not yet available
                if i == current_step_idx + 1:
                    st.markdown(f"⏳ {step}")
                else:
                    st.markdown(f"⏸️ {step}")


def render_input_forms():
    """Render the input forms for requirements and constraints."""
    st.header("📝 Production Planning Input")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("A) Production Requirements")
        st.info("💡 Enter the production demands defined by managers for the upcoming week.")
        
        # Load historical data to get available products
        try:
            available_products = get_available_products()
        except Exception as e:
            st.error(f"Could not load historical data: {e}")
            available_products = ["100g Knusperkeks", "100g Waffel", "100g Marzipan", "Mini Knusperkeks", "Standard"]
        
        # Planning week selection
        st.write("**Planning Week:**")
        planning_date = st.date_input(
            "Select Monday of the week to plan",
            value=date.today() + timedelta(days=(7 - date.today().weekday())),  # Next Monday
            help="Choose the Monday of the week you want to create a production plan for"
        )
        
        # Product requirements table
        st.write("**Product Demands:**")
        
        if 'requirements_df' not in st.session_state:
            # Initialize with some default products
            default_products = available_products[:5] if len(available_products) >= 5 else available_products
            st.session_state.requirements_df = pd.DataFrame({
                'Product': default_products,
                'Quantity (hours)': [0.0] * len(default_products),
                'Priority': ['Medium'] * len(default_products),
                'Deadline': ['Friday'] * len(default_products)
            })
        
        # Editable dataframe for requirements
        requirements_df = st.data_editor(
            st.session_state.requirements_df,
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
        
        st.session_state.requirements_df = requirements_df
        
        # Validation
        total_hours = requirements_df['Quantity (hours)'].sum()
        st.metric("Total Production Hours Requested", f"{total_hours:.1f} h")
        
        if total_hours > 600:  # 5 lines * 5 days * 24h = 600h theoretical max
            st.error("⚠️ Total hours exceed theoretical capacity (600h/week)")
        elif total_hours > 480:  # 5 lines * 5 days * ~19h average = more reasonable max
            st.warning("⚠️ Total hours are very high - may require overtime")
    
    with col2:
        st.subheader("B) Constraints & Factors")
        
        # Line availability
        st.write("**Line Availability:**")
        line_availability = {}
        lines = ["hohl2", "hohl3", "hohl4", "massiv2", "massiv3"]
        
        for line in lines:
            line_availability[line] = st.checkbox(
                f"{line.capitalize()} available",
                value=True,
                help=f"Uncheck if {line} is down for maintenance"
            )
        
        # Constraint overrides
        st.write("**Constraint Settings:**")
        
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
        st.write("**Additional Factors:**")
        
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
        
        st.write("**Special Notes:**")
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
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🔮 Generate Forecast & Optimize", type="primary", use_container_width=True):
            if total_hours == 0:
                st.error("Please enter at least one product requirement")
            else:
                # Reset processing state and move to forecast step
                reset_processing_state()
                st.session_state.planning_step = 'forecast'
                st.rerun()
    
    with col3:
        if st.button("📊 Load Sample Scenario", use_container_width=True):
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
    st.success("✅ Sample scenario loaded! Review the requirements and click 'Generate Forecast & Optimize'")
    st.rerun()


def render_processing():
    """Render the processing step with progress indicators."""
    st.header("🔮 Generating Forecast and Optimization")
    
    # Check if we should run processing
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    if not st.session_state.processing_complete:
        # Show processing in progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Load historical data and generate forecast
            status_text.text("🔄 Analyzing historical patterns...")
            progress_bar.progress(25)
            
            forecast_results = run_forecast(
                st.session_state.requirements,
                st.session_state.constraints
            )
            
            # Step 2: Run optimization
            status_text.text("⚖️ Optimizing schedule with constraints...")
            progress_bar.progress(50)
            
            optimization_results = run_optimization(
                forecast_results,
                st.session_state.requirements,
                st.session_state.constraints
            )
            
            # Step 3: Calculate metrics
            status_text.text("📊 Calculating performance metrics...")
            progress_bar.progress(75)
            
            metrics = calculate_metrics(forecast_results, optimization_results)
            
            # Step 4: Complete
            status_text.text("✅ Processing complete!")
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
    st.header("📊 Optimized Production Schedule")
    
    if not st.session_state.optimization_results:
        st.error("No optimization results available. Please run the optimization first.")
        return
    
    # Action buttons at top
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔙 Modify Inputs", type="secondary"):
            st.session_state.planning_step = 'input'
            reset_processing_state()
            st.rerun()
    with col2:
        if st.button("🔄 Re-run Optimization"):
            st.session_state.planning_step = 'forecast'
            reset_processing_state()
            st.rerun()
    
    # Key metrics
    st.subheader("📈 Performance Overview")
    
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
    st.subheader("📅 Optimized Weekly Schedule")
    
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
            if st.button("📊 Generate Excel Report"):
                st.info("Excel export feature will be implemented in the next iteration")
        
        with col3:
            # Print-friendly view
            if st.button("🖨️ Print View"):
                st.info("Print-friendly format will be implemented in the next iteration")
    
    # Load Distribution Visualization
    st.subheader("📊 Load Distribution Analysis")
    
    if 'optimized_df' in st.session_state.optimization_results:
        optimized_df = st.session_state.optimization_results['optimized_df']
        
        # Create daily load chart
        daily_totals = optimized_df.groupby(['date', 'weekday'])['total_hours'].sum().reset_index()
        daily_totals['date_str'] = pd.to_datetime(daily_totals['date']).dt.strftime('%a %m/%d')
        
        fig = px.bar(
            daily_totals, 
            x='date_str', 
            y='total_hours',
            title='Daily Total Production Hours',
            labels={'total_hours': 'Hours', 'date_str': 'Day'},
            color='total_hours',
            color_continuous_scale='Blues'
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Line utilization chart
        st.subheader("🔧 Line Utilization")
        
        line_pivot = optimized_df.pivot_table(
            index=['date', 'weekday'], 
            columns='line', 
            values='total_hours', 
            fill_value=0
        ).reset_index()
        
        # Create stacked bar chart
        line_columns = [col for col in line_pivot.columns if col not in ['date', 'weekday']]
        line_pivot['date_str'] = pd.to_datetime(line_pivot['date']).dt.strftime('%a %m/%d')
        
        fig_lines = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        for i, line in enumerate(line_columns):
            fig_lines.add_trace(go.Bar(
                name=line.upper(),
                x=line_pivot['date_str'],
                y=line_pivot[line],
                marker_color=colors[i % len(colors)]
            ))
        
        fig_lines.update_layout(
            barmode='stack',
            title='Production Hours by Line and Day',
            xaxis_title='Day',
            yaxis_title='Hours',
            height=400
        )
        st.plotly_chart(fig_lines, use_container_width=True)
    
    # Constraint Compliance
    st.subheader("✅ Constraint Compliance")
    
    violations = st.session_state.optimization_results.get('constraint_violations', [])
    
    if len(violations) == 0:
        st.success("🎉 All constraints satisfied!")
        
        # Show compliance badges
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("✅ Idle Line Constraint")
        with col2:
            st.success("✅ Personnel-Intensive Constraint")
        with col3:
            st.success("✅ Capacity Constraints")
    else:
        st.warning(f"⚠️ Found {len(violations)} constraint violations")
        for violation in violations[:5]:  # Show first 5
            st.warning(f"• {violation.get('constraint', 'Unknown')} violated on {violation.get('date', 'Unknown date')}")
    
    # Summary Statistics
    st.subheader("📈 Planning Summary")
    
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
        st.write("**Transfers Applied:**")
        transfers = st.session_state.optimization_results.get('transfers', [])
        
        if transfers:
            st.metric("Optimization Transfers", len(transfers))
            st.write("Recent transfers:")
            for transfer in transfers[:3]:  # Show first 3
                st.caption(f"• Moved {transfer.get('hours', 0):.1f}h from {transfer.get('from', '')} to {transfer.get('to', '')}")
        else:
            st.info("No transfers were needed - schedule was already optimal!")


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
