#!/usr/bin/env python3
"""
Unified TTS Diagnostic Tool
Comprehensive system health check and testing for Emstar233's TTS System
"""

import asyncio
import websockets
import json
import random
import threading
import requests
import os
import sys
import psutil
import subprocess
import platform
import shutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from time import time
import time as time_module

# Direct subprocess calls
RUNNER_AVAILABLE = False

# Global variable to hold all websocket connections (like ws testing server)
connected_clients = set()

async def broadcast_message(message):
    """Send the message to all connected clients (EXACT from ws testing server)."""
    message_json = json.dumps(message)  # Convert message to JSON string
    if connected_clients:  # Check if there are any connected clients
        # Send the message to each connected client
        for websocket in connected_clients:
            try:
                await websocket.send(message_json)
                # Don't print the full message - just log that it was sent
            except Exception as e:
                print(f"Error sending message to a client: {e}")

class UnifiedDiagnostics:
    def __init__(self):
        self.test_results = {}
        self.running = False
        self.loop = None
        self.tts_gui_process = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.tts_dir = os.path.join(os.path.dirname(self.script_dir), 'TTS BSR v4 13')
        self.expected_connections = ['main.pyw', 'user_tracker.pyw']  # Only expect 2 connections when Start TTS is pressed
        self.connected_processes = set()
        
        # Ensure the TTS directory exists
        if not os.path.exists(self.tts_dir):
            print(f"❌ TTS directory not found: {self.tts_dir}")
            print("Please ensure the diagnostic tool is in the correct location relative to the TTS BSR v4 13 folder")
            input("Press Enter to exit...")
            sys.exit(1)
            
        print(f"📁 Diagnostic tool location: {self.script_dir}")
        print(f"📁 TTS system location: {self.tts_dir}")
        print(f"📁 Report will be saved to: {self.script_dir}")
        
    def print_header(self, title):
        """Print a formatted header."""
        print(f"\n{'='*70}")
        print(f" {title}")
        print(f"{'='*70}")
    
    def print_section(self, title):
        """Print a formatted section header."""
        print(f"\n{'-'*50}")
        print(f" {title}")
        print(f"{'-'*50}")
        
    def print_result(self, test_name: str, success: bool, message: str = ""):
        """Print a test result with consistent formatting."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if message:
            print(f"     {message}")
        self.test_results[test_name] = success
        
    def check_tikfinity_process(self) -> bool:
        """Check if TikFinity.exe is running and close it if found."""
        self.print_section("Checking TikFinity Process")
        
        tikfinity_found = False
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] and 'tikfinity' in proc.info['name'].lower():
                    tikfinity_found = True
                    print(f"🔍 Found TikFinity process (PID: {proc.info['pid']})")
                    
                    # Try to terminate gracefully
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                        self.print_result("TikFinity Process", True, "Successfully closed TikFinity.exe")
                    except psutil.TimeoutExpired:
                        proc.kill()
                        self.print_result("TikFinity Process", True, "Force-killed TikFinity.exe")
                    except Exception as e:
                        self.print_result("TikFinity Process", False, f"Failed to close: {e}")
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if not tikfinity_found:
            self.print_result("TikFinity Process", True, "No TikFinity.exe found running")
            
        return True
        
    def check_gui_process(self) -> bool:
        """Check if TTS GUI is already running and ask user to close it."""
        self.print_section("Checking TTS GUI Process")
        
        gui_found = False
        for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('tts_gui_v4.pyw' in arg for arg in cmdline):
                    gui_found = True
                    print(f"🔍 Found TTS GUI process (PID: {proc.info['pid']})")
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if gui_found:
            print("\n⚠️ TTS GUI is already running!")
            print("Please close the TTS GUI window manually.")
            print("This ensures a clean start for the diagnostic test.")
            
            # Wait for user to close GUI
            while True:
                input("\nPress Enter after you have closed the TTS GUI...")
                
                # Check if GUI is still running
                gui_still_running = False
                for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
                    try:
                        cmdline = proc.info['cmdline']
                        if cmdline and any('tts_gui_v4.pyw' in arg for arg in cmdline):
                            gui_still_running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if not gui_still_running:
                    self.print_result("TTS GUI Process", True, "TTS GUI closed successfully")
                    break
                else:
                    print("❌ TTS GUI is still running. Please close it completely and try again.")
        else:
            self.print_result("TTS GUI Process", True, "No TTS GUI found running")
            
        return True
        
    def launch_gui(self) -> bool:
        """Launch the TTS GUI using the shortcut."""
        self.print_section("Launching TTS GUI")
        
        try:
            # Find the shortcut
            shortcut_path = os.path.join(os.path.dirname(self.tts_dir), 'Run TTS BSR.lnk')
            if not os.path.exists(shortcut_path):
                self.print_result("GUI Launch", False, f"Shortcut not found: {shortcut_path}")
                return False
                
            # Launch using Windows shell
            import subprocess
            result = subprocess.run(['cmd', '/c', 'start', '', shortcut_path], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.print_result("GUI Launch", True, "TTS GUI launched successfully")
                
                # Wait a moment for GUI to start
                time_module.sleep(3)
                
                # Bring diagnostic window to front
                self.bring_to_front()
                
                return True
            else:
                self.print_result("GUI Launch", False, f"Failed to launch: {result.stderr}")
                return False
                
        except Exception as e:
            self.print_result("GUI Launch", False, f"Exception: {e}")
            return False
            
    def bring_to_front(self):
        """Bring the diagnostic window to the front."""
        try:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.ShowWindow(hwnd, 1)  # SW_SHOWNORMAL
                print("📱 Brought diagnostic window to front")
        except Exception as e:
            print(f"⚠️ Could not bring window to front: {e}")
            
    def start_websocket_server(self, port=21213):
        """Start WebSocket server in a separate thread (like ws testing server)."""
        
        async def handler(websocket, path):
            """Main handler for the WebSocket connection."""
            connected_clients.add(websocket)  # Add the new websocket connection to the set
            print("🔌 WebSocket connection established.")  # Debug statement
            try:
                await websocket.wait_closed()  # Keep the connection open until closed
            finally:
                connected_clients.remove(websocket)  # Remove the websocket connection when closed
                print("🔌 WebSocket connection closed.")  # Debug statement

        async def main():
            """Start the WebSocket server."""
            async with websockets.serve(handler, "localhost", port):
                print(f"🚀 Diagnostic WebSocket server running on ws://localhost:{port}/")
                await asyncio.Future()  # run forever

        try:
            # Create a new event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)  # Set the new loop as the current loop

            # Start the WebSocket server in a separate thread
            server_thread = threading.Thread(target=lambda: self.loop.run_until_complete(main()))
            server_thread.start()
            
            print("🚀 WebSocket server started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start WebSocket server: {e}")
            return False
            
    def generate_test_message(self, comment: str) -> Dict:
        """Generate a test chat message using EXACT code from ws testing server."""
        # Generate random user details (EXACT same as ws testing server)
        user_id = str(random.randint(1000000000000000000, 9999999999999999999))
        sec_uid = "<redacted>"
        unique_id = "zerodytester"
        nickname = "Diagnostics"  # Changed from "roger100" to "Diagnostics"
        profile_picture_url = "https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0...webp"

        # User badges (EXACT same as ws testing server)
        user_badges = [
            {
                "type": "pm_mt_moderator_im",
                "name": "Moderator"
            },
            {
                "type": "image",
                "displayType": 1,
                "url": "https://p19-webcast.tiktokcdn.com/webcast-va/rankl...image"
            },
            {
                "type": "image",
                "displayType": 1,
                "url": "https://p19-webcast.tiktokcdn.com/webcast-va/....~...image"
            }
        ]

        # User details (EXACT same as ws testing server)
        user_details = {
            "createTime": str(int(time())),  # Current timestamp
            "bioDescription": "",
            "profilePictureUrls": [
                profile_picture_url,
                profile_picture_url,
                profile_picture_url
            ]
        }

        # Follow info (EXACT same as ws testing server)
        follow_info = {
            "followingCount": 10000,
            "followerCount": 606,
            "followStatus": 0,
            "pushStatus": 0
        }

        # Create the message payload in the EXACT format from ws testing server
        message = {
            "event": "chat",
            "data": {
                "comment": comment,
                "userId": user_id,
                "secUid": sec_uid,
                "uniqueId": unique_id,
                "nickname": nickname,
                "profilePictureUrl": profile_picture_url,
                "followRole": 0,  # 0 = none
                "userBadges": user_badges,
                "userDetails": user_details,
                "followInfo": follow_info,
                "isModerator": True,  # Change made here: now a string
                "isNewGifter": False,  # Also changed to string if necessary
                "isSubscriber": False,   # Also changed to string if necessary
                "topGifterRank": 0,
                "msgId": str(random.randint(1000000000000000000, 9999999999999999999)),  # Random message ID
                "createTime": str(int(time()))  # Current timestamp
            }
        }
        
        return message
        
    def send_test_message(self, comment: str) -> bool:
        """Send a test message using EXACT method from ws testing server."""
        message = self.generate_test_message(comment)
        
        # Broadcast the message to all connected clients (EXACT same as ws testing server)
        if connected_clients:  # Ensure there are active connections
            asyncio.run_coroutine_threadsafe(broadcast_message(message), self.loop)
            print(f"📤 Sent test message: {comment}")
            return True
        else:
            print("No active WebSocket connections.")
            return False
        
    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        self.print_section("Python Version Check")
        
        current_version = sys.version_info
        print(f"Current Python: {current_version.major}.{current_version.minor}.{current_version.micro}")
        
        # Check if it's Python 3.12.x
        if current_version.major == 3 and current_version.minor == 12:
            self.print_result("Python Version", True, f"Using Python {current_version.major}.{current_version.minor}.{current_version.micro}")
            return True
        else:
            self.print_result("Python Version", False, f"Expected Python 3.12.x, got {current_version.major}.{current_version.minor}.{current_version.micro}")
            return False
            
    def check_required_packages(self) -> bool:
        """Check if all required packages are installed."""
        self.print_section("Required Packages Check")
        
        required_packages = [
            'asyncio', 'websockets', 'requests', 'psutil', 'pygame', 
            'pycaw', 'comtypes', 'pydub', 'watchdog'
        ]
        
        all_installed = True
        for package in required_packages:
            try:
                __import__(package)
                self.print_result(f"Package: {package}", True)
            except ImportError:
                self.print_result(f"Package: {package}", False, "Not installed")
                all_installed = False
                
        return all_installed
        
    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        self.print_section("FFmpeg Check")
        
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract version from output
                version_line = result.stdout.split('\n')[0]
                self.print_result("FFmpeg", True, f"Found: {version_line}")
                return True
            else:
                self.print_result("FFmpeg", False, "FFmpeg command failed")
                return False
        except FileNotFoundError:
            self.print_result("FFmpeg", False, "FFmpeg not found in PATH")
            return False
        except Exception as e:
            self.print_result("FFmpeg", False, f"Error: {e}")
            return False
            
    def check_tts_files(self) -> bool:
        """Check if all required TTS files exist."""
        self.print_section("TTS Files Check")
        
        required_files = [
            'main.pyw', 'tts_gui_v4.pyw', 'TTS.pyw', 'TTSESD.pyw',
            'audio_queue_server_v2.pyw', 'user_tracker.pyw', 'api_monitor.pyw',
            'crash_detector.pyw'
        ]
        
        all_exist = True
        for file in required_files:
            file_path = os.path.join(self.tts_dir, file)
            if os.path.exists(file_path):
                self.print_result(f"File: {file}", True)
            else:
                self.print_result(f"File: {file}", False, "File not found")
                all_exist = False
                
        return all_exist
        
    def check_config_files(self) -> bool:
        """Check if configuration files exist and are valid JSON."""
        self.print_section("Configuration Files Check")
        
        config_files = [
            'options.json', 'filter.json', 'user_management.json', 
            'voices.json', 'config.json'
        ]
        
        all_valid = True
        for config in config_files:
            config_path = os.path.join(self.tts_dir, 'data', config)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    self.print_result(f"Config: {config}", True)
                except json.JSONDecodeError:
                    self.print_result(f"Config: {config}", False, "Invalid JSON")
                    all_valid = False
                except Exception as e:
                    self.print_result(f"Config: {config}", False, f"Error: {e}")
                    all_valid = False
            else:
                self.print_result(f"Config: {config}", False, "File not found")
                all_valid = False
                
        return all_valid
        
    def check_logs_for_errors(self) -> bool:
        """Check logs for errors and processing steps after sending test message."""
        self.print_section("Log Analysis")
        
        # Wait for logs to be written
        time_module.sleep(5)
        
        log_files = [
            os.path.join(self.tts_dir, 'data', 'logs', 'full_log.txt'),
            os.path.join(self.tts_dir, 'data', 'logs', 'gui_messages.log')
        ]
        
        errors_found = []
        processing_steps = []
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Look for error indicators
                        error_indicators = ['ERROR', 'CRITICAL', 'FAILED', 'Exception', 'Traceback']
                        for indicator in error_indicators:
                            if indicator in content:
                                errors_found.append(f"{os.path.basename(log_file)}: {indicator}")
                        
                        # Look for processing steps
                        processing_indicators = [
                            'WebSocket message received',
                            'Message sorted/filtered successfully',
                            'Message sorted/filtered failed',
                            'TTS processing completed',
                            'TTS processing failed',
                            'Audio client and server complete',
                            'Audio client and server failed',
                            'Connected to TikFinity',
                            'Message processing error'
                        ]
                        
                        for indicator in processing_indicators:
                            if indicator in content:
                                processing_steps.append(f"{os.path.basename(log_file)}: {indicator}")
                                
                except Exception as e:
                    errors_found.append(f"Could not read {log_file}: {e}")
            else:
                errors_found.append(f"Log file not found: {log_file}")
                
        # Report processing steps
        if processing_steps:
            print("📋 Processing Steps Found:")
            for step in processing_steps:
                print(f"     ✅ {step}")
        else:
            print("❌ No processing steps found in logs")
            errors_found.append("No processing steps detected")
                
        if errors_found:
            print("❌ Errors Found:")
            for error in errors_found:
                print(f"     ❌ {error}")
            self.print_result("Log Analysis", False, f"Found {len(errors_found)} issues")
            return False
        else:
            self.print_result("Log Analysis", True, "No errors found in logs")
            return True
            
    def check_audio_system(self) -> bool:
        """Check audio system status."""
        self.print_section("Audio System Check")
        
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.quit()
            self.print_result("Pygame Audio", True)
        except Exception as e:
            self.print_result("Pygame Audio", False, f"Error: {e}")
            return False
            
        try:
            from pycaw.pycaw import AudioUtilities
            devices = AudioUtilities.GetSpeakers()
            self.print_result("Windows Audio", True)
        except Exception as e:
            self.print_result("Windows Audio", False, f"Error: {e}")
            return False
            
        return True
        
    def system_type_selection(self) -> str:
        """Initial system type selection."""
        self.print_section("System Type Selection")
        
        print("\n🎯 SYSTEM DIAGNOSTIC")
        print("=" * 50)
        print("What system are you having issues with?")
        print("1. BSR Injector")
        print("2. TTS")
        
        while True:
            response = input("\nSelect option (1 or 2): ").strip()
            if response == "1":
                return "BSR"
            elif response == "2":
                return "TTS"
            else:
                print("Please enter 1 for BSR Injector or 2 for TTS.")
                
    def bsr_troubleshooting(self):
        """BSR Injector troubleshooting flow."""
        self.print_section("BSR Injector Troubleshooting")
        
        print("\n🔧 BSR INJECTOR DIAGNOSTIC")
        print("=" * 50)
        
        # Question 1: Game Type
        print("\nIs this for Beatsaber?")
        while True:
            response = input("Answer (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                # Question 2: OAuth Issue Check
                print("\nIs there any red text in game chat window or a message asking for a new 0Auth key?")
                while True:
                    oauth_response = input("Answer (y/n): ").lower().strip()
                    if oauth_response in ['y', 'yes']:
                        self.show_oauth_fix_instructions()
                        return
                    elif oauth_response in ['n', 'no']:
                        self.show_bsr_instructions()
                        return
                    else:
                        print("Please answer 'y' for yes or 'n' for no.")
            elif response in ['n', 'no']:
                self.show_bsr_instructions()
                return
            else:
                print("Please answer 'y' for yes or 'n' for no.")
                
    def show_oauth_fix_instructions(self):
        """Show OAuth fix instructions."""
        print("\n🔑 OAUTH FIX INSTRUCTIONS")
        print("=" * 50)
        print("Start game and go to http://localhost:8339/ (ctrl+click) to get a new 0auth code")
        print("and make sure you press save, after this the tool can be closed by user")
        input("\nPress Enter to continue...")
        
    def show_bsr_instructions(self):
        """Show full BSR setup instructions."""
        print("\n📋 BSR SETUP INSTRUCTIONS")
        print("=" * 50)
        print("When you have launched the program make sure you click on the BSR Injector button")
        print("to open the injector in a browser window, click on the button to get a new 0Auth token,")
        print("on the newly opened website login and select bot, then copy the top code from the 3 entries")
        print("and close that tab/window, in the bsr injector page click edit and paste the code you just")
        print("copied into the top box, then in the username box enter your twitch username, you can then")
        print("click save, once saved press connect and it should connect fine, if there is an error it will")
        print("tell you beside the connect button what is wrong, like invalid key or wrong username, this")
        print("browser must stay open while in use, if you close it no messages will be passed like bsr codes")
        print("or TikTok chat to Twitch")
        input("\nPress Enter to continue...")
                
    def interactive_audio_test(self) -> bool:
        """Interactive audio test with user confirmation and helpful feedback."""
        self.print_section("Interactive Audio Test")
        
        print("\n🎵 AUDIO TEST")
        print("=" * 50)
        print("A test TTS message should have been played.")
        print("Did you hear: 'This is a diagnostics test of Emstar233's TTS System, please wait while we check everything'?")
        
        while True:
            response = input("\nDid you hear the TTS message? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                self.print_result("Audio Test", True, "User confirmed TTS audio was heard")
                return True
            elif response in ['n', 'no']:
                self.print_result("Audio Test", False, "User did not hear TTS audio")
                self.troubleshoot_audio()
                return False
            else:
                print("Please answer 'y' for yes or 'n' for no.")
                
    def troubleshoot_audio(self):
        """Provide intelligent audio troubleshooting with logical flow."""
        print("\n🔧 AUDIO TROUBLESHOOTING")
        print("=" * 50)
        
        print("\nLet's troubleshoot your audio step by step:")
        
        # Check if they have any audio output
        print("\n1. Do you have speakers or headphones connected to your computer?")
        response = input("Answer (y/n): ").lower().strip()
        if response in ['n', 'no']:
            print("❌ You need speakers or headphones to hear audio!")
            print("💡 Connect speakers or headphones to your computer and try again.")
            input("\nPress Enter to continue...")
            return
        
        # Check if they're using headphones
        print("\n2. Are you using headphones?")
        response = input("Answer (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            print("\n3. Are your headphones plugged in and connected?")
            response = input("Answer (y/n): ").lower().strip()
            if response in ['n', 'no']:
                print("❌ Your headphones aren't connected!")
                print("💡 Plug in your headphones properly and try again.")
                input("\nPress Enter to continue...")
                return
        else:
            print("\n3. Are your speakers turned on and connected?")
            response = input("Answer (y/n): ").lower().strip()
            if response in ['n', 'no']:
                print("❌ Your speakers aren't working!")
                print("💡 Turn on your speakers and make sure they're connected properly.")
                input("\nPress Enter to continue...")
                return
        
        # Check system volume
        print("\n4. Is your Windows system volume turned up?")
        response = input("Answer (y/n): ").lower().strip()
        if response in ['n', 'no']:
            print("❌ Your system volume is too low!")
            print("💡 Turn up your Windows volume (click the speaker icon in the taskbar).")
            input("\nPress Enter to continue...")
            return
        
        # Check TTS volume
        print("\n5. Is the TTS system volume set correctly in the GUI?")
        response = input("Answer (y/n): ").lower().strip()
        if response in ['n', 'no']:
            print("❌ The TTS volume is too low!")
            print("💡 Open the TTS GUI and turn up the volume slider.")
            input("\nPress Enter to continue...")
            return
        
        # Test with other applications
        print("\n6. Can you hear audio from other applications (like YouTube)?")
        response = input("Answer (y/n): ").lower().strip()
        if response in ['n', 'no']:
            print("❌ Your audio system isn't working at all!")
            print("💡 This is a Windows audio problem, not a TTS problem.")
            print("   - Check Windows Sound settings")
            print("   - Update audio drivers")
            print("   - Try a different audio output device")
            input("\nPress Enter to continue...")
            return
        
        # If we get here, everything should be working
        print("\n✅ All audio checks passed!")
        print("💡 If you still can't hear the TTS, try:")
        print("   - Restart the TTS system")
        print("   - Check if other applications are using audio")
        print("   - Try running the diagnostic tool again")
        
        input("\nPress Enter to continue...")
        
    def check_api_endpoints(self) -> bool:
        """Check if API endpoints are responding."""
        self.print_section("API Endpoints Check")
        
        # Check if the WebSocket server is responding
        try:
            import websockets
            async def test_connection():
                try:
                    async with websockets.connect('ws://localhost:21213/', timeout=5):
                        return True
                except:
                    return False
                    
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_connection())
            loop.close()
            
            if result:
                self.print_result("API Endpoints", True, "WebSocket server responding")
                return True
            else:
                self.print_result("API Endpoints", False, "WebSocket server not responding")
                return False
                
        except Exception as e:
            self.print_result("API Endpoints", False, f"Error: {e}")
            return False
            
    def generate_report(self):
        """Generate a comprehensive diagnostic report."""
        self.print_section("Diagnostic Report")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! Your TTS system is working correctly.")
        else:
            print(f"\n⚠️ {failed_tests} test(s) failed. Please review the issues above.")
            
        # Save report to file in diagnostics folder
        report_path = os.path.join(self.script_dir, f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"TTS System Diagnostic Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Tests: {total_tests}\n")
                f.write(f"Passed: {passed_tests}\n")
                f.write(f"Failed: {failed_tests}\n")
                f.write(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n\n")
                
                for test_name, result in self.test_results.items():
                    status = "PASS" if result else "FAIL"
                    f.write(f"{status}: {test_name}\n")
                    
            print(f"\n📄 Report saved to: {report_path}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")
            
    def wait_for_user_start(self):
        """Wait for user to manually start TTS system and detect all connections."""
        self.print_section("Manual TTS Start")
        
        print("\n🎮 MANUAL START REQUIRED")
        print("=" * 50)
        print("Please click the 'Start TTS' button in the GUI window.")
        print("This tests both GUI responsiveness and the start process.")
        print(f"\nWaiting for TTS system to connect to diagnostic WebSocket server...")
        print("Expected: TTS system will connect to ws://localhost:21213/")
        
        # Wait for WebSocket connections
        max_wait = 60  # 60 seconds timeout
        start_time = time_module.time()
        
        while time_module.time() - start_time < max_wait:
            # Check if all expected processes are running
            running_processes = self.verify_expected_processes()
            
            # Check WebSocket connections
            connection_count = len(connected_clients)
            
            print(f"\r⏳ Waiting... Processes: {len(running_processes)}/{len(self.expected_connections)}, Connections: {connection_count}", end="", flush=True)
            
            # Success condition: all processes running and at least one connection
            if len(running_processes) == len(self.expected_connections) and connection_count > 0:
                print(f"\n✅ All expected processes running and {connection_count} WebSocket connection(s) detected!")
                return True
                
            time_module.sleep(1)
        
        print(f"\n❌ Timeout waiting for TTS system to start")
        print(f"Processes found: {len(running_processes)}/{len(self.expected_connections)}")
        print(f"WebSocket connections: {len(connected_clients)}")
        print("\n💡 Troubleshooting:")
        print("- Ensure you clicked the 'Start TTS' button in the GUI")
        print("- Check if the TTS system is trying to connect to ws://localhost:21213/")
        print("- The diagnostic tool is running a WebSocket server that the TTS system should connect to")
        return False

    def verify_expected_processes(self):
        """Check if all expected TTS processes are running."""
        running_processes = set()
        
        for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline:
                    for expected in self.expected_connections:
                        if any(expected in arg for arg in cmdline):
                            running_processes.add(expected)
                            break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return running_processes

    def run_diagnostics(self):
        """Run the complete diagnostic suite."""
        self.print_header("Unified Diagnostic Tool")
        print(f"Starting comprehensive diagnostics at {datetime.now().strftime('%H:%M:%S')}")
        
        # Phase 0: System Type Selection
        system_type = self.system_type_selection()
        
        if system_type == "BSR":
            # BSR Injector troubleshooting
            self.bsr_troubleshooting()
            print(f"\n🏁 BSR diagnostics completed at {datetime.now().strftime('%H:%M:%S')}")
            input("\nPress Enter to exit...")
            sys.exit(0)
        else:
            # TTS System diagnostics
            self.run_tts_diagnostics()
            
    def run_tts_diagnostics(self):
        """Run the TTS diagnostic suite."""
        self.print_header("TTS System Diagnostic Tool")
        
        # Phase 1: Automated System Preparation
        print("\n🔧 Phase 1: System Preparation")
        if not self.check_tikfinity_process():
            return
            
        if not self.check_gui_process():
            return
            
        if not self.check_python_version():
            return
            
        if not self.check_required_packages():
            return
            
        if not self.check_ffmpeg():
            return
            
        if not self.check_tts_files():
            return
            
        if not self.check_config_files():
            return
            
        if not self.check_audio_system():
            return
            
        # Phase 2: Start WebSocket Server and Launch GUI
        print("\n🚀 Phase 2: Start WebSocket Server and Launch GUI")
        
        # Start WebSocket server FIRST (this is the fake TikFinity)
        print("\n🚀 Starting WebSocket server (fake TikFinity)...")
        if not self.start_websocket_server():
            return
            
        # Now launch the GUI
        if not self.launch_gui():
            return
            
        # Wait for user to manually start TTS
        if not self.wait_for_user_start():
            return
            
        # Phase 3: Automated Testing
        print("\n🧪 Phase 3: Automated Testing")
        
        # Send test message
        test_message = "This is a diagnostics test of Emstar233's TTS System, please wait while we check everything"
        
        # Wait 4-5 seconds for TTS system to fully start before sending message
        print("⏳ Waiting 5 seconds for TTS system to fully initialize...")
        time_module.sleep(5)
        
        self.send_test_message(test_message)
        
        # Wait and check logs
        time_module.sleep(10)
        
        # Check logs for errors
        self.check_logs_for_errors()
        
        # Check API endpoints
        self.check_api_endpoints()
        
        # Interactive audio test
        self.interactive_audio_test()
        
        # Generate report
        self.generate_report()
        
        print(f"\n🏁 TTS diagnostics completed at {datetime.now().strftime('%H:%M:%S')}")
        
        # Keep window open and actually exit
        input("\nPress Enter to exit...")
        sys.exit(0)

def main():
    """Main entry point."""
    diagnostics = UnifiedDiagnostics()
    
    try:
        diagnostics.run_diagnostics()
    except KeyboardInterrupt:
        print("\n🛑 Diagnostics interrupted by user")
        input("Press Enter to exit...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Diagnostic error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
