#!/usr/bin/env python3
"""
Simple script to run the Ritter Sport Production Planner interface locally.

For production deployment, use Docker:
    ./deploy.sh
    # OR: docker compose up --build

For local development:
    python run_planner_interface.py
    # OR: streamlit run src/interface/planner_app.py
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit planner interface."""
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if streamlit is available
    try:
        import streamlit
    except ImportError:
        print("❌ Streamlit not found. Please install requirements:")
        print("   pip install -r requirements.txt")
        print("")
        print("Or use Docker deployment:")
        print("   ./deploy.sh")
        sys.exit(1)
    
    print("🍫 Starting Ritter Sport Production Planner...")
    print("📊 Interface will open at: http://localhost:8501")
    print("🔄 Press Ctrl+C to stop the application")
    print("")
    
    # Run the Streamlit app
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/interface/planner_app.py",
            "--server.port=8501",
            "--server.headless=false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start application: {e}")
        print("\nTry using Docker instead:")
        print("   ./deploy.sh")
        sys.exit(1)

if __name__ == "__main__":
    main()