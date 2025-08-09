#!/usr/bin/env python3
"""
Setup validation script for Load Balancing PoC.

Checks that all required files, dependencies, and data are properly configured
before running the full reproduction pipeline.
"""

import os
import sys
from pathlib import Path


def check_dependencies():
    """Check if required Python packages are installed."""
    print("🔍 Checking Python dependencies...")
    
    required_packages = ['pandas', 'openpyxl', 'yaml']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ❌ {package} - MISSING")
    
    if missing:
        print(f"\n⚠️  Install missing packages: pip install {' '.join(missing)}")
        return False
    
    return True


def check_directory_structure():
    """Check if required directories exist."""
    print("\n🗂️  Checking directory structure...")
    
    required_dirs = [
        'src/etl', 'src/forecast', 'src/smooth', 'src/viz',
        'data/processed', 'data/reports', 'logs', 'config', 'docs'
    ]
    
    missing_dirs = []
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✅ {directory}/")
        else:
            missing_dirs.append(directory)
            print(f"  ❌ {directory}/ - MISSING")
    
    if missing_dirs:
        print(f"\n⚠️  Create missing directories:")
        for directory in missing_dirs:
            print(f"    mkdir -p {directory}")
        return False
    
    return True


def check_source_files():
    """Check if required Python source files exist."""
    print("\n📄 Checking source files...")
    
    required_files = [
        'src/etl/utils.py',
        'src/etl/ingest.py', 
        'src/etl/matrix_parser.py',
        'src/forecast/baseline.py',
        'src/smooth/greedy.py',
        'src/viz/dashboard.py',
        'config/personnel_intensive.yml'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path} - MISSING")
    
    if missing_files:
        print(f"\n⚠️  Copy missing source files from PoC repository")
        return False
    
    return True


def check_data_files():
    """Check if Excel data files are available."""
    print("\n📊 Checking data files...")
    
    data_dirs = ['data/2024/H2_H3', 'data/2024/H4', 'data/2024/M2_M3']
    excel_files_found = 0
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            xlsx_files = list(Path(data_dir).glob('*.xlsx'))
            if xlsx_files:
                print(f"  ✅ {data_dir}/ - {len(xlsx_files)} Excel files")
                excel_files_found += len(xlsx_files)
            else:
                print(f"  ⚠️  {data_dir}/ - No Excel files found")
        else:
            print(f"  ❌ {data_dir}/ - Directory missing")
    
    if excel_files_found == 0:
        print(f"\n⚠️  No Excel files found. Ensure data is placed in correct directories.")
        return False
    elif excel_files_found < 5:
        print(f"\n⚠️  Only {excel_files_found} Excel files found. Consider adding more for better analysis.")
    
    return excel_files_found > 0


def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False


def run_quick_test():
    """Run a quick import test of key modules."""
    print("\n🧪 Running quick module tests...")
    
    try:
        # Test key imports
        import pandas as pd
        import yaml
        print("  ✅ Core imports successful")
        
        # Test configuration loading
        if os.path.exists('config/personnel_intensive.yml'):
            with open('config/personnel_intensive.yml', 'r') as f:
                config = yaml.safe_load(f)
            print("  ✅ Configuration file readable")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import test failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🔄 Load Balancing PoC - Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Source Files", check_source_files),
        ("Data Files", check_data_files),
        ("Module Tests", run_quick_test),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ {name} check failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\n🎉 All checks passed! Ready to run the reproduction pipeline.")
        print("\nNext steps:")
        print("1. python -m src.etl.ingest --help")
        print("2. python -m src.forecast.baseline --help")
        print("3. python -m src.viz.dashboard --help")
    else:
        print("\n⚠️  Some checks failed. Please address the issues above before proceeding.")
        print("\nRefer to REPRODUCTION_GUIDE.md for detailed setup instructions.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
