#!/usr/bin/env python3
"""
Progress checker for voice discovery
"""

import os
import glob
import json
from datetime import datetime

def main():
    print("=== TikTok TTS Voice Discovery Progress ===")
    print(f"Checked at: {datetime.now()}")
    print()
    
    # Check if script is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'comprehensive_voice_discovery.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Discovery script is currently running")
            pids = result.stdout.strip().split('\n')
            print(f"  Process IDs: {', '.join(pids)}")
        else:
            print("✗ Discovery script is not running")
    except:
        print("? Could not check if script is running")
    
    print()
    
    # Check for log file
    if os.path.exists("voice_discovery_log.txt"):
        print("📝 Log file found. Last few lines:")
        with open("voice_discovery_log.txt", "r") as f:
            lines = f.readlines()
            for line in lines[-10:]:  # Last 10 lines
                print(f"   {line.rstrip()}")
    else:
        print("📝 No log file found yet")
    
    print()
    
    # Check for result files
    result_files = glob.glob("voice_discovery_results_*.json")
    summary_files = glob.glob("voice_discovery_summary_*.txt")
    
    if result_files or summary_files:
        print("📊 Result files found:")
        for f in sorted(result_files + summary_files):
            size = os.path.getsize(f)
            mtime = datetime.fromtimestamp(os.path.getmtime(f))
            print(f"  {f} ({size} bytes, modified: {mtime})")
        
        # Show latest summary if available
        if summary_files:
            latest_summary = sorted(summary_files)[-1]
            print(f"\n📋 Latest summary ({latest_summary}):")
            with open(latest_summary, "r") as f:
                print(f.read())
    else:
        print("📊 No result files found yet")

if __name__ == "__main__":
    main()