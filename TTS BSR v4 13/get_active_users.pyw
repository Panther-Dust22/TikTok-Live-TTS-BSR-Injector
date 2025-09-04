#!/usr/bin/env python3
"""
Helper script to get active users from the database
"""
import json
import os
from datetime import datetime

# GUI Communication System
GUI_LOG_FILE = "data/logs/gui_messages.log"

def log_to_gui(message):
    """Write message to GUI log file for display in the GUI"""
    try:
        from pathlib import Path
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(GUI_LOG_FILE, 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
    except:
        pass



def get_active_users():
    """Get list of currently active users"""
    database_file = "data/active_users.json"
    
    try:
        if os.path.exists(database_file):
            with open(database_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                active_users = data.get('active_users', {})
                last_updated = data.get('last_updated', 'Unknown')
                
                print("📊 Active Users Database")
                print("=" * 40)
                print(f"Total Active Users: {len(active_users)}")
                print(f"Last Updated: {last_updated}")
                print()
                
                if active_users:
                    print("👥 Currently Active Users:")
                    for nickname, timestamp in active_users.items():
                        last_activity = datetime.fromtimestamp(timestamp)
                        minutes_ago = (datetime.now() - last_activity).total_seconds() / 60
                        print(f"   • {nickname} (last active: {minutes_ago:.1f} mins ago)")
                else:
                    print("👥 No active users currently")
                
                return list(active_users.keys())
                
        else:
            print("❌ Active users database not found")
            return []
            
    except Exception as e:
        print(f"⚠️ Error reading database: {e}")
        return []

def get_user_count():
    """Get count of active users"""
    database_file = "data/active_users.json"
    
    try:
        if os.path.exists(database_file):
            with open(database_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return len(data.get('active_users', {}))
        return 0
    except:
        return 0

if __name__ == "__main__":
    # Log start
    try:
        from pathlib import Path
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] get_active_users.pyw started\n")
    except:
        pass
    
    # Hide console window on Windows when running with pythonw
    import ctypes
    import os
    
    if os.name == 'nt':  # Windows
        try:
            # Get the console window handle and hide it immediately
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            
            # Get console window handle
            console_window = kernel32.GetConsoleWindow()
            if console_window:
                # Hide the console window immediately
                user32.ShowWindow(console_window, 0)  # 0 = SW_HIDE
        except Exception:
            pass  # Fail silently if hiding console doesn't work
    
    try:
        active_users = get_active_users()
        print(f"\n🎯 Summary: {len(active_users)} active users")
        try:
            from pathlib import Path
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Retrieved {len(active_users)} active users\n")
        except:
            pass
    except Exception as e:
        try:
            from pathlib import Path
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] get_active_users execution error: {e}\n")
        except:
            pass
        print(f"Error: {e}")
    finally:
        try:
            from pathlib import Path
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] get_active_users.pyw stopped\n")
        except:
            pass