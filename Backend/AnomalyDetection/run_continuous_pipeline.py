#!/usr/bin/env python3
"""
Continuous ML Pipeline - Runs ML and Prophet on log stream
"""
import sys
sys.path.insert(0, '.')

import time
from datetime import datetime
import subprocess
import os

def run_ml_pipeline():
    """Execute ML pipeline"""
    print(f"\n{'='*80}")
    print(f"⏰ [ML Pipeline] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    result = subprocess.run(['python3', 'main.py'], capture_output=True, text=True, timeout=15)
    if result.returncode == 0:
        print("✅ ML Pipeline completed")
        # Print last few lines of output
        lines = result.stdout.split('\n')
        for line in lines[-8:]:
            if line.strip() and '=' not in line:
                print(f"   {line}")
    else:
        print(f"❌ ML Error: {result.stderr[:200]}")

def run_prophet_forecaster():
    """Execute Prophet forecasting"""
    print(f"\n{'='*80}")
    print(f"🔮 [Prophet] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    result = subprocess.run(['python3', 'prophet_forecaster.py'], capture_output=True, text=True, timeout=20)
    if result.returncode == 0:
        print("✅ Prophet Forecasting completed")
    else:
        print(f"⚠️ Prophet Error: {result.stderr[:200]}")

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 CONTINUOUS ML & PROPHET PIPELINE STARTED")
    print("="*80)
    print("📊 Configuration:")
    print("   • ML Pipeline: Every 30 seconds")
    print("   • Prophet Forecasting: Every 60 seconds")
    print("   • Data Source: Kubernetes pod log stream")
    print("   • Storage: MongoDB")
    print("="*80 + "\n")
    
    # Run first iteration immediately
    print("🔄 Running initial pipeline...")
    run_ml_pipeline()
    
    # Run continuously with simple timing
    try:
        ml_counter = 0
        prophet_counter = 0
        while True:
            ml_counter += 1
            prophet_counter += 1
            
            if ml_counter >= 30:
                run_ml_pipeline()
                ml_counter = 0
            
            if prophet_counter >= 60:
                run_prophet_forecaster()
                prophet_counter = 0
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✅ Pipeline stopped gracefully")
