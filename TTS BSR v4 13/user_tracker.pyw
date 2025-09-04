import asyncio
import websockets
import json
import time
import threading
import os
from datetime import datetime, timedelta

# Simple logging function
def write_log(message, level="INFO"):
    """Simple logging to data/logs/full_log.txt"""
    try:
        import os
        from datetime import datetime
        from pathlib import Path
        
        # Ensure logs directory exists
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file path
        log_file = logs_dir / "full_log.txt"
        
        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format log entry
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # Write to file with UTF-8 encoding
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    except Exception as e:
        # Fallback to print if logging fails
        print(f"Logging error: {e}")
        print(f"[{level}] {message}")

# Simple WebSocket functions for TikFinity
def create_robust_websocket(url, name, **kwargs):
    return websockets.connect(url, **kwargs), None
def close_robust_websocket(name):
    pass

class ActiveUserTracker:
    def __init__(self, database_file="data/active_users.json"):
        self.database_file = database_file
        self.active_users = {}  # {nickname: last_message_timestamp}
        self.websocket_url = "ws://localhost:21213/"
        self.cleanup_interval = 60  # Check every 60 seconds
        self.activity_timeout = 600  # 10 minutes in seconds
        self.running = True
        
        # Load existing database
        self.load_database()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def load_database(self):
        """Load active users from JSON database"""
        try:
            if os.path.exists(self.database_file):
                with open(self.database_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.active_users = data.get('active_users', {})
                    
                # Clean up any expired users from loaded data
                self._cleanup_expired_users()
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.database_file), exist_ok=True)
                self.active_users = {}
        except Exception:
            self.active_users = {}
    
    def save_database(self):
        """Save active users to JSON database"""
        try:
            data = {
                'active_users': self.active_users,
                'last_updated': datetime.now().isoformat(),
                'total_users': len(self.active_users)
            }
            
            # Direct write like other settings files
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            # Log successful save
            write_log(f"Saved database with {len(self.active_users)} users", "INFO")
                
        except Exception as e:
            # Log save error
            write_log(f"Error saving database: {str(e)}", "ERROR")
    
    def add_user_activity(self, nickname):
        """Add or update user activity timestamp"""
        current_time = time.time()
        was_new_user = nickname not in self.active_users
        
        self.active_users[nickname] = current_time
        
        # Only save to database periodically to reduce file I/O
        # Save every 30 seconds instead of every activity
        if not hasattr(self, '_last_save_time'):
            self._last_save_time = 0
        
        if current_time - self._last_save_time > 30:  # Save every 30 seconds
            self.save_database()
            self._last_save_time = current_time
    
    def remove_user(self, nickname):
        """Remove user from active list"""
        if nickname in self.active_users:
            del self.active_users[nickname]
            self.save_database()
            return True
        return False
    
    def get_active_users(self):
        """Get list of currently active users"""
        return list(self.active_users.keys())
    
    def get_user_count(self):
        """Get count of active users"""
        return len(self.active_users)
    
    def get_user_last_activity(self, nickname):
        """Get last activity timestamp for a user"""
        if nickname in self.active_users:
            timestamp = self.active_users[nickname]
            return datetime.fromtimestamp(timestamp)
        return None
    
    def _cleanup_expired_users(self):
        """Remove users who haven't been active for 10+ minutes"""
        current_time = time.time()
        expired_users = []
        
        for nickname, last_activity in self.active_users.items():
            if current_time - last_activity > self.activity_timeout:
                expired_users.append(nickname)
        
        # Remove expired users
        for nickname in expired_users:
            self.remove_user(nickname)
        
        return len(expired_users)
    
    def _cleanup_loop(self):
        """Background thread that periodically cleans up expired users"""
        while self.running:
            try:
                time.sleep(self.cleanup_interval)
                expired_count = self._cleanup_expired_users()
                
                if expired_count > 0:
                    pass
                    
            except Exception:
                pass
    
    def print_stats(self):
        """Print current statistics"""
        print(f"\n📊 Active User Stats:")
        print(f"   Total Active Users: {len(self.active_users)}")
        print(f"   Activity Timeout: {self.activity_timeout // 60} minutes")
        print(f"   Database File: {self.database_file}")
        
        if self.active_users:
            print(f"   Current Users: {', '.join(list(self.active_users.keys())[:5])}")
            if len(self.active_users) > 5:
                print(f"   ... and {len(self.active_users) - 5} more")
        print()
    
    async def connect_to_tikfinity(self):
        """Connect to TikFinity and track user activity"""
        retry_delay = 1
        max_delay = 10
        
        # Log startup
        write_log(f"User tracker starting, connecting to {self.websocket_url}", "INFO")
        
        while self.running:
            try:
                # Simple WebSocket connection for TikFinity
                websocket = await asyncio.wait_for(
                    websockets.connect(
                        self.websocket_url,
                        ping_interval=23,    # 23 seconds between pings
                        ping_timeout=10,     # 10 second timeout
                        close_timeout=10
                    ),
                    timeout=10.0
                )
                
                retry_delay = 1  # Reset delay on successful connection
                
                # Log successful connection
                write_log("Connected to TikFinity successfully", "INFO")
                
                # Listen for messages
                async for message in websocket:
                    try:
                        # Ensure message is properly decoded as UTF-8
                        if isinstance(message, bytes):
                            message = message.decode('utf-8', errors='replace')
                        
                        data = json.loads(message)
                        
                        # Log all messages to debug
                        write_log(f"Received message: {str(data)[:200]}...", "DEBUG")
                        write_log(f"Event: {data.get('event', 'NO_EVENT')}", "DEBUG")
                        if 'data' in data and isinstance(data['data'], dict):
                            write_log(f"Data keys: {list(data['data'].keys())}", "DEBUG")
                            write_log(f"Nickname in data: {data['data'].get('nickname', 'NOT_FOUND')}", "DEBUG")
                            try:
                                with open("data/logs/user_tracker_debug.log", "a", encoding="utf-8") as f:
                                    f.write(f"{time.strftime('%H:%M:%S')} - Received message: {str(data)[:200]}...\n")
                                    f.write(f"{time.strftime('%H:%M:%S')} - Event: {data.get('event', 'NO_EVENT')}\n")
                                    if 'data' in data and isinstance(data['data'], dict):
                                        f.write(f"{time.strftime('%H:%M:%S')} - Data keys: {list(data['data'].keys())}\n")
                                        f.write(f"{time.strftime('%H:%M:%S')} - Nickname in data: {data['data'].get('nickname', 'NOT_FOUND')}\n")
                            except:
                                pass
                        
                        # Extract nickname from message (handle nested format)
                        nickname = ''
                        if data.get('event') == 'chat' and 'data' in data and isinstance(data['data'], dict):
                            chat_data = data['data']
                            nickname = chat_data.get('nickname', '').strip()
                        elif 'nickname' in data:
                            nickname = data.get('nickname', '').strip()  # Fallback for direct format
                        
                        if nickname:
                            # Add/update user activity
                            self.add_user_activity(nickname)
                            # Debug output (will be written to log file)
                            write_log(f"Added user: {nickname}", "INFO")
                        else:
                            # Log when no nickname found
                            write_log("No nickname found in message", "WARNING")
                            
                    except json.JSONDecodeError as e:
                        write_log(f"JSON decode error: {e}", "DEBUG")
                        pass  # Ignore non-JSON messages
                    except UnicodeDecodeError as e:
                        write_log(f"Unicode decode error: {e}", "DEBUG")
                        pass  # Ignore messages with encoding issues
                    except Exception as e:
                        write_log(f"Message processing error: {e}", "ERROR")
                        pass
                        
            except asyncio.TimeoutError:
                pass
            except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidStatusCode):
                pass
            except ConnectionRefusedError:
                pass
            except Exception:
                pass
            finally:
                # Clean up websocket
                try:
                    if 'websocket' in locals() and not websocket.closed:
                        await websocket.close()
                except:
                    pass
                
                # Wait before reconnecting
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.2, max_delay)
    
    def shutdown(self):
        """Clean shutdown"""
        self.running = False
        self.save_database()

# Main execution
async def main():
    """Main function to run the user tracker"""
    # Log start
    try:
        from pathlib import Path
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] User tracker started\n")
    except:
        pass
    
    # Check if another instance is already running
    import os
    lock_file = "data/user_tracker.lock"
    
    try:
        # Try to create a lock file
        with open(lock_file, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        
        tracker = ActiveUserTracker()
        
        try:
            # Start tracking
            await tracker.connect_to_tikfinity()
            
        except KeyboardInterrupt:
            try:
                from pathlib import Path
                logs_dir = Path("data/logs")
                logs_dir.mkdir(parents=True, exist_ok=True)
                with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                    from datetime import datetime
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] User tracker stopped by user (KeyboardInterrupt)\n")
            except:
                pass
        except Exception as e:
            try:
                from pathlib import Path
                logs_dir = Path("data/logs")
                logs_dir.mkdir(parents=True, exist_ok=True)
                with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                    from datetime import datetime
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] User tracker connection error: {e}\n")
            except:
                pass
        finally:
            tracker.shutdown()
            
    except FileExistsError:
        # Another instance is running, exit silently
        return
    finally:
        # Clean up lock file
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except:
            pass

if __name__ == "__main__":
    # Hide console window on Windows
    import ctypes
    import os
    
    if os.name == 'nt':  # Windows
        try:
            # Get the console window handle
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            
            # Get console window handle
            console_window = kernel32.GetConsoleWindow()
            if console_window:
                # Hide the console window
                user32.ShowWindow(console_window, 0)  # 0 = SW_HIDE
        except Exception:
            pass  # Fail silently if hiding console doesn't work
    
    # Run silently with no console output
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Silent exit on Ctrl+C
    except Exception as e:
        # Log any unhandled exceptions
        try:
            import os
            os.makedirs("data/logs", exist_ok=True)
            with open("data/logs/user_tracker_crash.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} - Fatal error: {e}\n")
                import traceback
                f.write(traceback.format_exc())
        except:
            pass