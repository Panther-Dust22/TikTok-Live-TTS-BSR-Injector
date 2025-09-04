#!/usr/bin/env python3
"""
TTS System GUI V4.0 - OVERHAUL
Comprehensive interface for managing the TTS Voice System
Created by Emstar233 & Husband (V4)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
import threading
import time
from datetime import datetime
import subprocess
# Windows-specific flag for hiding console windows
CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
import psutil
import webbrowser
from io import StringIO
import sys

# Import our helper functions
try:
    from get_active_users import get_active_users, get_user_count
    TRACKER_AVAILABLE = True
except ImportError:
    TRACKER_AVAILABLE = False

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

# Windows Audio Session Management
try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, AudioSession
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

class TTSAudioSessionManager:
    """Controls the audio queue server's audio session"""
    
    def __init__(self):
        # No session creation - just control the existing one
        pass
    
    def get_session_volume(self):
        """Get the current volume level from the TTS Voice System session (0.0 to 1.0)"""
        try:
            if not AUDIO_AVAILABLE:
                return 1.0
                
            # Get all audio sessions
            sessions = AudioUtilities.GetAllSessions()
            
            # Find the TTS Voice System session (audio queue server)
            for session in sessions:
                if session.Process and hasattr(session.Process, 'name'):
                    process_name = session.Process.name().lower()
                    # Look for Python process that has the TTS Voice System title
                    if 'python' in process_name and session.ProcessId:
                        try:
                            session_volume = session.SimpleAudioVolume
                            # Get the current volume from this session
                            return session_volume.GetMasterVolume()
                        except:
                            continue
            
            return 1.0  # Default if no session found
            
        except Exception:
            return 1.0  # Default volume if can't read
    
    def set_session_volume(self, volume_level):
        """Set the volume of the TTS Voice System session (0.0 to 1.0)"""
        try:
            if not AUDIO_AVAILABLE:
                return
                
            # Get all audio sessions
            sessions = AudioUtilities.GetAllSessions()
            
            # Find the TTS Voice System session (audio queue server)
            for session in sessions:
                if session.Process and hasattr(session.Process, 'name'):
                    process_name = session.Process.name().lower()
                    # Look for Python process that has the TTS Voice System title
                    if 'python' in process_name and session.ProcessId:
                        try:
                            session_volume = session.SimpleAudioVolume
                            # Clamp volume between 0.0 and 1.0 (0% to 100%)
                            clamped_volume = max(0.0, min(1.0, volume_level))
                            session_volume.SetMasterVolume(clamped_volume, None)
                            return
                        except:
                            continue
            
        except Exception:
            pass  # Silent failure
    
    def shutdown(self):
        """No cleanup needed - we don't own the session"""
        pass

class TTSSystemGUIV4:
    def __init__(self):
        try:
            # Log initialization
            write_log("GUI initialized", "INFO")
            print("🚀 GUI __init__ started")
            
            self.setup_window()
            print("✅ Window setup complete")
            self.load_configurations()
            print("✅ Configurations loaded")
            self.create_layout()
            print("✅ Layout created")
            self.start_background_updates()
            print("✅ Background updates started")
            self.main_process = None
            self.output_thread = None
            self.user_tracker_process = None
            self.emergency_stop_process = None
            self.audio_queue_process = None
            self.api_monitor_process = None
            self.crash_detector_process = None
            self.voice_commands_enabled = False
            self.active_processes = []  # Track all subprocesses for cleanup
            self.system_running = False
            self.emergency_stop_running = False
            
            # Start background services on first run
            print("🚀 Starting background services...")
            self.log_to_console("🚀 Starting background services...")
            self.start_background_services()
            print("✅ Background services started")
            
            # Start crash detector (runs independently)
            print("🔍 About to call start_crash_detector()...")
            self.log_to_console("🔍 About to call start_crash_detector()...")
            write_log("GUI about to call start_crash_detector()", "INFO")
            self.start_crash_detector()
            print("✅ Crash detector call completed")
            
        except Exception as e:
            print(f"❌ Error in GUI __init__: {e}")
            write_log(f"Error in GUI __init__: {e}", "ERROR")
            import traceback
            traceback.print_exc()
        
        self.gui_log_file = "data/logs/gui_messages.log"
        self.last_log_position = 0
        self.update_button_states()
        
        # Check for updates on startup
        self.root.after(2000, self.check_updates)  # Check after 2 seconds
        
        # Start GUI message monitoring
        self.monitor_gui_messages()
        
        # Start queue size monitoring
        self.monitor_queue_size()
        
    def setup_window(self):
        """Initialize the main window"""
        self.root = tk.Tk()
        self.root.title("TTS Voice System V4.0 - OVERHAUL")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_configurations(self):
        """Load configuration files"""
        self.configs = {}
        self.available_voices = []
        
        config_files = [
            'data/options.json',
            'data/user_management.json', 
            'data/voices.json',
            'data/config.json',
            'data/filter.json'
        ]
        
        for config_file in config_files:
            try:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_name = os.path.basename(config_file).replace('.json', '')
                        self.configs[config_name] = json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading {config_file}: {e}")
                
        # Extract voice names from voices.json
        self.extract_voice_names()
        
    def extract_voice_names(self):
        """Extract all voice names from voices.json"""
        self.available_voices = []
        
        if 'voices' in self.configs:
            voice_data = self.configs['voices'].get('Voice_List_cheat_sheet', {})
            
            # Extract voice names from all categories
            for category, voices in voice_data.items():
                if isinstance(voices, list):
                    for voice in voices:
                        if isinstance(voice, dict) and 'name' in voice:
                            self.available_voices.append(voice['name'])
                    
        # Sort voices alphabetically
        self.available_voices.sort()
            
    def refresh_user_management_data(self):
        """Refresh user_management.json data from disk"""
        try:
            user_management_file = 'data/user_management.json'
            if os.path.exists(user_management_file):
                with open(user_management_file, 'r', encoding='utf-8') as f:
                    self.configs['user_management'] = json.load(f)
                    self.log_to_console("🔄 Refreshed user management data from disk")
            else:
                self.log_to_console("⚠️ User management file not found")
        except Exception as e:
            self.log_to_console(f"❌ Error refreshing user management data: {e}")
            
    def create_layout(self):
        """Create the main layout based on the design"""
        
        # ===== TOP STATIC HEADER =====
        self.create_header()
        
        # ===== MAIN CONTENT AREA =====
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left side - Console/Command window info (exactly half width)
        left_frame = tk.Frame(main_frame, bg='#1a1a1a', relief='ridge', bd=2)
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 5))
        left_frame.config(width=700)  # Fixed half width
        
        console_label = tk.Label(left_frame, text="Command Window Information", 
                                bg='#1a1a1a', fg='white', font=('Arial', 12, 'bold'))
        console_label.pack(pady=5)
        
        self.console_text = scrolledtext.ScrolledText(
            left_frame, 
            bg='#000000', 
            fg='#00ff00',
            font=('Consolas', 9),
            wrap=tk.WORD,
            height=30
        )
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Right side - Split into controls (top) and browser (bottom)
        right_frame = tk.Frame(main_frame, bg='#2b2b2b')
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Top half of right side - Controls
        controls_frame = tk.Frame(right_frame, bg='#2b2b2b')
        controls_frame.pack(fill="x", pady=(0, 5))
        
        self.create_controls(controls_frame)
        
                # Bottom half of right side - BSR Injector button
        self.create_bsr_section(right_frame)
        
    def create_header(self):
        """Create the static decorative header"""
        header_frame = tk.Frame(self.root, bg='#000000', relief='ridge', bd=3)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Create the sparkly border and content
        header_text = """✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨
✨         TTS Voice System V4.0            ✨
✨                OVERHAUL                  ✨
✨       ___ __  __    ___ ________         ✨
✨      | __|  \\/  |/\\|_  )__ /__ /         ✨
✨      | _|| |\\/| >  </ / |_ \\|_ \\         ✨
✨      |___|_|  |_|\\//___|___/___/         ✨
✨💫 Created by Emstar233 & Husband (V4) 💫✨
✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨"""
        
        header_label = tk.Label(
            header_frame,
            text=header_text,
            bg='#000000',
            fg='#ffff00',
            font=('Courier New', 10, 'bold'),
            justify='center'
        )
        header_label.pack(pady=10)
        
    def create_controls(self, parent):
        """Create the control panel on the right side"""
        
        # Row 1 - Main control buttons
        button_frame1 = tk.Frame(parent, bg='#2b2b2b')
        button_frame1.pack(fill="x", pady=5)
        
        self.start_main_btn = tk.Button(button_frame1, text="Start TTS", 
                                       command=self.toggle_main_system, bg='#F44336', fg='white',
                                       font=('Arial', 9, 'bold'), width=15, height=2)
        self.start_main_btn.pack(side="left", padx=2)
        

        
        self.tts_cmd_btn = tk.Button(button_frame1, text="!tts Command\nDisabled", 
                                   command=self.toggle_tts_command, bg='#F44336', fg='white',
                                   font=('Arial', 9, 'bold'), width=10, height=2)
        self.tts_cmd_btn.pack(side="left", padx=2)
        
        self.mod_cmd_btn = tk.Button(button_frame1, text="Mod Commands\nDisabled", 
                                      command=self.toggle_moderator_commands, bg='#F44336', fg='white',
                                      font=('Arial', 9, 'bold'), width=15, height=2)
        self.mod_cmd_btn.pack(side="left", padx=2)
        
        # Specials button
        self.specials_btn = tk.Button(button_frame1, text="Specials", 
                                      command=self.open_specials_window, bg='#FF9800', fg='white',
                                      font=('Arial', 9, 'bold'), width=10, height=2)
        self.specials_btn.pack(side="left", padx=2)
        
        # Bad word filter button
        self.filter_btn = tk.Button(button_frame1, text="Edit Bad Word\nFilter & Reply", 
                                   command=self.edit_filter, bg='#F44336', fg='white',
                                   font=('Arial', 9, 'bold'), width=15, height=2)
        self.filter_btn.pack(side="left", padx=2)
        
        # Emergency stop button
        self.emergency_btn = tk.Button(button_frame1, text="🚨 Emergency Stop\nDaemon", 
                                       command=self.toggle_emergency_stop, bg='#800000', fg='white',
                                       font=('Arial', 9, 'bold'), width=15, height=2)
        self.emergency_btn.pack(side="left", padx=2)
        
        # BSR Injector button
        self.bsr_btn = tk.Button(button_frame1, text="BSR Injector", 
                                command=self.open_bsr_injector, bg='#FF6600', fg='white',
                                font=('Arial', 9, 'bold'), width=12, height=2)
        self.bsr_btn.pack(side="left", padx=2)
        
        # Row 2 - Dropdowns and controls
        controls_frame1 = tk.Frame(parent, bg='#2b2b2b')
        controls_frame1.pack(fill="x", pady=5)
        
        # Active users dropdown
        users_frame = tk.Frame(controls_frame1, bg='#2b2b2b')
        users_frame.pack(side="left", padx=2)
        tk.Label(users_frame, text="Active Users:", bg='#2b2b2b', fg='white', font=('Arial', 8)).pack()
        self.users_var = tk.StringVar()
        self.users_dropdown = ttk.Combobox(users_frame, textvariable=self.users_var, 
                                          width=12, state="readonly")
        self.users_dropdown.pack()
        self.users_dropdown.bind('<<ComboboxSelected>>', self.on_user_selected)
        self.start_auto_refresh()  # start live updates
        
        # Voices dropdown  
        voices_frame = tk.Frame(controls_frame1, bg='#2b2b2b')
        voices_frame.pack(side="left", padx=2)
        tk.Label(voices_frame, text="Voices:", bg='#2b2b2b', fg='white', font=('Arial', 8)).pack()
        self.voice_var = tk.StringVar()
        self.voice_dropdown = ttk.Combobox(voices_frame, textvariable=self.voice_var,
                                          values=self.available_voices, width=35)
        self.voice_dropdown.pack()
        
        # Name swap entry
        nameswap_frame = tk.Frame(controls_frame1, bg='#2b2b2b')
        nameswap_frame.pack(side="left", padx=2)
        tk.Label(nameswap_frame, text="Name Swap:", bg='#2b2b2b', fg='white', font=('Arial', 8)).pack()
        self.nameswap_var = tk.StringVar()
        self.nameswap_entry = tk.Entry(nameswap_frame, textvariable=self.nameswap_var, width=15)
        self.nameswap_entry.pack()
        
        # Speed dropdown
        speed_frame = tk.Frame(controls_frame1, bg='#2b2b2b')
        speed_frame.pack(side="left", padx=2)
        tk.Label(speed_frame, text="Speed:", bg='#2b2b2b', fg='white', font=('Arial', 8)).pack()
        self.speed_var = tk.StringVar(value="None")
        speed_values = ["None"] + [str(x/10) for x in range(1, 21)]  # None, 0.1 to 2.0
        self.speed_dropdown = ttk.Combobox(speed_frame, textvariable=self.speed_var,
                                          values=speed_values, width=6)
        self.speed_dropdown.pack()
        
        # Voice control buttons in separate frame
        voice_buttons_frame = tk.Frame(controls_frame1, bg='#2b2b2b')
        voice_buttons_frame.pack(side="left", padx=2)
        tk.Label(voice_buttons_frame, text="", bg='#2b2b2b', fg='white', font=('Arial', 8)).pack()
        
        # Apply Voice Settings button
        self.apply_voice_btn = tk.Button(voice_buttons_frame, text="Apply", 
                                        command=self.apply_voice_settings, bg='#607D8B', fg='white',
                                        font=('Arial', 8, 'bold'), width=8)
        self.apply_voice_btn.pack(side="left")
        
        # Remove Voice Settings button
        self.remove_voice_btn = tk.Button(voice_buttons_frame, text="Remove", 
                                         command=self.remove_voice_settings, bg='#F44336', fg='white',
                                         font=('Arial', 8, 'bold'), width=8)
        self.remove_voice_btn.pack(side="left", padx=(2, 0))
        
        # Edit Priority List button
        self.edit_priority_btn = tk.Button(voice_buttons_frame, text="Edit List", 
                                          command=self.open_priority_list_window, bg='#9C27B0', fg='white',
                                          font=('Arial', 8, 'bold'), width=8)
        self.edit_priority_btn.pack(side="left", padx=(2, 0))
        
        # Row 3 - More controls
        controls_frame2 = tk.Frame(parent, bg='#2b2b2b')
        controls_frame2.pack(fill="x", pady=5)
        

        

        

        
        # Row 3 - Volume slider (its own row)
        volume_frame = tk.Frame(parent, bg='#2b2b2b')
        volume_frame.pack(fill="x", pady=5)
        tk.Label(volume_frame, text="TTS Volume:", bg='#2b2b2b', fg='white', font=('Arial', 8)).pack()
        
        # Initialize volume slider with current audio session volume
        current_volume = self.get_audio_volume()
        self.volume_var = tk.DoubleVar(value=current_volume)
        self.volume_slider = tk.Scale(volume_frame, from_=0.0, to=1.0, resolution=0.05,
                                     orient=tk.HORIZONTAL, variable=self.volume_var,
                                     bg='#2b2b2b', fg='white', highlightbackground='#2b2b2b',
                                     command=self.on_volume_change)
        self.volume_slider.pack(fill="x")
        
        # Row 4 - Updates and actions
        actions_frame = tk.Frame(parent, bg='#2b2b2b')
        actions_frame.pack(fill="x", pady=5)
        
        # Queue size display
        self.queue_display = tk.Label(actions_frame, text=" MSG Queue \n\n0", 
                                     bg='#000000', fg='#00ff00', 
                                     font=('Consolas', 10),
                                     width=10, height=3,
                                     relief='ridge', bd=2, anchor='center')
        self.queue_display.pack(side="left", padx=5)
        
        # GitHub updates check
        self.update_btn = tk.Button(actions_frame, text="No updates", 
                                   command=self.check_updates, bg='#795548', fg='white',
                                   font=('Arial', 10, 'bold'))
        self.update_btn.pack(side="left", padx=5)
        
        # API Performance Test button
        self.api_test_btn = tk.Button(actions_frame, text="Test API\nPerformance", 
                                     command=self.test_api_performance, bg='#2196F3', fg='white',
                                     font=('Arial', 10, 'bold'))
        self.api_test_btn.pack(side="left", padx=5)
        
    def create_bsr_section(self, parent):
        """Create BSR Integration Coming Soon section"""
        bsr_frame = tk.Frame(parent, bg='#1a1a1a', relief='ridge', bd=2)
        bsr_frame.pack(fill="x", pady=(10, 0))
    
        link = "https://discord.gg/PVvv8M5e83"

        bsr_label = tk.Label(
            bsr_frame,
            text=f"BSR Integration Coming Soon | Discord {link}",
            bg='#1a1a1a',
            fg='blue',  # hyperlink color
            cursor="hand2",  # pointer hand on hover
            font=('Arial', 14, 'bold', 'underline')  # underline for link style
        )
        bsr_label.pack(pady=20)

        # Bind click event
        bsr_label.bind("<Button-1>", lambda e: webbrowser.open(link))

            
    def create_html_preview(self, html_content):
        """Create a simplified preview of HTML content"""
        try:
            import re
            
            # Remove HTML tags but keep content
            text_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
            text_content = re.sub(r'<style.*?</style>', '', text_content, flags=re.DOTALL)
            text_content = re.sub(r'<[^>]+>', '', text_content)
            
            # Clean up whitespace
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Create a nice preview
            preview = "📄 WEBPAGE PREVIEW:\n"
            preview += "=" * 50 + "\n\n"
            
            if text_content:
                # Show first 500 characters
                if len(text_content) > 500:
                    preview += text_content[:500] + "...\n\n"
                else:
                    preview += text_content + "\n\n"
            else:
                preview += "This webpage contains interactive content.\n\n"
                
            preview += "=" * 50 + "\n"
            preview += "🖱️ Click anywhere to open in full browser"
            
            return preview
            
        except Exception as e:
            return f"📄 HTML Content Loaded\n\n🖱️ Click to open in full browser\n\nPreview error: {e}"
            
    def load_html_content(self, html_content, file_path):
        """Load HTML content into the browser widget"""
        try:
            if self.browser_type == "tkhtml":
                # Use tkinter.html if available
                self.browser_widget.delete("1.0", tk.END)
                self.browser_widget.insert("1.0", html_content)
            elif self.browser_type == "tkinterweb":
                # Use tkinterweb for proper HTML rendering with JavaScript
                self.browser_widget.load_file(file_path)
            elif self.browser_type == "webview":
                # Use webview for better rendering
                import webview
                # Create webview window embedded in the frame
                webview.create_window('Index.html', url=f"file://{os.path.abspath(file_path)}", 
                                    width=400, height=300)
            else:
                # Fallback to text widget with better HTML rendering
                self.browser_text.delete("1.0", tk.END)
                
                # Simple HTML-to-text converter with basic formatting
                display_content = self.render_html_as_text(html_content)
                self.browser_text.insert("1.0", display_content)
                
                # Make links clickable by binding to external browser
                self.setup_link_handling(html_content)
                
        except Exception as e:
            self.log_to_console(f"❌ Failed to load HTML content: {e}")
            
    def render_html_as_text(self, html_content):
        """Convert HTML to readable text with basic formatting"""
        try:
            import re
            
            # Remove script and style tags
            content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
            content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL)
            
            # Convert common HTML tags to readable text formatting
            content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n=== \1 ===\n', content, flags=re.DOTALL)
            content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.DOTALL)
            content = re.sub(r'<br[^>]*>', '\n', content)
            content = re.sub(r'<div[^>]*>(.*?)</div>', r'\1\n', content, flags=re.DOTALL)
            
            # Enhanced button and link handling
            content = re.sub(r'<button[^>]*onclick=["\']([^"\']*)["\'][^>]*>(.*?)</button>', r'🔘 [\2] (Action: \1)', content, flags=re.DOTALL)
            content = re.sub(r'<button[^>]*>(.*?)</button>', r'🔘 [\1] (Clickable)', content, flags=re.DOTALL)
            content = re.sub(r'<input[^>]*type=["\']button["\'][^>]*value=["\']([^"\']*)["\'][^>]*onclick=["\']([^"\']*)["\'][^>]*>', r'🔘 [\1] (Action: \2)', content)
            content = re.sub(r'<input[^>]*type=["\']button["\'][^>]*value=["\']([^"\']*)["\'][^>]*>', r'🔘 [\1] (Clickable)', content)
            content = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'🔗 [\2] (Link: \1)', content, flags=re.DOTALL)
            
            # Remove remaining HTML tags
            content = re.sub(r'<[^>]+>', '', content)
            
            # Clean up whitespace
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r'[ \t]+', ' ', content)
            
            return content.strip()
            
        except Exception as e:
            return f"HTML Content (Error rendering: {e})\n\n{html_content[:500]}..."
            
    def setup_link_handling(self, html_content):
        """Setup click handling for buttons and links in the HTML"""
        try:
            import re
            
            # Find all buttons and links
            buttons = re.findall(r'<button[^>]*onclick=["\']([^"\']*)["\'][^>]*>', html_content)
            links = re.findall(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>', html_content)
            
            # For simplicity, make the entire text widget clickable to open external browser
            def open_external(event):
                try:
                    index_paths = ["data/index.html", "index.html", "web/index.html"]
                    for path in index_paths:
                        if os.path.exists(path):
                            webbrowser.open(f"file://{os.path.abspath(path)}")
                            self.log_to_console("🌐 Opened external browser for full functionality")
                            break
                except Exception as e:
                    self.log_to_console(f"❌ Failed to open external browser: {e}")
                    
            self.browser_text.bind("<Button-1>", open_external)
            
        except Exception as e:
            self.log_to_console(f"⚠️ Error setting up link handling: {e}")
        
    def log_to_console(self, message):
        """Add message to console window"""
        # Only add timestamp for GUI-specific messages, not main.py output
        if message.startswith(("🚀", "✅", "❌", "📄", "💾", "⚠️")):
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
        else:
            formatted_message = f"{message}\n"
        
        self.console_text.insert(tk.END, formatted_message)
        self.console_text.see(tk.END)
        
        # Limit console to last 1000 lines
        lines = self.console_text.get("1.0", tk.END).split('\n')
        if len(lines) > 1000:
            self.console_text.delete("1.0", f"{len(lines)-1000}.0")
            
    def monitor_gui_messages(self):
        """Monitor the GUI log file for new messages from main.py"""
        try:
            if os.path.exists(self.gui_log_file):
                with open(self.gui_log_file, 'r', encoding='utf-8') as f:
                    f.seek(self.last_log_position)
                    new_content = f.read()
                    if new_content:
                        # Split into lines and process each
                        lines = new_content.strip().split('\n')
                        for line in lines:
                            if line.strip():
                                # Remove timestamp from main.py output (format: "HH:MM:SS | message")
                                if " | " in line:
                                    # Extract just the message part after the timestamp
                                    message_part = line.split(" | ", 1)[1]
                                    self.console_text.insert(tk.END, f"{message_part}\n")
                                elif "|" in line and len(line.split("|")) == 2:
                                    # Handle format without spaces around |
                                    parts = line.split("|")
                                    if len(parts) == 2 and parts[0].strip().count(":") == 2:
                                        # Looks like a timestamp (HH:MM:SS)
                                        message_part = parts[1].strip()
                                        self.console_text.insert(tk.END, f"{message_part}\n")
                                    else:
                                        # Not a timestamp, insert as-is
                                        self.console_text.insert(tk.END, f"{line}\n")
                                else:
                                    # If no timestamp format, insert as-is
                                    self.console_text.insert(tk.END, f"{line}\n")
                                self.console_text.see(tk.END)
                        self.last_log_position = f.tell()
            else:
                # Create the log file if it doesn't exist
                try:
                    with open(self.gui_log_file, 'w', encoding='utf-8') as f:
                        f.write("")
                except Exception:
                    pass
        except Exception as e:
            # Only show error once to avoid spam
            if not hasattr(self, '_log_error_shown'):
                self.console_text.insert(tk.END, f"Log monitor error: {e}\n")
                self.console_text.see(tk.END)
                self._log_error_shown = True

        # Schedule next check
        self.root.after(100, self.monitor_gui_messages)  # Check more frequently (100ms)
            
    def start_main_system(self):
        """Start main.pyw process and ensure background services are running"""
        try:
            if self.main_process and self.main_process.poll() is None:
                self.log_to_console("❌ Main system is already running!")
                return
                
            # Clear console and reset log position
            self.console_text.delete("1.0", tk.END)
            self.last_log_position = 0
            
            # Clear both log files to prevent stale messages
            try:
                # Clear GUI log file
                with open(self.gui_log_file, 'w', encoding='utf-8') as f:
                    f.write("")
                # Clear full log file
                with open("data/logs/full_log.txt", 'w', encoding='utf-8') as f:
                    f.write("")
            except Exception:
                pass
            
            # Show starting status
            self.log_to_console("🚀 Starting TTS Main System...")
            self.log_to_console(f"📁 Working directory: {os.getcwd()}")
            
            # Ensure background services are running
            self.log_to_console("🔧 Ensuring background services are running...")
            self.start_background_services()
            
            # Start main process
            self.start_main_process()
            
            if self.system_running:
                self.start_main_btn.configure(text="Stop TTS", bg='#4CAF50')
                self.log_to_console("✅ Main system started successfully!")
            else:
                self.log_to_console("❌ Failed to start main system")
            
        except Exception as e:
            self.log_to_console(f"❌ Failed to start main system: {e}")
            write_log(f"Failed to start main system: {e}", "ERROR")
            
    def monitor_process_output(self):
        """Monitor the main.pyw process output in background"""
        try:
            while self.main_process and self.main_process.poll() is None:
                # Check stdout
                if self.main_process.stdout:
                    stdout_line = self.main_process.stdout.readline()
                    if stdout_line:
                        self.log_to_console(f"[STDOUT] {stdout_line.strip()}")
                
                # Check stderr
                if self.main_process.stderr:
                    stderr_line = self.main_process.stderr.readline()
                    if stderr_line:
                        self.log_to_console(f"[STDERR] {stderr_line.strip()}")
                    
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            # Process has ended, get final output
            if self.main_process and self.main_process.stdout and self.main_process.stderr:
                try:
                    stdout, stderr = self.main_process.communicate()
                    if stdout:
                        self.log_to_console(f"[FINAL STDOUT] {stdout}")
                    if stderr:
                        self.log_to_console(f"[FINAL STDERR] {stderr}")
                    self.log_to_console(f"🛑 Main system stopped (exit code: {self.main_process.returncode})")
                except Exception:
                    self.log_to_console("🛑 Main system stopped")
            else:
                self.log_to_console("🛑 Main system stopped")
                
        except Exception as e:
            self.log_to_console(f"❌ Process monitor error: {e}")
    
    def stop_main_system(self):
        """Stop all TTS services"""
        try:
            self.log_to_console("🛑 Stopping all TTS services...")
            
            # Stop ESD first if it's running to prevent it from restarting main.pyw
            if self.emergency_stop_running:
                self.log_to_console("🛑 Stopping ESD first to prevent auto-restart...")
                self.stop_emergency_stop()
                # Wait for ESD to fully shut down before stopping other services
                self.log_to_console("⏳ Waiting for ESD to fully shut down...")
                time.sleep(2)
            
            # Stop all services
            self.stop_all_services()
            
            # Update button state
            self.start_main_btn.configure(text="Start TTS", bg='#F44336')
            self.log_to_console("✅ All TTS services stopped")
            
        except Exception as e:
            self.log_to_console(f"❌ Failed to stop TTS services: {e}")
            write_log(f"Failed to stop TTS services: {e}", "ERROR")
            

            
    def toggle_main_system(self):
        """Toggle main.py system on/off"""
        if self.system_running:
            self.stop_main_system()
        else:
            # Temporarily disable button to prevent multiple clicks
            self.start_main_btn.configure(state='disabled')
            self.start_main_system()
            # Re-enable button after a short delay
            self.root.after(2000, lambda: self.start_main_btn.configure(state='normal'))
            
    def toggle_tts_command(self):
        """Toggle A_ttscode in options.json"""
        try:
            if 'options' not in self.configs:
                self.configs['options'] = {}
                
            current_value = self.configs['options'].get('A_ttscode', 'FALSE')
            new_value = 'TRUE' if current_value == 'FALSE' else 'FALSE'
            
            self.configs['options']['A_ttscode'] = new_value
            self.save_config('options')
            
            if new_value == 'TRUE':
                self.tts_cmd_btn.configure(text="!tts Command\nEnabled", bg='#4CAF50')
                self.log_to_console("✅ !tts command ENABLED")
            else:
                self.tts_cmd_btn.configure(text="!tts Command\nDisabled", bg='#F44336')
                self.log_to_console("❌ !tts command DISABLED")
                
        except Exception as e:
            self.log_to_console(f"❌ Failed to toggle !tts command: {e}")
            
    def toggle_moderator_commands(self):
        """Toggle Voice_change.Enabled in options.json"""
        try:
            if 'options' not in self.configs:
                self.configs['options'] = {}
            if 'Voice_change' not in self.configs['options']:
                self.configs['options']['Voice_change'] = {}
                
            current_value = self.configs['options']['Voice_change'].get('Enabled', 'TRUE')
            new_value = 'FALSE' if current_value == 'TRUE' else 'TRUE'
            
            self.configs['options']['Voice_change']['Enabled'] = new_value
            self.save_config('options')
            
            if new_value == 'TRUE':
                self.mod_cmd_btn.configure(text="Mod Commands\nEnabled", bg='#4CAF50')
                self.log_to_console("✅ Moderator commands ENABLED")
            else:
                self.mod_cmd_btn.configure(text="Mod Commands\nDisabled", bg='#F44336')
                self.log_to_console("❌ Moderator commands DISABLED")
                
        except Exception as e:
            self.log_to_console(f"❌ Failed to toggle moderator commands: {e}")
            
    def on_user_selected(self, event):
        """Auto-populate settings when user is selected"""
        try:
            selected_user = self.users_var.get().strip()
            if not selected_user:
                return
                
            # Refresh user_management.json data before populating
            self.refresh_user_management_data()
            
            # Clear current settings
            self.voice_var.set("")
            self.speed_var.set("None")
            self.nameswap_var.set("")
            
            # Get user's current settings from user_management.json
            user_mgmt = self.configs.get('user_management', {})
            
            # Check priority voice
            priority_voices = user_mgmt.get('C_priority_voice', {})
            
            if selected_user in priority_voices:
                voice_data = priority_voices[selected_user]
                
                if isinstance(voice_data, dict):
                    # Voice with speed
                    for voice, speed in voice_data.items():
                        self.voice_var.set(voice)
                        self.speed_var.set(speed)
                        break
                else:
                    # Just voice
                    self.voice_var.set(voice_data)
                    
            # Check name swap
            name_swaps = user_mgmt.get('E_name_swap', {})
            
            if selected_user in name_swaps:
                self.nameswap_var.set(name_swaps[selected_user])
                
        except Exception as e:
            self.log_to_console(f"❌ Error auto-populating user settings: {e}")
            print(f"Error auto-populating user settings: {e}")
            
    def apply_voice_settings(self):
        """Apply voice settings to selected user"""
        try:
            user = self.users_var.get().strip()
            voice = self.voice_var.get().strip()
            speed = self.speed_var.get().strip()
            nameswap = self.nameswap_var.get().strip()
            
            if not user:
                self.log_to_console("❌ Please select a user first")
                return
                
            # Initialize user_management config if it doesn't exist
            if 'user_management' not in self.configs:
                self.configs['user_management'] = {}
                
            # Update priority voice settings
            if voice:
                priority_voices = self.configs['user_management'].setdefault('C_priority_voice', {})
                
                if speed and speed != "None":
                    priority_voices[user] = {voice: speed}
                    self.log_to_console(f"✅ Set {user}: {voice} @ {speed}x speed")
                else:
                    priority_voices[user] = voice
                    self.log_to_console(f"✅ Set {user}: {voice} @ default speed")
                    
            # Handle name swap
            if nameswap:
                name_swaps = self.configs['user_management'].setdefault('E_name_swap', {})
                name_swaps[user] = nameswap
                self.log_to_console(f"✅ Name swap: {user} -> {nameswap}")
                
            # Save changes to user_management.json
            self.save_config('user_management')
            self.log_to_console(f"💾 Voice settings saved for {user}")
                
        except Exception as e:
            self.log_to_console(f"❌ Failed to apply voice settings: {e}")
    
    def remove_voice_settings(self):
        """Remove voice settings for selected user from priority voices"""
        try:
            selected_user = self.users_var.get().strip()
            
            if not selected_user:
                self.log_to_console("❌ Please select a user first")
                return
            
            # Get current priority voices
            user_mgmt = self.configs.get('user_management', {})
            priority_voices = user_mgmt.get('C_priority_voice', {})
            
            # Check if user has a priority voice
            if selected_user in priority_voices:
                # Remove the user from priority voices
                del priority_voices[selected_user]
                
                # Save the updated configuration
                self.save_config('user_management')
                
                # Clear the voice and speed dropdowns
                self.voice_var.set("")
                self.speed_var.set("None")
                
                self.log_to_console(f"✅ Removed voice settings for {selected_user}")
                
                # Update the users dropdown to refresh the list
                self.update_users_dropdown()
            else:
                self.log_to_console(f"❌ {selected_user} doesn't have any voice settings to remove")
                
        except Exception as e:
            self.log_to_console(f"❌ Failed to remove voice settings: {e}")
    
    def open_priority_list_window(self):
        """Open the priority voice list editor window"""
        self.priority_window = tk.Toplevel(self.root)
        self.priority_window.title("Priority Voice List Editor")
        self.priority_window.geometry("600x500")
        self.priority_window.configure(bg='#2b2b2b')
        self.priority_window.transient(self.root)
        self.priority_window.grab_set()
        
        # Title
        title_label = tk.Label(self.priority_window, text="Priority Voice List", 
                              bg='#2b2b2b', fg='white', font=('Arial', 14, 'bold'))
        title_label.pack(pady=(10, 20))
        
        # Create scrollable frame
        canvas = tk.Canvas(self.priority_window, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.priority_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Get current priority voices
        user_mgmt = self.configs.get('user_management', {})
        priority_voices = user_mgmt.get('C_priority_voice', {})
        
        if not priority_voices:
            # No priority voices
            no_voices_label = tk.Label(scrollable_frame, text="No priority voices set", 
                                     bg='#2b2b2b', fg='#888888', font=('Arial', 12))
            no_voices_label.pack(pady=20)
        else:
            # Create list of priority voices
            for username, voice_data in priority_voices.items():
                entry_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
                entry_frame.pack(fill="x", padx=10, pady=2)
                
                # Username
                username_label = tk.Label(entry_frame, text=f"{username}:", 
                                        bg='#2b2b2b', fg='white', font=('Arial', 10), width=25, anchor="w")
                username_label.pack(side="left")
                
                # Voice info
                if isinstance(voice_data, dict):
                    # Voice with speed
                    for voice, speed in voice_data.items():
                        voice_info = f"{voice} @ {speed}x"
                        break
                else:
                    # Just voice
                    voice_info = str(voice_data)
                
                voice_label = tk.Label(entry_frame, text=voice_info, 
                                     bg='#2b2b2b', fg='#00ff00', font=('Arial', 10))
                voice_label.pack(side="left", padx=(10, 0))
                
                # Remove button
                remove_btn = tk.Button(entry_frame, text="Remove", 
                                     command=lambda u=username: self.remove_priority_user(u, entry_frame), 
                                     bg='#F44336', fg='white', font=('Arial', 8, 'bold'), width=8)
                remove_btn.pack(side="right", padx=(10, 0))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        close_btn = tk.Button(self.priority_window, text="Close", 
                             command=self.priority_window.destroy, bg='#607D8B', fg='white',
                             font=('Arial', 10, 'bold'), width=15)
        close_btn.pack(pady=10)
    
    def remove_priority_user(self, username, entry_frame):
        """Remove a user from the priority voice list"""
        try:
            # Get current priority voices
            user_mgmt = self.configs.get('user_management', {})
            priority_voices = user_mgmt.get('C_priority_voice', {})
            
            # Remove the user
            if username in priority_voices:
                del priority_voices[username]
                
                # Save the updated configuration
                self.save_config('user_management')
                
                # Remove the entry frame from the UI
                entry_frame.destroy()
                
                # Refresh the popup to show updated list
                self.refresh_priority_popup()
                
                self.log_to_console(f"✅ Removed {username} from priority voice list")
            else:
                self.log_to_console(f"❌ {username} not found in priority voice list")
                
        except Exception as e:
            self.log_to_console(f"❌ Failed to remove {username}: {e}")
    
    def refresh_priority_popup(self):
        """Refresh the priority voice popup list"""
        try:
            # Find the scrollable frame
            for widget in self.priority_window.winfo_children():
                if isinstance(widget, tk.Canvas):
                    for canvas_child in widget.winfo_children():
                        if isinstance(canvas_child, tk.Frame):
                            # Clear the frame
                            for child in canvas_child.winfo_children():
                                child.destroy()
                            
                            # Get updated priority voices
                            user_mgmt = self.configs.get('user_management', {})
                            priority_voices = user_mgmt.get('C_priority_voice', {})
                            
                            if not priority_voices:
                                # No priority voices
                                no_voices_label = tk.Label(canvas_child, text="No priority voices set", 
                                                         bg='#2b2b2b', fg='#888888', font=('Arial', 12))
                                no_voices_label.pack(pady=20)
                            else:
                                # Recreate list of priority voices
                                for username, voice_data in priority_voices.items():
                                    entry_frame = tk.Frame(canvas_child, bg='#2b2b2b')
                                    entry_frame.pack(fill="x", padx=10, pady=2)
                                    
                                    # Username
                                    username_label = tk.Label(entry_frame, text=f"{username}:", 
                                                            bg='#2b2b2b', fg='white', font=('Arial', 10), width=25, anchor="w")
                                    username_label.pack(side="left")
                                    
                                    # Voice info
                                    if isinstance(voice_data, dict):
                                        # Voice with speed
                                        for voice, speed in voice_data.items():
                                            voice_info = f"{voice} @ {speed}x"
                                            break
                                    else:
                                        # Just voice
                                        voice_info = str(voice_data)
                                    
                                    voice_label = tk.Label(entry_frame, text=voice_info, 
                                                         bg='#2b2b2b', fg='#00ff00', font=('Arial', 10))
                                    voice_label.pack(side="left", padx=(10, 0))
                                    
                                    # Remove button
                                    remove_btn = tk.Button(entry_frame, text="Remove", 
                                                         command=lambda u=username: self.remove_priority_user(u, entry_frame), 
                                                         bg='#F44336', fg='white', font=('Arial', 8, 'bold'), width=8)
                                    remove_btn.pack(side="right", padx=(10, 0))
                            break
        except Exception as e:
            self.log_to_console(f"❌ Error refreshing priority popup: {e}")
            

    
    def open_specials_window(self):
        """Open the specials configuration window"""
        self.specials_window = tk.Toplevel(self.root)
        self.specials_window.title("Special Voice Settings")
        self.specials_window.geometry("800x700")
        self.specials_window.configure(bg='#2b2b2b')
        self.specials_window.transient(self.root)
        self.specials_window.grab_set()
        
        # Create main frame with scrollbar
        main_frame = tk.Frame(self.specials_window, bg='#2b2b2b')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Special Voice Settings", 
                              bg='#2b2b2b', fg='white', font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Default speed section
        speed_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
        speed_frame.pack(fill="x", pady=10)
        
        speed_label = tk.Label(speed_frame, text="Default Speed:", 
                              bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold'))
        speed_label.pack(anchor="w")
        
        speed_input_frame = tk.Frame(speed_frame, bg='#2b2b2b')
        speed_input_frame.pack(fill="x", pady=5)
        
        self.default_speed_popup_var = tk.StringVar(value="1.0")
        speed_entry = tk.Entry(speed_input_frame, textvariable=self.default_speed_popup_var, 
                              width=10, bg='#3b3b3b', fg='white', insertbackground='white')
        speed_entry.pack(side="left")
        
        speed_help = tk.Label(speed_input_frame, text="(0.1 to 2.0)", 
                             bg='#2b2b2b', fg='#888888', font=('Arial', 8))
        speed_help.pack(side="left", padx=(5, 0))
        
        # Voice mapping section
        voice_mapping_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
        voice_mapping_frame.pack(fill="x", pady=10)
        
        voice_mapping_label = tk.Label(voice_mapping_frame, text="Voice Mapping:", 
                                      bg='#2b2b2b', fg='white', font=('Arial', 10, 'bold'))
        voice_mapping_label.pack(anchor="w")
        
        # Get current voice mappings
        current_mappings = self.configs.get('options', {}).get('D_voice_map', {})
        
        # Voice mapping options with proper labels
        voice_options = [
            ("Subscriber Voice", "Subscriber"),
            ("Moderator Voice", "Moderator"),
            ("Everyone", "Follow Role 0"),
            ("Follower Voice", "Follow Role 1"),
            ("Friend", "Follow Role 2"),
            ("Top Gifter 1", "Top Gifter 1"),
            ("Top Gifter 2", "Top Gifter 2"),
            ("Top Gifter 3", "Top Gifter 3"),
            ("Top Gifter 4", "Top Gifter 4"),
            ("Top Gifter 5", "Top Gifter 5"),
            ("Filter Reply Voice", "BadWordVoice"),
            ("Default", "Default")
        ]
        
        # Create dropdown variables and widgets
        self.voice_mapping_vars = {}
        
        for display_name, config_key in voice_options:
            option_frame = tk.Frame(voice_mapping_frame, bg='#2b2b2b')
            option_frame.pack(fill="x", pady=5)
            
            label = tk.Label(option_frame, text=f"{display_name}:", 
                           bg='#2b2b2b', fg='white', font=('Arial', 9), width=20, anchor="w")
            label.pack(side="left")
            
            # Create dropdown with all voices + NONE option
            dropdown_var = tk.StringVar(value=current_mappings.get(config_key, "NONE"))
            self.voice_mapping_vars[config_key] = dropdown_var
            
            dropdown = ttk.Combobox(option_frame, textvariable=dropdown_var,
                                   values=["NONE"] + self.available_voices, 
                                   width=35, state="readonly")
            dropdown.pack(side="left", padx=(10, 0))
        
        # Buttons frame
        buttons_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
        buttons_frame.pack(fill="x", pady=20)
        
        save_btn = tk.Button(buttons_frame, text="Save Settings", 
                            command=self.save_specials, bg='#4CAF50', fg='white',
                            font=('Arial', 10, 'bold'), width=15, height=2)
        save_btn.pack(side="left", padx=5)
        
        cancel_btn = tk.Button(buttons_frame, text="Cancel", 
                              command=self.specials_window.destroy, bg='#F44336', fg='white',
                              font=('Arial', 10, 'bold'), width=15, height=2)
        cancel_btn.pack(side="left", padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load current default speed from config.json
        current_default_speed = self.configs.get('config', {}).get('playback_speed', 1.0)
        self.default_speed_popup_var.set(str(current_default_speed))
    
    def save_specials(self):
        """Save the special settings to options.json"""
        try:
            # Update voice mappings
            voice_mappings = {}
            for config_key, var in self.voice_mapping_vars.items():
                voice_mappings[config_key] = var.get()
            
            # Update options.json
            if 'options' not in self.configs:
                self.configs['options'] = {}
            
            self.configs['options']['D_voice_map'] = voice_mappings
            
            # Save voice mappings to options.json
            self.save_config('options')
            
            # Save default speed to config.json
            if 'config' not in self.configs:
                self.configs['config'] = {}
            
            try:
                speed_float = float(self.default_speed_popup_var.get())
                if speed_float <= 0 or speed_float > 3.0:
                    self.log_to_console("❌ Speed must be between 0.1 and 3.0")
                    return
                self.configs['config']['playback_speed'] = speed_float
                self.save_config('config')
            except ValueError:
                self.log_to_console("❌ Invalid speed value")
                return
            
            self.log_to_console("✅ Special settings saved successfully")
            self.specials_window.destroy()
            
        except Exception as e:
            self.log_to_console(f"❌ Failed to save special settings: {e}")
    
    def open_bsr_injector(self):
        """Open BSR Injector in browser"""
        try:
            import webbrowser
            index_path = os.path.join("data", "index.html")
            if os.path.exists(index_path):
                webbrowser.open(f"file://{os.path.abspath(index_path)}")
            else:
                webbrowser.open("https://twitchtokengenerator.com/")
        except Exception as e:
            self.log_to_console(f"❌ Failed to open BSR Injector: {e}")
            
    def edit_filter(self):
        """Open bad word filter editor"""
        filter_window = tk.Toplevel(self.root)
        filter_window.title("Bad Word Filter & Reply Editor")
        filter_window.geometry("800x500")
        filter_window.configure(bg='#2b2b2b')
        
        # Load latest data from disk so GUI reflects external changes (e.g., !vrude)
        try:
            with open(os.path.join("data", "filter.json"), 'r', encoding='utf-8') as f:
                latest_filter = json.load(f)
        except Exception:
            latest_filter = {}
        if 'filter' not in self.configs:
            self.configs['filter'] = {}
        self.configs['filter'].update(latest_filter)
        
        # Use refreshed values
        filter_data = self.configs.get('filter', {}).get('B_word_filter', [])
        reply_data = self.configs.get('filter', {}).get('B_filter_reply', [])
        
        # Main container
        main_frame = tk.Frame(filter_window, bg='#2b2b2b')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Bad Words
        left_frame = tk.Frame(main_frame, bg='#2b2b2b')
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        tk.Label(left_frame, text="Bad Words (one per line):", 
                bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold')).pack(pady=(0, 5))
        
        self.filter_text = scrolledtext.ScrolledText(left_frame, height=20, bg='#1a1a1a', fg='white',
                                                   insertbackground='white', selectbackground='#3d3d3d')
        self.filter_text.pack(fill="both", expand=True)
        self.filter_text.focus_set()  # Set cursor focus
        
        # Populate with current filter words
        if filter_data and len(filter_data) > 0:
            self.filter_text.insert("1.0", "\n".join(str(word) for word in filter_data))
        else:
            self.filter_text.insert("1.0", "# Add bad words here, one per line\n# Example:\n# badword1\n# badword2")
            
        # Right side - Reply Messages
        right_frame = tk.Frame(main_frame, bg='#2b2b2b')
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        tk.Label(right_frame, text="Reply Messages (one per line):", 
                bg='#2b2b2b', fg='white', font=('Arial', 12, 'bold')).pack(pady=(0, 5))
        
        self.reply_text = scrolledtext.ScrolledText(right_frame, height=20, bg='#1a1a1a', fg='white',
                                                  insertbackground='white', selectbackground='#3d3d3d')
        self.reply_text.pack(fill="both", expand=True)
        
        # Populate with current reply messages
        if reply_data and len(reply_data) > 0:
            self.reply_text.insert("1.0", "\n".join(str(reply) for reply in reply_data))
        else:
            self.reply_text.insert("1.0", "# Add reply messages here, one per line\n# These are sent when bad words are detected\n# Example:\n# Please keep chat family friendly!\n# That language is not allowed")
            
        # Save button
        button_frame = tk.Frame(filter_window, bg='#2b2b2b')
        button_frame.pack(fill="x", padx=10, pady=5)
        
        def save_filter():
            # Save bad words
            filter_content = self.filter_text.get("1.0", tk.END).strip()
            words = [word.strip() for word in filter_content.split('\n') 
                    if word.strip() and not word.strip().startswith('#')]
            
            # Save reply messages
            reply_content = self.reply_text.get("1.0", tk.END).strip()
            replies = [reply.strip() for reply in reply_content.split('\n') 
                      if reply.strip() and not reply.strip().startswith('#')]
            
            if 'filter' not in self.configs:
                self.configs['filter'] = {}
                
            self.configs['filter']['B_word_filter'] = words
            self.configs['filter']['B_filter_reply'] = replies
            
            self.save_config('filter')
            # Reload from disk after save to keep GUI cache in sync
            try:
                with open(os.path.join("data", "filter.json"), 'r', encoding='utf-8') as f:
                    self.configs['filter'] = json.load(f)
            except Exception:
                pass
            filter_window.destroy()
            
        save_btn = tk.Button(button_frame, text="Save Filter & Replies", command=save_filter,
                           bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'))
        save_btn.pack(pady=5)
        
    def toggle_emergency_stop(self):
        """Toggle emergency stop daemon on/off"""
        if self.emergency_stop_running:
            self.stop_emergency_stop()
        else:
            self.start_emergency_stop()
            
    def start_emergency_stop(self):
        """Start emergency stop daemon"""
        try:
            if self.emergency_stop_process and self.emergency_stop_process.poll() is None:
                self.log_to_console("❌ Emergency stop daemon is already running!")
                return
                
            # Start TTSESD.pyw as a background process (capture stdout/stderr into files)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            ttsesd_path = os.path.join(script_dir, 'TTSESD.pyw')
            try:
                logs_dir = os.path.join(script_dir, 'data', 'logs')
                os.makedirs(logs_dir, exist_ok=True)
                esd_out = open(os.path.join(logs_dir, 'ttsesd_subprocess.out.log'), 'a', encoding='utf-8')
                esd_err = open(os.path.join(logs_dir, 'ttsesd_subprocess.err.log'), 'a', encoding='utf-8')
            except Exception as log_err:
                esd_out = subprocess.DEVNULL
                esd_err = subprocess.DEVNULL
                write_log(f"Failed to open ESD stdout/stderr logs: {log_err}", "WARNING")

            self.emergency_stop_process = subprocess.Popen(
                ['py', ttsesd_path],
                stdout=esd_out,
                stderr=esd_err,
                creationflags=CREATE_NO_WINDOW,
                cwd=script_dir
            )
            
            self.emergency_stop_running = True
            self.emergency_btn.configure(text="🚨 Emergency Stop\nDaemon ACTIVE", bg='#4CAF50')
            self.log_to_console("✅ Emergency stop daemon started")
            
        except Exception as e:
            self.log_to_console(f"❌ Failed to start emergency stop daemon: {e}")
            
    def stop_emergency_stop(self):
        """Stop emergency stop daemon"""
        try:
            if self.emergency_stop_process:
                self.emergency_stop_process.terminate()
                self.emergency_stop_process = None
                # Close log files if we opened them
                try:
                    if 'esd_out' in locals() and esd_out not in (None, subprocess.DEVNULL):
                        esd_out.close()
                    if 'esd_err' in locals() and esd_err not in (None, subprocess.DEVNULL):
                        esd_err.close()
                except Exception:
                    pass
                
            # Also kill any python processes running TTSESD.pyw
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'TTSESD.pyw' in cmdline:
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            self.emergency_stop_running = False
            self.emergency_btn.configure(text="🚨 Emergency Stop\nDaemon", bg='#800000')
            self.log_to_console("🛑 Emergency stop daemon stopped")
            
        except Exception as e:
            self.log_to_console(f"❌ Failed to stop emergency stop daemon: {e}")
            write_log(f"Failed to stop emergency stop daemon: {e}", "ERROR")
    
    def handle_esd_activation(self):
        """Handle ESD activation - update GUI state only (ESD handles process management)"""
        try:
            self.log_to_console("🚨 ESD ACTIVATED - Updating GUI state...")
            
            # Update GUI state only - ESD handles the actual process management
            self.system_running = False
            self.root.after(0, self.update_start_stop_button)
            
            self.log_to_console("✅ GUI state updated for ESD activation")
            
        except Exception as e:
            self.log_to_console(f"❌ Error handling ESD activation: {e}")
            write_log(f"Error handling ESD activation: {e}", "ERROR")
                
    def check_updates(self):
        """Check for GitHub updates via GitHub API"""
        try:
            import requests
            from packaging import version

            # Your current version
            current_version = "v4"  # Update this when you release a new version

            # GitHub API endpoint for the latest release
            api_url = "https://api.github.com/repos/Panther-Dust22/TikTok-Live-TTS-BSR-Injector/releases/latest"

            # Fetch the latest release info
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            latest_version = data.get("tag_name", "").lower()

            if latest_version:
                # Compare versions numerically
                if version.parse(latest_version) > version.parse(current_version):
                    # Update available
                    self.update_btn.configure(text="Update Available!", bg='#F44336')
                    self.log_to_console(f"🆕 Update available! Latest version: {latest_version}")
                    self.flash_update_button()
                else:
                    # No update (latest is same or older)
                    self.update_btn.configure(text="No updates", bg='#795548')
                    self.log_to_console(f"✅ No updates available (current {current_version}, latest {latest_version})")
            else:
                # Could not determine latest version
                self.update_btn.configure(text="No updates", bg='#795548')
                self.log_to_console("✅ No updates available (could not read latest version)")

        except Exception as e:
            self.log_to_console(f"❌ Failed to check updates: {e}")
            self.update_btn.configure(text="Check Failed", bg='#FF9800')
    
    def flash_update_button(self):
        """Flash the update button to draw attention"""
        try:
            if hasattr(self, '_flash_count'):
                self._flash_count += 1
            else:
                self._flash_count = 0
            
            if self._flash_count < 6:  # Flash 3 times (6 color changes)
                if self._flash_count % 2 == 0:
                    self.update_btn.configure(bg='#F44336')  # Red
                else:
                    self.update_btn.configure(bg='#FF9800')  # Orange
                
                # Schedule next flash
                self.root.after(500, self.flash_update_button)
            else:
                # Stop flashing, keep red
                self.update_btn.configure(bg='#F44336')
                self._flash_count = 0
        except Exception as e:
            self.log_to_console(f"❌ Error flashing update button: {e}")
    
    def update_queue_display(self, queue_size):
        """Update the queue size display"""
        if hasattr(self, 'queue_display'):
            self.queue_display.configure(text=f" MSG Queue \n\n{queue_size}")
    
    def monitor_queue_size(self):
        """Monitor the queue size from full_log.txt"""
        try:
            full_log_path = "data/logs/full_log.txt"
            if os.path.exists(full_log_path):
                with open(full_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Look for the most recent queue size update
                    for line in reversed(lines):
                        if 'Queue size:' in line:
                            # Extract the queue size number
                            try:
                                queue_size = line.split('Queue size:')[1].strip()
                                self.update_queue_display(queue_size)
                                break
                            except:
                                pass
        except Exception as e:
            # Silently handle errors
            pass
        
        # Schedule next check
        self.root.after(500, self.monitor_queue_size)  # Check every 500ms for better responsiveness
    
    def open_github_page(self):
        """Open the GitHub repository page"""
        try:
            import webbrowser
            webbrowser.open("https://github.com/Panther-Dust22/TikTok-Live-TTS-BSR-Injector")
        except Exception as e:
            self.log_to_console(f"❌ Failed to open GitHub page: {e}")
    
    def test_api_performance(self):
        """Test API performance with 10 different tests using different words and voices"""
        try:
            self.log_to_console("🚀 Starting comprehensive API performance test (5 runs)...")
            
            # Test data with different words and voices (reduced to 5 tests)
            test_data = [
                {"text": "Hello world, this is a test message.", "voice": "EN_US_MALE_1"},
                {"text": "Welcome to the voice system.", "voice": "EN_US_FEMALE_1"},
                {"text": "Testing different voices and speeds.", "voice": "EN_UK_MALE_1"},
                {"text": "Performance evaluation in progress.", "voice": "EN_AU_FEMALE_1"},
                {"text": "Checking API reliability and speed.", "voice": "EN_US_MALE_2"}
            ]
            
            # Run performance test using the TTS module
            import subprocess
            import sys
            
            all_results = []
            
            for i, test in enumerate(test_data, 1):
                self.log_to_console(f"📊 Test {i}/5: '{test['text'][:30]}...' with {test['voice']}")
                
                # Run the TTS script with --retest flag
                process = subprocess.Popen([
                    'py', '-3.12', "TTS.pyw",
                    "-v", test['voice'],
                    "-t", test['text'],
                    "--retest"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
                
                # Track the process for cleanup
                self.active_processes.append(process)
                
                try:
                    result = process.communicate(timeout=90)  # Increased timeout to 90 seconds
                    stdout, stderr = result
                    returncode = process.returncode
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    raise subprocess.TimeoutExpired(process.args, 90)
                finally:
                    # Remove from active processes list
                    if process in self.active_processes:
                        self.active_processes.remove(process)
                
                if returncode == 0:
                    # Parse and display the results
                    output_lines = stdout.split('\n')
                    for line in output_lines:
                        if line.strip() and any(keyword in line for keyword in ['[START]', '[INFO]', '[OK]', '[FAIL]', '[WARN]', '->', '[RETEST]']):
                            self.log_to_console(f"   {line.strip()}")
                    
                    all_results.append(f"Test {i}: [OK] Success")
                else:
                    self.log_to_console(f"   ❌ Test {i} failed: {stderr}")
                    all_results.append(f"Test {i}: [FAIL] Failed")
                
                # Brief delay between tests
                time.sleep(1)
            
            # Save results to configuration
            self.save_performance_results(all_results)
            
            self.log_to_console("[OK] Comprehensive API performance test completed!")
            self.log_to_console(f"[INFO] Results: {len([r for r in all_results if '[OK]' in r])}/5 tests successful")
            
        except subprocess.TimeoutExpired:
            self.log_to_console("❌ API performance test timed out")
        except Exception as e:
            self.log_to_console(f"❌ Failed to run API performance test: {e}")
    
    def save_performance_results(self, results):
        """Save performance test results to configuration"""
        try:
            # Load existing TTS config
            tts_config_path = "data/TTSconfig.json"
            if os.path.exists(tts_config_path):
                with open(tts_config_path, 'r', encoding='utf-8') as f:
                    tts_config = json.load(f)
            else:
                tts_config = {}
            
            # Add performance test results
            tts_config['last_performance_test'] = {
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'total_tests': len(results),
                'successful_tests': len([r for r in results if '[OK]' in r])
            }
            
            # Save updated config
            with open(tts_config_path, 'w', encoding='utf-8') as f:
                json.dump(tts_config, f, indent=4, ensure_ascii=False)
            
            self.log_to_console("💾 Performance test results saved to TTSconfig.json")
            
        except Exception as e:
            self.log_to_console(f"❌ Failed to save performance results: {e}")
        
    def save_config(self, config_name):
        """Save configuration to file"""
        try:
            config_path = f"data/{config_name}.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.configs[config_name], f, indent=4, ensure_ascii=False)
            self.log_to_console(f"💾 Saved {config_name}.json")
        except Exception as e:
            self.log_to_console(f"❌ Failed to save {config_name}: {e}")
            
    def update_users_dropdown(self):
        """Update the active users dropdown"""
        if TRACKER_AVAILABLE:
            try:
                users = get_active_users()
                self.users_dropdown['values'] = users
                if users and not self.users_var.get():
                    self.users_var.set(users[0])
            except:
                pass

    def start_auto_refresh(self):
        """Automatically refresh the active users dropdown every 2 seconds."""
        self.update_users_dropdown()  # call your existing function
        self.users_dropdown.after(2000, self.start_auto_refresh)  # repeat every 2 seconds
                
    def start_background_services(self):
        """Start all background services (first run)"""
        try:
            write_log("Starting background services", "INFO")
            
            # Start audio queue server
            self.start_audio_queue_server()
            
            # Start user tracker
            self.start_user_tracker()
            
            # Start API monitor
            self.start_api_monitor()
            

            
            self.log_to_console("✅ Background services started")
            
        except Exception as e:
            self.log_to_console(f"❌ Error starting background services: {e}")
            write_log(f"Error starting background services: {e}", "ERROR")
    
    def start_audio_queue_server(self):
        """Start audio queue server v2"""
        try:
            if not self.audio_queue_process or self.audio_queue_process.poll() is not None:
                self.audio_queue_process = subprocess.Popen(
                    ['py', '-3.12', 'audio_queue_server_v2.pyw'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=CREATE_NO_WINDOW,
                    cwd=os.getcwd()
                )
                self.active_processes.append(self.audio_queue_process)
                write_log("Audio queue server v2 started", "INFO")
        except Exception as e:
            self.log_to_console(f"⚠️ Failed to start audio queue server v2: {e}")
            write_log(f"Failed to start audio queue server v2: {e}", "ERROR")
    
    def start_user_tracker(self):
        """Start user tracker"""
        try:
            if not self.user_tracker_process or self.user_tracker_process.poll() is not None:
                self.user_tracker_process = subprocess.Popen(
                    ['py', '-3.12', 'user_tracker.pyw'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=CREATE_NO_WINDOW,
                    cwd=os.getcwd()
                )
                self.active_processes.append(self.user_tracker_process)
                write_log("User tracker started", "INFO")
        except Exception as e:
            self.log_to_console(f"⚠️ Failed to start user tracker: {e}")
            write_log(f"Failed to start user tracker: {e}", "ERROR")
    
    def start_api_monitor(self):
        """Start API monitor"""
        try:
            if not self.api_monitor_process or self.api_monitor_process.poll() is not None:
                self.api_monitor_process = subprocess.Popen(
                    ['py', '-3.12', 'api_monitor.pyw'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=CREATE_NO_WINDOW,
                    cwd=os.getcwd()
                )
                self.active_processes.append(self.api_monitor_process)
                write_log("API monitor started", "INFO")
        except Exception as e:
            self.log_to_console(f"⚠️ Failed to start API monitor: {e}")
            write_log(f"Failed to start API monitor: {e}", "ERROR")
    
    def start_crash_detector(self):
        """Start crash detector (runs independently)"""
        try:
            self.log_to_console("🔍 Attempting to start crash detector...")
            write_log("GUI attempting to start crash detector", "INFO")
            
            if not self.crash_detector_process or self.crash_detector_process.poll() is not None:
                self.log_to_console("🔍 Crash detector process check passed, starting...")
                write_log("Crash detector process check passed, starting subprocess", "INFO")
                
                self.crash_detector_process = subprocess.Popen(
                    ['py', '-3.12', 'crash_detector.pyw'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=CREATE_NO_WINDOW,
                    cwd=os.getcwd()
                )
                self.active_processes.append(self.crash_detector_process)
                self.log_to_console(f"✅ Crash detector started with PID: {self.crash_detector_process.pid}")
                write_log(f"Crash detector started with PID: {self.crash_detector_process.pid}", "INFO")
            else:
                self.log_to_console("⚠️ Crash detector already running, skipping start")
                write_log("Crash detector already running, skipping start", "INFO")
        except Exception as e:
            self.log_to_console(f"❌ Failed to start crash detector: {e}")
            write_log(f"Failed to start crash detector: {e}", "ERROR")
    
    def stop_all_services(self):
        """Stop all TTS-related services"""
        try:
            write_log("Stopping all TTS services", "INFO")
            
            # Stop main process
            if self.main_process and self.main_process.poll() is None:
                try:
                    self.main_process.terminate()
                    self.main_process.wait(timeout=3)
                except:
                    try:
                        self.main_process.kill()
                    except:
                        pass
            
            # Stop audio queue server
            if self.audio_queue_process and self.audio_queue_process.poll() is None:
                try:
                    self.audio_queue_process.terminate()
                    self.audio_queue_process.wait(timeout=3)
                except:
                    try:
                        self.audio_queue_process.kill()
                    except:
                        pass
            
            # Stop user tracker
            if self.user_tracker_process and self.user_tracker_process.poll() is None:
                try:
                    self.user_tracker_process.terminate()
                    self.user_tracker_process.wait(timeout=3)
                except:
                    try:
                        self.user_tracker_process.kill()
                    except:
                        pass
            
            # Stop API monitor
            if self.api_monitor_process and self.api_monitor_process.poll() is None:
                try:
                    self.api_monitor_process.terminate()
                    self.api_monitor_process.wait(timeout=3)
                except:
                    try:
                        self.api_monitor_process.kill()
                    except:
                        pass
            
            # Stop crash detector
            if self.crash_detector_process and self.crash_detector_process.poll() is None:
                try:
                    self.crash_detector_process.terminate()
                    self.crash_detector_process.wait(timeout=3)
                except:
                    try:
                        self.crash_detector_process.kill()
                    except:
                        pass
            
            # Clear process references
            self.main_process = None
            self.audio_queue_process = None
            self.user_tracker_process = None
            self.api_monitor_process = None
            self.crash_detector_process = None
            
            # Clean up active processes list
            self.active_processes.clear()
            
            self.system_running = False
            self.log_to_console("✅ All TTS services stopped")
            
        except Exception as e:
            self.log_to_console(f"❌ Error stopping services: {e}")
            write_log(f"Error stopping services: {e}", "ERROR")
    
    def restart_all_services(self):
        """Restart all TTS services"""
        try:
            write_log("Restarting all TTS services", "INFO")
            
            self.log_to_console("🔄 Restarting TTS services...")
            
            # Stop all services first
            self.stop_all_services()
            
            # Wait a moment
            time.sleep(1)
            
            # Start background services
            self.start_background_services()
            
            # Start main process if system should be running
            if self.system_running:
                self.start_main_process()
            
            self.log_to_console("✅ All TTS services restarted")
            
        except Exception as e:
            self.log_to_console(f"❌ Error restarting services: {e}")
            write_log(f"Error restarting services: {e}", "ERROR")
    
    def start_main_process(self):
        """Start main.pyw process"""
        try:
            # Check if already running
            if self.system_running and self.main_process and self.main_process.poll() is None:
                self.log_to_console("⚠️ Main process is already running")
                return
                
            # Check if process exists but is dead
            if self.main_process and self.main_process.poll() is not None:
                self.main_process = None
                
            if not self.main_process:
                self.main_process = subprocess.Popen(
                    ['py', '-3.12', 'main.pyw'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=CREATE_NO_WINDOW,
                    cwd=os.getcwd()
                )
                self.active_processes.append(self.main_process)
                self.system_running = True
                
                write_log("Main process started", "INFO")
                
                # Start output monitoring thread
                self.start_output_monitoring()
                
        except Exception as e:
            self.log_to_console(f"❌ Failed to start main process: {e}")
            write_log(f"Failed to start main process: {e}", "ERROR")
    
    def start_output_monitoring(self):
        """Start monitoring main process output"""
        try:
            if self.main_process:
                # Start a background thread to monitor the process output
                self.output_monitor_thread = threading.Thread(target=self.monitor_process_output, daemon=True)
                self.output_monitor_thread.start()
        except Exception as e:
            self.log_to_console(f"❌ Failed to start output monitoring: {e}")
            write_log(f"Failed to start output monitoring: {e}", "ERROR")
            
    def start_background_updates(self):
        """Start background update thread"""
        self.update_thread = threading.Thread(target=self.background_update_loop, daemon=True)
        self.update_thread.start()
        
    def background_update_loop(self):
        """Background loop to update displays and monitor for ESD activation"""
        while True:
            try:
                # Update users dropdown
                self.root.after(0, self.update_users_dropdown)
                
                # Check for ESD activation (main.pyw was stopped)
                if self.system_running and (not self.main_process or self.main_process.poll() is not None):
                    self.log_to_console("🚨 ESD activation detected - main.pyw was stopped")
                    self.handle_esd_activation()
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                self.log_to_console(f"❌ Background update error: {e}")
                time.sleep(10)
                
    def find_main_process(self):
        """Find if main.pyw is currently running"""
        try:
            import psutil
            for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        cmdline_str = " ".join(cmdline).lower()
                        if "main.pyw" in cmdline_str:
                            return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return None
        except ImportError:
            return None
    
    def update_start_stop_button(self):
        """Update the start/stop button state"""
        if self.system_running:
            self.start_stop_btn.configure(text="🛑 Stop TTS", bg='#4CAF50')
        else:
            self.start_stop_btn.configure(text="▶️ Start TTS", bg='#F44336')
    
    def update_button_states(self):
        """Update button states based on current config"""
        try:
            # Update !tts command button
            tts_enabled = self.configs.get('options', {}).get('A_ttscode', 'FALSE') == 'TRUE'
            if tts_enabled:
                self.tts_cmd_btn.configure(text="!tts Command\nEnabled", bg='#4CAF50')
            else:
                self.tts_cmd_btn.configure(text="!tts Command\nDisabled", bg='#F44336')
                
            # Update moderator commands button
            mod_enabled = self.configs.get('options', {}).get('Voice_change', {}).get('Enabled', 'TRUE') == 'TRUE'
            if mod_enabled:
                self.mod_cmd_btn.configure(text="Mod Commands\nEnabled", bg='#4CAF50')
            else:
                self.mod_cmd_btn.configure(text="Mod Commands\nDisabled", bg='#F44336')
                

            
        except Exception as e:
            self.log_to_console(f"⚠️ Error updating button states: {e}")
            
    def on_volume_change(self, value):
        """Handle volume slider changes"""
        try:
            volume_level = float(value)
            # Set TTS session volume in Windows mixer
            self.set_tts_session_volume(volume_level)
            # Only log volume changes occasionally to reduce spam
            if hasattr(self, '_last_volume_log') and abs(volume_level - self._last_volume_log) >= 0.2:
                self.log_to_console(f"🔊 TTS Volume: {volume_level:.1f}")
                self._last_volume_log = volume_level
            elif not hasattr(self, '_last_volume_log'):
                self._last_volume_log = volume_level
        except Exception as e:
            self.log_to_console(f"❌ Failed to set TTS volume: {e}")
            
    def on_volume_change(self, value):
        """Handle volume slider changes"""
        try:
            volume_level = float(value)
            # Set the volume using the existing audio manager
            self.set_audio_volume(volume_level)
        except Exception as e:
            self.log_to_console(f"❌ Failed to set volume: {e}")
            
    def get_audio_volume(self):
        """Get current audio volume from the audio queue server session"""
        try:
            # Create temporary audio manager to get volume
            audio_manager = TTSAudioSessionManager()
            return audio_manager.get_session_volume()
        except Exception:
            return 1.0  # Default to 100% if error
    
    def set_audio_volume(self, volume_level):
        """Set audio volume using the audio queue server session"""
        try:
            # Create temporary audio manager to set volume
            audio_manager = TTSAudioSessionManager()
            audio_manager.set_session_volume(volume_level)
            
        except Exception as e:
            self.log_to_console(f"⚠️ Failed to set audio volume: {e}")
                
    def on_closing(self):
        """Handle window closing - thorough cleanup of all TTS processes"""
        try:
            print("🔄 GUI closing - cleaning up all TTS processes...")
            
            # Stop all TTS services first
            self.stop_all_services()
            
            # Stop emergency stop daemon if running
            if hasattr(self, 'emergency_stop_process') and self.emergency_stop_process:
                try:
                    self.emergency_stop_process.terminate()
                    self.emergency_stop_process.wait(timeout=3)
                except:
                    try:
                        self.emergency_stop_process.kill()
                    except:
                        pass
            
            # Thorough cleanup of all TTS-related Python processes
            try:
                import psutil
                current_pid = os.getpid()
                processes_to_kill = []
                
                # Find all TTS-related processes
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if (proc.info['name'] and 'python' in proc.info['name'].lower() and 
                            proc.info['pid'] != current_pid and 
                            proc.info['cmdline']):
                            
                            cmdline_str = " ".join(proc.info['cmdline']).lower()
                            
                            # Check for TTS-related scripts
                            tts_scripts = [
                                'main.pyw', 'tts.pyw', 'ttsesd.pyw', 'user_tracker.pyw',
                                'api_monitor.pyw', 'audio_queue_server.pyw', 'audio_queue_server_v2.pyw',
                                'get_active_users.pyw', 'servermain.py', 'crash_detector.pyw'
                            ]
                            
                            if any(script in cmdline_str for script in tts_scripts):
                                processes_to_kill.append(proc)
                                
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                # Terminate processes gracefully first
                for proc in processes_to_kill:
                    try:
                        print(f"🛑 Terminating process: {proc.info.get('cmdline', ['unknown'])[0]}")
                        proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Wait a moment for graceful termination
                time.sleep(2)
                
                # Force kill any remaining processes
                for proc in processes_to_kill:
                    try:
                        if proc.is_running():
                            print(f"💀 Force killing process: {proc.info.get('cmdline', ['unknown'])[0]}")
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                print(f"✅ Cleanup completed - terminated {len(processes_to_kill)} processes")
                
            except ImportError:
                print("⚠️ psutil not available - limited cleanup performed")
            except Exception as e:
                print(f"⚠️ Error during process cleanup: {e}")
                
        except Exception as e:
            print(f"⚠️ Error during GUI cleanup: {e}")
        finally:
            print("👋 GUI shutting down...")
            self.root.destroy()
        
    def run(self):
        """Start the GUI"""
        # Remove startup messages from console - console is for main.py output only
        self.root.mainloop()

if __name__ == "__main__":
    # Hide console window immediately on startup
    import ctypes
    import os
    import signal
    import sys
    
    # Global reference to app for signal handling
    app = None
    
    def signal_handler(signum, frame):
        """Handle termination signals to ensure cleanup"""
        print(f"\n🛑 Received signal {signum} - cleaning up...")
        if app:
            try:
                app.on_closing()
            except:
                pass
        sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    try:
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    except:
        pass  # Signal handling not available on all platforms
    
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
        app = TTSSystemGUIV4()
        app.run()
    except Exception as e:
        # If running with pythonw, we can't use print/input, so create a simple error window
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            messagebox.showerror("GUI Error", f"Failed to start GUI: {e}")
        except:
            pass  # If even the error window fails, just exit silently