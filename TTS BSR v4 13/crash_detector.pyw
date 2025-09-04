#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crash Detector Script
Monitors other TTS processes for crashes and handles recovery
"""

import os
import sys
import time
import json
import psutil
import subprocess
import asyncio
import websockets
from pathlib import Path
from datetime import datetime

# Add the current directory to the path so we can import other modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Constants
websocket_url = "ws://localhost:21213/"
gui_log_file = "data/logs/gui_messages.log"
full_log_file = "data/logs/full_log.txt"
detection_timeout = 2  # seconds - reduced from 3 for faster response



def log_to_gui(message):
    """Write message to GUI log file"""
    try:
        # Ensure we're in the correct working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(gui_log_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
    except Exception as e:
        safe_print(f"GUI log write failed: {e}")
        pass

def safe_print(*args, **kwargs):
    """Safe print function that won't crash if stdout is not available"""
    try:
        print(*args, **kwargs)
    except Exception:
        pass

def write_log(message, level="INFO"):
    """Write to full log file"""
    try:
        # Ensure we're in the correct working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(full_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] [{level}] {message}\n")
    except Exception as e:
        # If we can't write to log, at least try to print to console
        safe_print(f"Log write failed: {e}")
        pass



def check_gui_log_for_message(nickname, comment, timeout_seconds=10):
    """Check if a message appears in GUI log within timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            # Ensure we're in the correct working directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            
            if os.path.exists(gui_log_file):
                with open(gui_log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if nickname in content and comment in content:
                        return True
        except Exception as e:
            safe_print(f"GUI log check failed: {e}")
            pass
        time.sleep(0.5)
    return False



def check_tikfinity_connection():
    """Check if TikFinity is connected by looking for recent connection message in full log"""
    global tikfinity_connected
    try:
        # Ensure we're in the correct working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        if os.path.exists(full_log_file):
            with open(full_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Look for recent "Connected to TikFinity" message (last 30 lines)
                recent_lines = lines[-30:] if len(lines) >= 30 else lines
                current_time = datetime.now()
                
                for line in recent_lines:
                    if "Connected to TikFinity" in line:
                        # Check if it's recent (within last 60 seconds)
                        try:
                            # Extract timestamp from log line [2025-08-11 17:45:25]
                            if '[' in line and ']' in line:
                                timestamp_str = line.split('[')[1].split(']')[0]
                                log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                time_diff = (current_time - log_time).total_seconds()
                                
                                if time_diff < 60:  # Within last 60 seconds
                                    tikfinity_connected = True
                                    return True
                        except:
                            # If timestamp parsing fails, just check if it's in recent lines
                            tikfinity_connected = True
                            return True
    except Exception as e:
        safe_print(f"TikFinity connection check failed: {e}")
        pass
    return False

def check_esd_activity():
    """Check if ESD has been activated recently by looking for ESD restart messages"""
    try:
        # Ensure we're in the correct working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        if os.path.exists(full_log_file):
            with open(full_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Look for recent ESD restart messages (last 50 lines)
                recent_lines = lines[-50:] if len(lines) >= 50 else lines
                current_time = datetime.now()
                
                for line in recent_lines:
                    # Check for ESD restart messages
                    if any(esd_indicator in line for esd_indicator in [
                        "🚨 ESD RESTART triggered by moderator",
                        "✅ ESD restart completed successfully",
                        "ESD restart triggered by moderator"
                    ]):
                        # Check if it's recent (within last 30 seconds)
                        try:
                            # Extract timestamp from log line [2025-08-11 17:45:25]
                            if '[' in line and ']' in line:
                                timestamp_str = line.split('[')[1].split(']')[0]
                                log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                time_diff = (current_time - log_time).total_seconds()
                                
                                if time_diff < 30:  # Within last 30 seconds
                                    write_log(f"🔍 ESD activity detected: {line.strip()}", "INFO")
                                    return True
                        except:
                            # If timestamp parsing fails, just check if it's in recent lines
                            write_log(f"🔍 ESD activity detected (no timestamp): {line.strip()}", "INFO")
                            return True
    except Exception as e:
        write_log(f"❌ Error checking ESD activity: {e}", "ERROR")
        pass
    return False

def stop_all_tts_processes():
    """Stop all TTS processes with optimized timeout and force kill"""
    write_log("🛑 Crash detector: Starting TTS process termination", "INFO")
    
    stopped_processes = []
    failed_processes = []
    
    try:
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
                            # Graceful termination with reduced timeout
                            proc.terminate()
                            proc.wait(timeout=3)  # Reduced from 5 to 3 seconds
                            
                            stopped_processes.append(f"{process_name} (PID: {process_pid})")
                            write_log(f"✅ {process_name} terminated gracefully", "INFO")
                                
                        except psutil.TimeoutExpired:
                            # Force kill if graceful termination fails
                            write_log(f"⚠️ {process_name} didn't terminate gracefully, force killing", "WARNING")
                            
                            try:
                                proc.kill()
                                proc.wait(timeout=1)  # Reduced from 2 to 1 second
                                stopped_processes.append(f"{process_name} (PID: {process_pid}) - FORCE KILLED")
                                write_log(f"✅ {process_name} force killed", "INFO")
                            except Exception as kill_error:
                                failed_processes.append(f"{process_name} (PID: {process_pid}) - KILL FAILED: {kill_error}")
                                write_log(f"❌ Failed to kill {process_name}: {kill_error}", "ERROR")
                                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        write_log(f"❌ Error during process termination: {e}", "ERROR")
    
    # Log summary
    write_log(f"Process termination summary: {len(stopped_processes)} stopped, {len(failed_processes)} failed", "INFO")
    return len(failed_processes) == 0  # Return True if all processes stopped successfully

def verify_processes_stopped():
    """Verify that all TTS processes have actually stopped (same as ESD)"""
    write_log("🔍 Verifying all TTS processes have stopped", "INFO")
    
    remaining_processes = []
    
    try:
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

def start_all_managed_processes():
    """Start all managed TTS processes in parallel for faster startup"""
    write_log("🚀 Starting all managed TTS processes in parallel", "INFO")
    
    started_processes = []
    failed_processes = []
    processes_to_start = []
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define all processes to start
        process_configs = [
            ("audio_queue_server_v2.pyw", "audio_queue_server_v2.pyw"),
            ("user_tracker.pyw", "user_tracker.pyw"),
            ("api_monitor.pyw", "api_monitor.pyw"),
            ("main.pyw", "main.pyw")  # main.pyw last for proper startup order
        ]
        
        # Start all processes in parallel
        for script_name, process_name in process_configs:
            script_path = os.path.join(script_dir, script_name)
            if os.path.isfile(script_path):
                try:
                    process = subprocess.Popen(
                        ["py", "-3.12", script_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        cwd=script_dir
                    )
                    processes_to_start.append((process, process_name))
                    started_processes.append(f"{process_name} (PID: {process.pid})")
                    write_log(f"✅ Started {process_name} (PID: {process.pid})", "INFO")
                except Exception as e:
                    failed_processes.append(f"{process_name}: {e}")
                    write_log(f"❌ Failed to start {process_name}: {e}", "ERROR")
            else:
                failed_processes.append(f"{process_name}: File not found")
                write_log(f"❌ Failed to start {process_name}: File not found", "ERROR")
                
    except Exception as e:
        write_log(f"❌ Error starting managed processes: {e}", "ERROR")
    
    # Log summary
    write_log(f"Process start summary: {len(started_processes)} started, {len(failed_processes)} failed", "INFO")
    return len(failed_processes) == 0  # Return True if all processes started successfully

def verify_processes_started():
    """Verify that all expected processes are running (same as ESD)"""
    write_log("🔍 Verifying all TTS processes have started", "INFO")
    
    expected_processes = ["main.pyw", "audio_queue_server_v2.pyw", "user_tracker.pyw", "api_monitor.pyw"]
    running_processes = []
    missing_processes = []
    
    try:
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
        write_log(f"❌ Error verifying started processes: {e}", "ERROR")
    
    # Check which expected processes are missing
    for expected in expected_processes:
        if not any(expected in proc for proc in running_processes):
            missing_processes.append(expected)
    
    if missing_processes:
        write_log(f"⚠️ Missing TTS processes: {', '.join(missing_processes)}", "WARNING")
        return False
    else:
        write_log("✅ All TTS processes verified as started", "INFO")
        return True

async def wait_for_esd_completion():
    """Wait for ESD activity to complete before proceeding"""
    write_log("🔍 Checking for ESD activity...", "INFO")
    
    # Wait up to 20 seconds for ESD activity to complete
    start_time = time.time()
    timeout = 20  # seconds
    
    while time.time() - start_time < timeout:
        # Check if ESD is currently active
        if check_esd_activity():
            write_log("⏳ ESD activity detected - waiting for completion...", "INFO")
            await asyncio.sleep(2)  # Wait 2 seconds before checking again
        else:
            write_log("✅ No ESD activity detected - proceeding", "INFO")
            return True
    
    write_log("⚠️ Timeout waiting for ESD completion - proceeding anyway", "WARNING")
    return False

async def wait_for_main_operational():
    """Wait for main.pyw to be fully operational before resuming monitoring"""
    write_log("🔍 Waiting for main.pyw operational indicators...", "INFO")
    
    # Wait up to 20 seconds for main.pyw to be fully operational (reduced from 30)
    start_time = time.time()
    timeout = 20  # seconds
    
    # First, wait a minimum startup time to avoid checking stale indicators
    write_log("⏳ Waiting minimum startup time (3 seconds)...", "INFO")
    await asyncio.sleep(3)
    
    while time.time() - start_time < timeout:
        try:
            # Ensure we're in the correct working directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.chdir(script_dir)
            
            if os.path.exists(full_log_file):
                with open(full_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Look for recent operational indicators in the last 30 lines (reduced from 50)
                    recent_lines = lines[-30:] if len(lines) >= 30 else lines
                    current_time = datetime.now()
                    
                    # Check for fresh indicators that main.pyw is operational
                    indicators_found = 0
                    required_indicators = 2  # Need at least 2 indicators
                    
                    for line in recent_lines:
                        # Check if the line is recent (within last 15 seconds)
                        try:
                            if '[' in line and ']' in line:
                                timestamp_str = line.split('[')[1].split(']')[0]
                                log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                time_diff = (current_time - log_time).total_seconds()
                                
                                # Only count indicators from the last 15 seconds
                                if time_diff <= 15:
                                    # Indicator 1: Fresh Connected to TikFinity
                                    if "Connected to TikFinity" in line:
                                        indicators_found += 1
                                    # Indicator 2: Fresh Started background TTS processor
                                    elif "Started background TTS processor" in line:
                                        indicators_found += 1
                                    # Indicator 3: Fresh Queue size logging
                                    elif "Queue size:" in line:
                                        indicators_found += 1
                                    # Indicator 4: Fresh GUI message
                                    elif "| Subscriber:" in line and "| Moderator:" in line:
                                        indicators_found += 1
                        except:
                            # If timestamp parsing fails, skip this line
                            continue
                    
                    if indicators_found >= required_indicators:
                        write_log(f"✅ Found {indicators_found} fresh operational indicators - main.pyw is ready", "INFO")
                        return True
                        
        except Exception as e:
            write_log(f"❌ Error checking operational status: {e}", "ERROR")
        
        # Wait 0.5 seconds before checking again (reduced from 1 second)
        await asyncio.sleep(0.5)
    
    write_log("⚠️ Timeout waiting for main.pyw operational indicators - proceeding anyway", "WARNING")
    return False

async def restart_services():
    """Restart TTS services with optimized timing"""
    try:
        write_log("🚨 CRASH DETECTOR RESTART triggered", "INFO")
        log_to_gui("Crash detected - Restarting services")
        
        # Step 0: Check for ESD activity and wait if needed
        write_log("🔍 Checking for ESD activity before proceeding...", "INFO")
        await wait_for_esd_completion()
        
        # Step 1: Stop all TTS processes with verification
        stop_success = stop_all_tts_processes()
        
        if not stop_success:
            write_log("⚠️ Some processes failed to stop, continuing anyway", "WARNING")
        
        # Step 2: Wait for processes to fully terminate (reduced from 5 to 3 seconds)
        write_log("⏳ Waiting for processes to fully terminate...", "INFO")
        await asyncio.sleep(3)  # Reduced from 5 to 3 seconds
        
        # Step 3: Verify all processes have stopped (skip if termination was successful)
        if stop_success:
            write_log("✅ Process termination successful, skipping verification", "INFO")
            processes_stopped = True
        else:
            processes_stopped = verify_processes_stopped()
            if not processes_stopped:
                write_log("⚠️ Some processes still running, waiting longer...", "WARNING")
                await asyncio.sleep(2)  # Reduced from 3 to 2 seconds
                processes_stopped = verify_processes_stopped()
        
        # Step 4: Start all managed processes
        write_log("🔄 Starting all TTS processes...", "INFO")
        log_to_gui("starting all TTS processes...")
        
        start_success = start_all_managed_processes()
        
        # Step 5: Wait for processes to start and verify (reduced from 3 to 2 seconds)
        write_log("⏳ Waiting for processes to start...", "INFO")
        await asyncio.sleep(2)  # Reduced from 3 to 2 seconds
        
        # Step 6: Final verification
        processes_started = verify_processes_started()
        
        if start_success and processes_stopped and processes_started:
            write_log("✅ Crash detector restart completed successfully - all processes verified", "INFO")
            log_to_gui("crash detector restart completed successfully - all processes verified")
            log_to_gui("")  # Add gap after restart
            
            # Step 7: Wait for main.pyw to be fully operational before resuming monitoring
            write_log("⏳ Waiting for main.pyw to be fully operational...", "INFO")
            await wait_for_main_operational()
            write_log("✅ Main.pyw is operational - waiting 5 seconds before resuming monitoring", "INFO")
            await asyncio.sleep(5)  # Wait 5 seconds before resuming monitoring
            write_log("✅ Resuming monitoring after 5-second safety delay", "INFO")
        else:
            write_log("⚠️ Crash detector restart completed with warnings", "WARNING")
            if not processes_stopped:
                write_log("   - Some old processes may still be running", "WARNING")
            if not start_success:
                write_log("   - Some new processes failed to start", "WARNING")
            if not processes_started:
                write_log("   - Not all expected processes are running", "WARNING")
        
    except Exception as e:
        write_log(f"❌ Error during crash detector restart: {e}", "ERROR")



async def connect_to_websocket():
    """Connect to TikFinity websocket and monitor messages"""
    global websocket_client
    
    write_log("🔄 connect_to_websocket() function started", "INFO")
    
    while True:
        websocket = None
        try:
            safe_print("Attempting to connect to TikFinity...")
            write_log("🔌 Crash detector connecting to TikFinity...", "INFO")
            
            write_log(f"🔄 About to connect to {websocket_url}", "INFO")
            websocket = await asyncio.wait_for(
                websockets.connect(
                    websocket_url,
                    ping_interval=23,
                    ping_timeout=10,
                    close_timeout=10
                ),
                timeout=10.0
            )
            
            websocket_client = websocket
            safe_print("Connected to TikFinity")
            write_log("✅ Crash detector connected to TikFinity", "INFO")
            
            write_log("🔄 Starting message processing loop", "INFO")
            async for message in websocket:
                try:
                    write_log("📨 Received message from TikFinity", "INFO")
                    if isinstance(message, bytes):
                        message = message.decode('utf-8', errors='replace')
                    
                    data = json.loads(message)
                    write_log(f"📨 Parsed message: {data.get('event', 'unknown')}", "INFO")
                    
                    # Check if it's a chat message
                    if data.get("event") == "chat":
                        chat_data = data.get("data", {})
                        nickname = chat_data.get("nickname", "")
                        comment = chat_data.get("comment", "")
                        
                        write_log(f"💬 Processing chat message: {nickname}: {comment[:30]}...", "INFO")
                        
                        if nickname and comment:
                            # Skip moderator commands - they're handled by ESD or main.pyw voice change system, not normal TTS processing
                            moderator_commands = [
                                '!restart',  # ESD handles this
                                '!vadd',     # Voice change system
                                '!vremove',  # Voice change system
                                '!vchange',  # Voice change system
                                '!vname',    # Voice change system
                                '!vnoname',  # Voice change system
                                '!vrude'     # Voice change system
                            ]
                            
                            comment_lower = comment.strip().lower()
                            if any(comment_lower.startswith(cmd) for cmd in moderator_commands):
                                write_log(f"⏭️ Skipping moderator command: {comment[:30]}...", "INFO")
                                continue
                            
                            # Check if message appears in GUI log within timeout
                            write_log(f"🔍 Checking if message appears in GUI log...", "INFO")
                            if not check_gui_log_for_message(nickname, comment, detection_timeout):
                                write_log(f"⚠️ Message NOT found in GUI log - triggering restart!", "WARNING")
                                await restart_services()
                            else:
                                write_log(f"✅ Message found in GUI log, processing normally", "INFO")
                        
                except json.JSONDecodeError:
                    write_log("❌ Failed to parse JSON message", "ERROR")
                    pass
                except Exception as e:
                    write_log(f"❌ Error processing message: {e}", "ERROR")
                    
        except asyncio.TimeoutError:
            safe_print("Connection timeout. Retrying...")
        except Exception as e:
            safe_print(f"WebSocket error: {e}")
        finally:
            if websocket and not websocket.closed:
                try:
                    await websocket.close()
                except:
                    pass
            websocket_client = None
            await asyncio.sleep(1)



async def supervisor(task_fn, task_name):
    """Supervisor function that continuously restarts a task if it fails"""
    write_log(f"🔄 Supervisor started for {task_name}", "INFO")
    while True:
        try:
            write_log(f"🔄 Starting {task_name}...", "INFO")
            await task_fn()
        except Exception as e:
            write_log(f"❌ Task {task_name} crashed: {e}", "ERROR")
            import traceback
            write_log(f"❌ Task {task_name} traceback: {traceback.format_exc()}", "ERROR")
        write_log(f"🔄 Restarting {task_name} in 1 second...", "INFO")
        await asyncio.sleep(1)  # Small pause before restart

async def main_async():
    """Main async function"""
    write_log("🚀 Crash Detector main_async() function started", "INFO")
    
    write_log("🔄 About to start websocket client with supervisor", "INFO")
    # Start websocket client with supervisor that will continuously restart it
    await asyncio.gather(
        supervisor(connect_to_websocket, "WebSocket Client")
    )

def main():
    """Main crash detector function"""
    safe_print("🚀 Crash Detector started")
    write_log("🚀 Crash Detector main() function started", "INFO")
    
    try:
        write_log("🔄 About to call asyncio.run(main_async())", "INFO")
        asyncio.run(main_async())
    except KeyboardInterrupt:
        safe_print("Crash Detector stopped by user")
        write_log("🛑 Crash Detector stopped by user", "INFO")
    except Exception as e:
        safe_print(f"Crash Detector error: {e}")
        write_log(f"❌ Crash Detector main() error: {e}", "ERROR")
        import traceback
        write_log(f"❌ Crash Detector main() traceback: {traceback.format_exc()}", "ERROR")

if __name__ == "__main__":
    main()
