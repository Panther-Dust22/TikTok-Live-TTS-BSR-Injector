import asyncio
import time
import traceback
import websockets
import json
import psutil
import subprocess
import time
import os
import sys



# Simple WebSocket functions for TikFinity
def create_robust_websocket(url, name, **kwargs):
    return websockets.connect(url, **kwargs), None
def close_robust_websocket(name):
    pass

# WebSocket server address
WS_SERVER = 'ws://localhost:21213/'

# Optional file logger for ESD
esd_logger = None
last_message_ts = 0.0

def esd_log(message, level="INFO"):
    """Log to file directly."""
    try:
        from pathlib import Path
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}\n")
    except:
        pass

# Override GUI logger to avoid importing GUI module here
def write_log(message, level="INFO"):
    esd_log(message, level)

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

# Function to find the process running main.py
def find_main_py_process():
    """Find the running main.pyw process with improved detection"""
    for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline:
                cmdline_str = " ".join(cmdline).lower()
                # Check for main.pyw in command line
                if "main.pyw" in cmdline_str:
                    return proc
                # Also check for main.py (fallback)
                elif "main.py" in cmdline_str:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

# Function to stop main.py
def stop_main_py():
    """Stop main.pyw process with improved detection and termination"""
    process = find_main_py_process()
    if process:
        try:
            process.terminate()  # Gracefully terminate
            process.wait(timeout=5)  # Wait for process to exit
        except psutil.TimeoutExpired:
            process.kill()  # Force terminate if it doesn't stop in time
        except Exception:
            pass
    else:
        # Try to kill any remaining python processes that might be main.pyw
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and "main.pyw" in " ".join(cmdline).lower():
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

# Function to stop all TTS processes with robust termination
def stop_all_tts_processes():
    """Stop all TTS processes with proper timeout and force kill"""
    write_log("🛑 Starting TTS process termination", "INFO")
    
    stopped_processes = []
    failed_processes = []
    
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmdline_str = " ".join(cmdline).lower()
                    # Stop main.pyw, audio_queue_server_v2.pyw, user_tracker.pyw, api_monitor.pyw
                    if any(x in cmdline_str for x in ["main.pyw", "audio_queue_server_v2.pyw", "user_tracker.pyw", "api_monitor.pyw"]):
                        process_name = " ".join(cmdline).split()[-1] if cmdline else "unknown"
                        process_pid = proc.info['pid']
                        
                        write_log(f"Terminating {process_name} (PID: {process_pid})", "INFO")
                        
                        try:
                            # Graceful termination
                            proc.terminate()
                            proc.wait(timeout=5)  # Increased to 5 seconds
                            
                            stopped_processes.append(f"{process_name} (PID: {process_pid})")
                            write_log(f"✅ {process_name} terminated gracefully", "INFO")
                                
                        except psutil.TimeoutExpired:
                            # Force kill if graceful termination fails
                            write_log(f"⚠️ {process_name} didn't terminate gracefully, force killing", "WARNING")
                            
                            try:
                                proc.kill()
                                proc.wait(timeout=2)  # Wait for force kill
                                stopped_processes.append(f"{process_name} (PID: {process_pid}) - FORCE KILLED")
                                write_log(f"✅ {process_name} force killed", "INFO")
                            except Exception as kill_error:
                                failed_processes.append(f"{process_name} (PID: {process_pid}) - KILL FAILED: {kill_error}")
                                write_log(f"❌ Failed to kill {process_name}: {kill_error}", "ERROR")
                                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        write_log(f"❌ Error during process termination: {e}", "ERROR")
        print(f"Error stopping TTS processes: {e}")
    
    # Log summary
    write_log(f"Process termination summary: {len(stopped_processes)} stopped, {len(failed_processes)} failed", "INFO")
    if stopped_processes:
        write_log(f"Stopped processes: {', '.join(stopped_processes)}", "DEBUG")
    if failed_processes:
        write_log(f"Failed processes: {', '.join(failed_processes)}", "WARNING")
    
    return len(failed_processes) == 0  # Return True if all processes stopped successfully

def verify_processes_stopped():
    """Verify that all TTS processes have actually stopped"""
    write_log("🔍 Verifying all TTS processes have stopped", "INFO")
    
    remaining_processes = []
    
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmdline_str = " ".join(cmdline).lower()
                    # Check for main.pyw, audio_queue_server_v2.pyw, user_tracker.pyw, api_monitor.pyw
                    if any(x in cmdline_str for x in ["main.pyw", "audio_queue_server_v2.pyw", "user_tracker.pyw", "api_monitor.pyw"]):
                        process_name = " ".join(cmdline).split()[-1] if cmdline else "unknown"
                        process_pid = proc.info['pid']
                        remaining_processes.append(f"{process_name} (PID: {process_pid})")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        write_log(f"❌ Error verifying processes: {e}", "ERROR")
    
    if remaining_processes:
        write_log(f"⚠️ Remaining TTS processes: {', '.join(remaining_processes)}", "WARNING")
        return False
    else:
        write_log("✅ All TTS processes verified as stopped", "INFO")
        log_to_gui("All tts processes verified as stopped")
        return True

def cleanup_shared_memory():
    """Clean up any shared memory segments that might be left behind"""
    write_log("🧹 Cleaning up shared memory", "INFO")
    log_to_gui("Cleaning memory and audio queue")
    
    try:
        import mmap
        import struct
        
        # Try to clean up the audio queue shared memory
        try:
            shared_memory = mmap.mmap(-1, 1024 * 1024, "audio_queue_memory")
            # Clear the buffer
            shared_memory.seek(0)
            shared_memory.write(b'\x00\x00\x00\x00')
            shared_memory.flush()
            shared_memory.close()
            
            write_log("✅ Audio queue shared memory cleaned up", "INFO")
                
        except Exception as e:
            write_log(f"ℹ️ No audio queue shared memory to clean up: {e}", "DEBUG")
                
    except Exception as e:
        write_log(f"⚠️ Error cleaning up shared memory: {e}", "WARNING")

def cleanup_lock_files():
    """Clean up any lock files that might prevent restart"""
    write_log("🧹 Cleaning up lock files", "INFO")
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "data")
        
        # List of potential lock files
        lock_files = [
            os.path.join(data_dir, "user_tracker.lock"),
            os.path.join(data_dir, "audio_queue.lock"),
            os.path.join(data_dir, "api_monitor.lock"),
            os.path.join(data_dir, "main.lock")
        ]
        
        cleaned_files = []
        for lock_file in lock_files:
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
                    cleaned_files.append(os.path.basename(lock_file))
                    write_log(f"✅ Removed lock file: {os.path.basename(lock_file)}", "DEBUG")
            except Exception as e:
                write_log(f"⚠️ Could not remove lock file {os.path.basename(lock_file)}: {e}", "WARNING")
        
        if cleaned_files:
            write_log(f"✅ Cleaned up {len(cleaned_files)} lock files: {', '.join(cleaned_files)}", "INFO")
        else:
            write_log("ℹ️ No lock files found to clean up", "DEBUG")
                
    except Exception as e:
        write_log(f"⚠️ Error cleaning up lock files: {e}", "WARNING")

# Function to start all managed TTS processes (like GUI does)
def start_all_managed_processes():
    """Start all managed TTS processes with verification"""
    write_log("🚀 Starting all managed TTS processes", "INFO")
    
    started_processes = []
    failed_processes = []
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Start audio queue server v2
        audio_queue_path = os.path.join(script_dir, "audio_queue_server_v2.pyw")
        if os.path.isfile(audio_queue_path):
            try:
                process = subprocess.Popen(
                    ["py", "-3.12", audio_queue_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    cwd=script_dir
                )
                started_processes.append(f"audio_queue_server_v2.pyw (PID: {process.pid})")
                write_log(f"✅ Started audio_queue_server_v2.pyw (PID: {process.pid})", "INFO")
            except Exception as e:
                failed_processes.append(f"audio_queue_server_v2.pyw: {e}")
                write_log(f"❌ Failed to start audio_queue_server_v2.pyw: {e}", "ERROR")
        else:
            failed_processes.append("audio_queue_server_v2.pyw: File not found")
            write_log("❌ audio_queue_server_v2.pyw not found", "ERROR")
        
        # Start user tracker
        user_tracker_path = os.path.join(script_dir, "user_tracker.pyw")
        if os.path.isfile(user_tracker_path):
            try:
                process = subprocess.Popen(
                    ["py", "-3.12", user_tracker_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    cwd=script_dir
                )
                started_processes.append(f"user_tracker.pyw (PID: {process.pid})")
                write_log(f"✅ Started user_tracker.pyw (PID: {process.pid})", "INFO")
            except Exception as e:
                failed_processes.append(f"user_tracker.pyw: {e}")
                write_log(f"❌ Failed to start user_tracker.pyw: {e}", "ERROR")
        else:
            failed_processes.append("user_tracker.pyw: File not found")
            write_log("❌ user_tracker.pyw not found", "ERROR")
        
        # Start API monitor
        api_monitor_path = os.path.join(script_dir, "api_monitor.pyw")
        if os.path.isfile(api_monitor_path):
            try:
                process = subprocess.Popen(
                    ["py", "-3.12", api_monitor_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    cwd=script_dir
                )
                started_processes.append(f"api_monitor.pyw (PID: {process.pid})")
                write_log(f"✅ Started api_monitor.pyw (PID: {process.pid})", "INFO")
            except Exception as e:
                failed_processes.append(f"api_monitor.pyw: {e}")
                write_log(f"❌ Failed to start api_monitor.pyw: {e}", "ERROR")
        else:
            failed_processes.append("api_monitor.pyw: File not found")
            write_log("❌ api_monitor.pyw not found", "ERROR")
        
        # Start main.pyw last
        main_py_path = os.path.join(script_dir, "main.pyw")
        if os.path.isfile(main_py_path):
            try:
                process = subprocess.Popen(
                    ["py", "-3.12", main_py_path], 
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    cwd=script_dir
                )
                started_processes.append(f"main.pyw (PID: {process.pid})")
                write_log(f"✅ Started main.pyw (PID: {process.pid})", "INFO")
            except Exception as e:
                failed_processes.append(f"main.pyw: {e}")
                write_log(f"❌ Failed to start main.pyw: {e}", "ERROR")
        else:
            failed_processes.append("main.pyw: File not found")
            write_log("❌ main.pyw not found", "ERROR")
                
    except Exception as e:
        write_log(f"❌ Error starting managed processes: {e}", "ERROR")
        print(f"Error starting managed processes: {e}")
    
    # Log summary
    write_log(f"Process start summary: {len(started_processes)} started, {len(failed_processes)} failed", "INFO")
    if started_processes:
        write_log(f"Started processes: {', '.join(started_processes)}", "DEBUG")
    if failed_processes:
        write_log(f"Failed processes: {', '.join(failed_processes)}", "WARNING")
    
    return len(failed_processes) == 0  # Return True if all processes started successfully

def verify_processes_started():
    """Verify that all expected TTS processes are running"""
    write_log("🔍 Verifying all TTS processes are running", "INFO")
    
    expected_processes = ["main.pyw", "audio_queue_server_v2.pyw", "user_tracker.pyw", "api_monitor.pyw"]
    running_processes = []
    missing_processes = []
    
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmdline_str = " ".join(cmdline).lower()
                    for expected in expected_processes:
                        if expected in cmdline_str:
                            process_name = " ".join(cmdline).split()[-1] if cmdline else "unknown"
                            process_pid = proc.info['pid']
                            running_processes.append(f"{process_name} (PID: {process_pid})")
                            break
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        write_log(f"❌ Error verifying running processes: {e}", "ERROR")
    
    # Check which expected processes are missing
    for expected in expected_processes:
        found = False
        for running in running_processes:
            if expected in running:
                found = True
                break
        if not found:
            missing_processes.append(expected)
    
    if missing_processes:
        write_log(f"⚠️ Missing processes: {', '.join(missing_processes)}", "WARNING")
        return False
    else:
        write_log(f"✅ All expected processes running: {', '.join(running_processes)}", "INFO")
        return True

# Function to start main.py in hidden mode (kept for backward compatibility)
def start_main_py():
    start_all_managed_processes()

# Asynchronous WebSocket client with robust reconnection
_restart_lock = asyncio.Lock()

async def listen_to_chat():
    retry_delay = 1
    max_delay = 10  # Cap at 10 seconds for localhost
    
    while True:
        websocket = None
        try:
            esd_log("[ESD] Attempting to connect to websocket...", "INFO")
            # Use regular websocket connection to ensure consistent behavior when launched from GUI
            try:
                websocket = await asyncio.wait_for(
                    websockets.connect(
                        WS_SERVER,
                        ping_interval=23,    # 23 seconds between pings
                        ping_timeout=10,     # 10 second timeout
                        close_timeout=10
                    ),
                    timeout=10.0
                )
            except Exception as conn_err:
                esd_log(f"[ESD] Websocket connect failed: {conn_err}", "ERROR")
                try:
                    if esd_logger:
                        esd_logger.log_error("[ESD] Connect traceback:\n" + traceback.format_exc())
                except Exception:
                    pass
                raise
            esd_log("[ESD] Connected to websocket", "INFO")
            
            async def heartbeat():
                while True:
                    try:
                        ws_open = (websocket is not None and not websocket.closed)
                        since_last = time.time() - last_message_ts if last_message_ts else -1
                        esd_log(f"[ESD] Heartbeat: ws_open={ws_open} since_last_msg={since_last:.1f}s", "DEBUG")
                    except Exception:
                        pass
                    await asyncio.sleep(10)
            
            hb_task = asyncio.create_task(heartbeat())
            
            retry_delay = 1  # Reset retry delay on successful connection
            
            # Send a connection handshake message
            try:
                handshake = {"event": "client_connect", "client": "TTSESD"}
                await websocket.send(json.dumps(handshake))
            except Exception:
                pass
            
            # Message processing loop with timeout
            try:
                async for message in websocket:
                    try:
                        # Ensure message is properly decoded as UTF-8
                        if isinstance(message, bytes):
                            message = message.decode('utf-8', errors='replace')
                        
                        # Parse the received JSON message
                        data = json.loads(message)
                        # update last message time
                        try:
                            globals()['last_message_ts'] = time.time()
                        except Exception:
                            pass

                        # Check if the event is a chat message
                        if data.get('event') == 'chat':
                            chat_data = data.get('data', {})

                            raw_comment = chat_data.get('comment', '')
                            comment = (raw_comment or '').strip().lower()
                            is_moderator = chat_data.get('isModerator', False)
                            nickname = chat_data.get('nickname', 'Unknown')

                            esd_log(f"[ESD] Chat seen: {nickname} | mod={is_moderator} | comment='{raw_comment}'", "DEBUG")

                            # Make moderator check more robust
                            is_moderator_bool = (str(is_moderator).lower() in ('true', '1', 'yes')) if is_moderator is not None else False

                            # Normalize command and allow variants like "!restart now"
                            normalized = comment
                            if normalized.startswith('!restart') and is_moderator_bool:
                                # Debounce: if a restart is already running, ignore further requests
                                if _restart_lock.locked():
                                    esd_log("ℹ️ Restart already in progress; ignoring duplicate request", "INFO")
                                    continue
                                
                                async with _restart_lock:
                                    esd_log(f"🚨 ESD RESTART triggered by moderator {nickname}", "INFO")
                                    log_to_gui(f"ESD restart triggered by moderator {nickname}")
                                
                                # Step 1: Stop all TTS processes with verification
                                stop_success = stop_all_tts_processes()
                                
                                if not stop_success:
                                    esd_log("⚠️ Some processes failed to stop, continuing anyway", "WARNING")
                                
                                # Step 2: Wait for processes to fully terminate
                                esd_log("⏳ Waiting for processes to fully terminate...", "INFO")
                                await asyncio.sleep(5)  # Increased to 5 seconds
                                
                                # Step 3: Verify all processes have stopped
                                processes_stopped = verify_processes_stopped()
                                if not processes_stopped:
                                    esd_log("⚠️ Some processes still running, waiting longer...", "WARNING")
                                    await asyncio.sleep(3)  # Additional wait
                                    processes_stopped = verify_processes_stopped()
                                
                                # Step 4: Clean up shared memory and lock files
                                cleanup_shared_memory()
                                cleanup_lock_files()
                                
                                # Step 5: Start all managed processes
                                esd_log("🔄 Starting all TTS processes...", "INFO")
                                log_to_gui("starting all TTS processes...")
                                
                                start_success = start_all_managed_processes()
                                
                                # Step 6: Wait for processes to start and verify
                                esd_log("⏳ Waiting for processes to start...", "INFO")
                                await asyncio.sleep(3)  # Wait for processes to start
                                
                                # Step 7: Final verification
                                processes_started = verify_processes_started()
                                
                                if start_success and processes_stopped and processes_started:
                                    esd_log("✅ ESD restart completed successfully - all processes verified", "INFO")
                                    log_to_gui("esd restart completed successfully - all processes verified")
                                    log_to_gui("")  # Add gap after ESD restart
                                else:
                                    esd_log("⚠️ ESD restart completed with warnings", "WARNING")
                                    if not processes_stopped:
                                        esd_log("   - Some old processes may still be running", "WARNING")
                                    if not start_success:
                                        esd_log("   - Some new processes failed to start", "WARNING")
                                    if not processes_started:
                                        esd_log("   - Not all expected processes are running", "WARNING")

                    except json.JSONDecodeError:
                        pass  # Ignore non-JSON messages
                    except Exception:
                        pass
                        
            except asyncio.CancelledError:
                break  # Exit the inner loop to reconnect
            except json.JSONDecodeError as e:
                esd_log(f"[ESD] JSON decode error: {e}", "DEBUG")
                continue  # Skip this message and continue
            except UnicodeDecodeError as e:
                esd_log(f"[ESD] Unicode decode error: {e}", "DEBUG")
                continue  # Skip this message and continue
            except Exception as e:
                esd_log(f"[ESD] Message processing error: {e}", "ERROR")
                log_to_gui(f"ESD Error: {e}")
                break  # Exit the inner loop to reconnect
                    
        except asyncio.TimeoutError:
            pass
        except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidStatusCode):
            pass
        except ConnectionRefusedError:
            pass
        except Exception as loop_err:
            esd_log(f"[ESD] listen loop error: {loop_err}", "ERROR")
            log_to_gui(f"ESD Loop Error: {loop_err}")
            try:
                if esd_logger:
                    esd_logger.log_error("[ESD] Loop traceback:\n" + traceback.format_exc())
            except Exception:
                pass
        finally:
            # Properly close websocket if it exists
            if PING_PONG_AVAILABLE and 'worker_task' in locals():
                try:
                    await close_robust_websocket("TTSESD")
                except Exception:
                    pass
            elif websocket and not websocket.closed:
                try:
                    await websocket.close()
                except Exception:
                    pass
            # stop heartbeat
            try:
                if 'hb_task' in locals():
                    hb_task.cancel()
            except Exception:
                pass
            
            # Wait before reconnecting with exponential backoff
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.2, max_delay)  # Gentle backoff for localhost

        # (Removed file-based restart fallback at user request)
        pass

# Main function to run the WebSocket listener
def main():
    # Log start
    try:
        from pathlib import Path
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] TTSESD.pyw started\n")
    except:
        pass
    
    try:
        asyncio.run(listen_to_chat())
    except KeyboardInterrupt:
        try:
            from pathlib import Path
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] TTSESD stopped by user (KeyboardInterrupt)\n")
        except:
            pass
    except Exception as e:
        try:
            from pathlib import Path
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] TTSESD main execution error: {e}\n")
        except:
            pass
    finally:
        try:
            from pathlib import Path
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] TTSESD.pyw stopped\n")
        except:
            pass

if __name__ == "__main__":
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
        main()
    except Exception as e:
        # Log any unhandled exceptions
        try:
            with open("data/logs/ttsesd_crash.log", "a", encoding="utf-8") as f:
                from datetime import datetime
                f.write(f"{datetime.now().isoformat()} - Fatal error: {e}\n")
                import traceback
                f.write(traceback.format_exc())
        except:
            pass