#!/usr/bin/env python3
"""
Launch script for the Ritter Sport Production Load Balancing Planner Interface.

This script launches the Streamlit web application for production planners.
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit planner interface."""
    
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if Streamlit is available
    try:
        import streamlit
        print("✅ Streamlit is available")
    except ImportError:
        print("❌ Streamlit not found. Please install it:")
        print("   conda install streamlit")
        sys.exit(1)
    
    # Check if the app file exists
    app_path = "src/interface/planner_app.py"
    if not os.path.exists(app_path):
        print(f"❌ App file not found: {app_path}")
        sys.exit(1)
    
    # Launch the Streamlit app
    print("🚀 Launching Ritter Sport Production Planner Interface...")
    print("   📱 Open your browser to: http://localhost:8501")
    print("   🛑 Press Ctrl+C to stop the server")
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Planner interface stopped.")

if __name__ == "__main__":
    main()
