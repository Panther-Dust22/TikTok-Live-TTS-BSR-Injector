import asyncio
import websockets
import json
import os
import subprocess
import time
import random
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



# Simple WebSocket functions for TikFinity
def create_robust_websocket(url, name, **kwargs):
    return websockets.connect(url, **kwargs), None
def close_robust_websocket(name):
    pass

# Windows Audio Session Management
try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, AudioSession
    import threading
    
    # Suppress pygame messages
    import os
    import sys
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    
    try:
        import pygame
    finally:
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr
    
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Message processing queue
message_queue = asyncio.Queue(maxsize=100)  # Configurable queue size
processing_tasks = set()  # Track background tasks

# Global variables for voice commands
C_priority_voice = {}
E_name_swap = {}

def strip_emojis_and_icons(text):
    """
    Strip emojis, icons, and other non-ASCII characters from text
    while preserving basic punctuation and alphanumeric characters
    """
    if not text:
        return text
    
    import re
    # Remove emojis and other non-ASCII characters
    # Keep alphanumeric, spaces, and basic punctuation
    cleaned = re.sub(r'[^\w\s\-_.,!?@#$%&*()+=<>[\]{}|\\/:;"\'`~]', '', text)
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# Custom Welcome Message
welcome_message = r"""
✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨
✨         TTS Voice System V4.0            ✨
✨                OVERHAUL                  ✨
✨       ___ __  __    ___ ________         ✨
✨      | __|  \/  |/\|_  )__ /__ /         ✨
✨      | _|| |\/| >  </ / |_ \|_ \         ✨
✨      |___|_|  |_|\//___|___/___/         ✨
✨💫 Created by Emstar233 & Husband (V4) 💫✨
✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨⭐✨
"""
# Fix encoding for console output
import sys
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# GUI Communication System
GUI_LOG_FILE = "data/logs/gui_messages.log"

def write_log(message, level="INFO"):
    """Write message to data/logs/full_log.txt"""
    try:
        from pathlib import Path
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}\n")
    except:
        pass

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

def clear_gui_log():
    """Clear the GUI log file and full log file"""
    try:
        import os
        # Ensure logs directory exists
        os.makedirs("data/logs", exist_ok=True)
        # Clear GUI log file
        with open(GUI_LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("")
        # Clear full log file
        with open("data/logs/full_log.txt", 'w', encoding='utf-8') as f:
            f.write("")
    except Exception:
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
    
    # Clear previous GUI log and show welcome message
    clear_gui_log()
    print(welcome_message.strip())  # Use strip() to remove extra newlines around the message
    try:
        from pathlib import Path
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] 🚀 TTS System V4.0 Started\n")
    except:
        pass
    
    # Send all console output to GUI as well
    import sys
    
    class DualOutput:
        def __init__(self, original_stdout):
            self.original = original_stdout
            
        def write(self, text):
            # Write to original console
            self.original.write(text)
            self.original.flush()
            # Also log to GUI (but avoid infinite loops)
            if text.strip() and not text.startswith('[') and 'log_to_gui' not in text:
                try:
                    # Don't log empty lines or just whitespace
                    if text.strip():
                        try:
                            from pathlib import Path
                            logs_dir = Path("data/logs")
                            logs_dir.mkdir(parents=True, exist_ok=True)
                            with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                                from datetime import datetime
                                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] {text.strip()}\n")
                        except:
                            pass
                except Exception as e:
                    # Debug: log the error to help troubleshoot
                    try:
                        import os
                        os.makedirs("data/logs", exist_ok=True)
                        with open("data/logs/gui_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"GUI log error: {e} for text: {text}\n")
                    except:
                        pass
                    
        def flush(self):
            self.original.flush()
    
    # Redirect stdout to capture all print statements
    sys.stdout = DualOutput(sys.stdout)

class TTSAudioSessionManager:
    """Manages a persistent Windows audio session for TTS volume control"""
    
    def __init__(self):
        self.session_active = False
        self.session_thread = None
        self.stop_event = threading.Event()
        if AUDIO_AVAILABLE:
            self.initialize_audio_session()
    
    def initialize_audio_session(self):
        """Initialize pygame mixer to create a persistent audio session"""
        try:
            # Suppress pygame messages
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')
            
            try:
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
                pygame.mixer.init()
                pygame.mixer.set_num_channels(1)  # Only need one channel for session
            finally:
                sys.stdout.close()
                sys.stderr.close()
                sys.stdout = original_stdout
                sys.stderr = original_stderr
            
            # Start the session maintenance thread
            self.session_thread = threading.Thread(target=self._maintain_session, daemon=True)
            self.session_thread.start()
            self.session_active = True
            
        except Exception:
            # Silent failure - don't break the system if audio session fails
            pass
    
    def _maintain_session(self):
        """Maintain the audio session by playing silent audio periodically"""
        try:
            # Create a very short silent audio buffer
            import numpy as np
            
            # Generate 0.1 seconds of silence at 22050 Hz
            sample_rate = 22050
            duration = 0.1
            samples = int(sample_rate * duration)
            
            # Create silent stereo audio (16-bit)
            silent_audio = np.zeros((samples, 2), dtype=np.int16)
            
            # Convert to pygame sound - handle different pygame versions
            try:
                # Try to initialize sndarray if available
                if hasattr(pygame.sndarray, 'init'):
                    pygame.sndarray.init()
                elif hasattr(pygame, 'sndarray'):
                    # Some versions don't need explicit init
                    pass
                    
                silent_sound = pygame.sndarray.make_sound(silent_audio)
                silent_sound.set_volume(0.01)  # Very low volume but not zero
                
                while not self.stop_event.is_set():
                    if pygame.mixer.get_init():
                        # Play silent sound every 30 seconds to maintain session
                        silent_sound.play()
                        time.sleep(0.2)  # Wait for sound to finish
                    
                    # Wait 30 seconds before next maintenance
                    self.stop_event.wait(30)
                    
            except Exception as sound_error:
                # Fallback: Create simple silence using mixer directly
                import io
                
                # Create minimal wav header for silence
                wav_data = self._create_silent_wav(duration, sample_rate)
                silent_sound = pygame.mixer.Sound(io.BytesIO(wav_data))
                silent_sound.set_volume(0.01)
                
                while not self.stop_event.is_set():
                    if pygame.mixer.get_init():
                        silent_sound.play()
                        time.sleep(0.2)
                    self.stop_event.wait(30)
                
        except Exception:
            # Silent failure - audio session maintenance failed but don't break the system
            pass
    
    def _create_silent_wav(self, duration, sample_rate):
        """Create a minimal WAV file with silence"""
        import struct
        # Calculate data size
        channels = 2
        bits_per_sample = 16
        bytes_per_sample = bits_per_sample // 8
        frame_size = channels * bytes_per_sample
        num_frames = int(sample_rate * duration)
        data_size = num_frames * frame_size
        
        # WAV header
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
                           b'RIFF', 36 + data_size, b'WAVE', b'fmt ', 16,
                           1, channels, sample_rate, sample_rate * frame_size,
                           frame_size, bits_per_sample, b'data', data_size)
        
        # Silent audio data (all zeros)
        silent_data = b'\x00' * data_size
        
        return header + silent_data
    
    def get_session_volume(self):
        """Get the current volume level from Windows mixer (0.0 to 1.0)"""
        try:
            if not AUDIO_AVAILABLE:
                return 1.0
                
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            
            # Get scalar volume (0.0 to 1.0)
            return volume.GetMasterScalarVolume()
            
        except Exception:
            return 1.0  # Default volume if can't read
    
    def set_session_volume(self, volume_level):
        """Set the session volume (0.0 to 1.0)"""
        try:
            if not AUDIO_AVAILABLE or not self.session_active:
                return
                
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            
            # Set scalar volume (0.0 to 1.0)
            volume.SetMasterScalarVolume(max(0.0, min(1.0, volume_level)), None)
            
        except Exception:
            pass  # Silent failure
    
    def shutdown(self):
        """Clean shutdown of audio session"""
        if self.session_active:
            self.stop_event.set()
            if self.session_thread and self.session_thread.is_alive():
                self.session_thread.join(timeout=5)
            
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
            except:
                pass
            
            self.session_active = False

# Initialize TTS Audio Session Manager
tts_audio_manager = TTSAudioSessionManager()

# WebSocket server URL
websocket_url = "ws://localhost:21213/"

# Load all configuration files
def load_json_file(file_path):
    """Load a JSON file with error handling"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def load_all_configs():
    """Load all configuration files"""
    return {
        'options': load_json_file(os.path.join("data", "options.json")),
        'filters': load_json_file(os.path.join("data", "filter.json")),
        'users': load_json_file(os.path.join("data", "user_management.json")),
        'voices': load_json_file(os.path.join("data", "voices.json")),
        'config': load_json_file(os.path.join("data", "config.json"))
    }

# Load all configurations
configs = load_all_configs()

# Extract settings from the new structure
A_ttscode = configs['options'].get("A_ttscode", "FALSE")
B_filter_reply = configs['filters'].get("B_filter_reply", [])
B_word_filter = configs['filters'].get("B_word_filter", [])
C_priority_voice = configs['users'].get("C_priority_voice", {})
D_voice_map = configs['options'].get("D_voice_map", {})
E_name_swap = configs['users'].get("E_name_swap", {})
Voice_change = configs['options'].get("Voice_change", {})

# Track last modification times for auto-reloading files
file_mod_times = {}

def load_settings():
    """Load all configuration data and return combined settings dictionary."""
    configs = load_all_configs()
    print("All configuration files loaded successfully.")
    write_log("✅ All configuration files loaded successfully")
    return configs

def check_for_file_updates():
    """Check if any configuration files have been updated and reload if necessary."""
    global file_mod_times, configs, A_ttscode, B_word_filter, B_filter_reply, C_priority_voice, D_voice_map, E_name_swap
    
    config_files = [
        os.path.join("data", "options.json"),
        os.path.join("data", "filter.json"),
        os.path.join("data", "user_management.json"),
        os.path.join("data", "voices.json"),
        os.path.join("data", "config.json")
    ]
    
    files_updated = False
    
    for config_file in config_files:
        try:
            # Get the current modification time of each config file
            mod_time = os.path.getmtime(config_file)
            
            # Check if the file has been modified since the last check
            if config_file not in file_mod_times or mod_time != file_mod_times[config_file]:
                file_mod_times[config_file] = mod_time
                files_updated = True
        except FileNotFoundError:
            print(f"Warning: {config_file} not found.")

    if files_updated:
        print("All settings loaded successfully")
        print()  # Add line break for clean separation
        # Reload all configurations
        configs = load_all_configs()
        if configs:
            # Reassign the global variables after loading new settings
            A_ttscode, B_word_filter, B_filter_reply, C_priority_voice, D_voice_map, E_name_swap = load_filters(configs)
            return A_ttscode, B_word_filter, B_filter_reply, C_priority_voice, D_voice_map, E_name_swap
    return None

# Load filter data
def load_file(file_path):
    try:
        # Try reading the file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except UnicodeDecodeError:
        # Fallback to a more lenient encoding (e.g., latin-1) if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as file:
            return file.read().strip()
    except FileNotFoundError:
        # Handle the case where the file is not found
        print(f"Error: {file_path} not found.")
        return None

def load_filters(configs):
    # Access values directly from the configs dictionary (which contains all config files)
    A_ttscode = configs.get('options', {}).get("A_ttscode", "FALSE") == "TRUE"
    B_word_filter = configs.get('filters', {}).get("B_word_filter", [])
    B_filter_reply = configs.get('filters', {}).get("B_filter_reply", [])
    C_priority_voice = configs.get('users', {}).get("C_priority_voice", {})
    D_voice_map = configs.get('options', {}).get("D_voice_map", {})
    E_name_swap = configs.get('users', {}).get("E_name_swap", {})
    Voice_change = configs.get('options', {}).get("Voice_change", {}).get("Enabled", "FALSE") == "TRUE"
    
    return A_ttscode, B_word_filter, B_filter_reply, C_priority_voice, D_voice_map, E_name_swap

def load_random_reply(B_filter_reply):
    if not B_filter_reply:  # If the list is empty
        return "is trying to make me say a bad word"
    return random.choice(B_filter_reply)

def is_voice_change_enabled(configs):
    # Access the "Voice_change" dictionary from configs and check if "Enabled" is "TRUE"
    Voice_change = configs.get('options', {}).get("Voice_change", {})
    return Voice_change.get("Enabled", "FALSE") == "TRUE"

import subprocess

def handle_voice_change(comment, nickname, isModerator, configs):
    global C_priority_voice, E_name_swap
    
    if not is_voice_change_enabled(configs):
        print("Voice change is disabled. Commands will not be processed.")
        return False, None, None

    if not isModerator:
        print("User is not a moderator. Ignoring voice change commands.")
        return False, None, None

    try:
        if comment.startswith("!vadd"):
            # Format: !vadd any name with spaces VOICE [speed]
            # Voice is always in CAPS, speed is optional
            command_parts = comment.split()
            if len(command_parts) >= 3:
                # Find the voice (last CAPS word) and optional speed
                voice = None
                speed = None
                target_nickname = ""
                
                # Look for voice (CAPS word) from the end
                for i in range(len(command_parts) - 1, 0, -1):
                    if command_parts[i].isupper() and len(command_parts[i]) > 1:
                        voice = command_parts[i]
                        # Check if there's a speed after the voice
                        if i + 1 < len(command_parts):
                            try:
                                speed = float(command_parts[i + 1])
                            except ValueError:
                                pass  # Not a valid speed
                        # Everything before the voice is the nickname
                        target_nickname = " ".join(command_parts[1:i]).lstrip("@")
                        break
                
                if voice and target_nickname:
                    if speed is not None:
                        msg = f"Adding voice with speed: {target_nickname} -> {voice} at {speed}x speed"
                        C_priority_voice[target_nickname] = {voice: str(speed)}
                    else:
                        msg = f"Adding voice: {target_nickname} -> {voice}"
                        C_priority_voice[target_nickname] = voice
                    
                    print(msg)
                    write_log(f"🎤 {msg}")
                    log_to_gui(f"{nickname} used {comment}")
                    save_settings(configs)
                    log_to_gui("settings updated confirmation")
                    print()
                    log_to_gui("")  # Add gap
                    return True, None, None
                else:
                    print("Invalid format. Use: !vadd name with spaces VOICE [speed]")
                    print()
                    return True, None, None

        elif comment.startswith("!vremove"):
            # Format: !vremove any name with spaces
            command_parts = comment.split()
            if len(command_parts) >= 2:
                target_nickname = " ".join(command_parts[1:]).lstrip("@")  # Everything after command is the name
                print(f"Removing voice: {target_nickname}")
                if C_priority_voice and target_nickname in C_priority_voice:
                    del C_priority_voice[target_nickname]
                    log_to_gui(f"{nickname} used {comment}")
                    save_settings(configs)
                    log_to_gui("settings updated confirmation")
                    print("Voice removed successfully")
                else:
                    print(f"No voice found for: {target_nickname}")
                print()
                log_to_gui("")  # Add gap
                return True, None, None

        elif comment.startswith("!vchange"):
            # Format: !vchange any name with spaces VOICE [speed]
            # Voice is always in CAPS, speed is optional
            command_parts = comment.split()
            if len(command_parts) >= 3:
                # Find the voice (last CAPS word) and optional speed
                voice = None
                speed = None
                target_nickname = ""
                
                # Look for voice (CAPS word) from the end
                for i in range(len(command_parts) - 1, 0, -1):
                    if command_parts[i].isupper() and len(command_parts[i]) > 1:
                        voice = command_parts[i]
                        # Check if there's a speed after the voice
                        if i + 1 < len(command_parts):
                            try:
                                speed = float(command_parts[i + 1])
                            except ValueError:
                                pass  # Not a valid speed
                        # Everything before the voice is the nickname
                        target_nickname = " ".join(command_parts[1:i]).lstrip("@")
                        break
                
                if voice and target_nickname:
                    if speed is not None:
                        msg = f"Changing voice with speed: {target_nickname} -> {voice} at {speed}x speed"
                        C_priority_voice[target_nickname] = {voice: str(speed)}
                    else:
                        msg = f"Changing voice: {target_nickname} -> {voice}"
                        C_priority_voice[target_nickname] = voice
                    
                    print(msg)
                    write_log(f"🎤 {msg}")
                    log_to_gui(f"{nickname} used {comment}")
                    save_settings(configs)
                    log_to_gui("settings updated confirmation")
                    print()
                    log_to_gui("")  # Add gap
                    return True, None, None
                else:
                    print("Invalid format. Use: !vchange name with spaces VOICE [speed]")
                    print()
                    return True, None, None

        elif comment.startswith("!vname"):
            # Format: !vname any name with spaces - new display name
            # Use - as separator between original name and new display name
            if " - " in comment:
                parts = comment.split(" - ", 1)  # Split on first occurrence of " - "
                if len(parts) == 2:
                    # Extract the original name (remove command and @)
                    original_part = parts[0].replace("!vname ", "").lstrip("@")
                    new_display_name = parts[1].strip()
                    
                    if original_part and new_display_name:
                        print(f"Adding name swap: {original_part} -> {new_display_name}")
                        E_name_swap[original_part] = new_display_name
                        log_to_gui(f"{nickname} used {comment}")
                        save_settings(configs)
                        log_to_gui("settings updated confirmation")
                        print()
                        log_to_gui("")  # Add gap
                        return True, None, None
                    else:
                        print("Invalid format. Use: !vname original name - new display name")
                        print()
                        return True, None, None
                else:
                    print("Invalid format. Use: !vname original name - new display name")
                    print()
                    return True, None, None
            else:
                print("Invalid format. Use: !vname original name - new display name")
                print()
                return True, None, None

        elif comment.startswith("!vnoname"):
            command_parts = comment.split()
            if len(command_parts) >= 2:
                # Format: !vnoname username
                target_username = command_parts[1].lstrip("@")  # Remove @ if present
                if E_name_swap and target_username in E_name_swap:
                    removed_name = E_name_swap[target_username]
                    del E_name_swap[target_username]  # Remove from name swap
                    print(f"Removing name swap: {target_username} -> {removed_name}")
                    log_to_gui(f"{nickname} used {comment}")
                    save_settings(configs)  # Save changes to file
                    log_to_gui("settings updated confirmation")
                    print()  # Add line break for clean formatting
                    log_to_gui("")  # Add gap
                    return True, None, None
                else:
                    print(f"No name swap found for: {target_username}")
                    print()  # Add line break for clean formatting
                    return True, None, None
                    
        elif comment.startswith("!vrude"):
            command_parts = comment.split()
            if len(command_parts) >= 2:
                # Format: !vrude word1 word2 word3 (can add multiple words)
                words_to_add = [w for w in command_parts[1:] if w]
                
                # Load current filter from file to preserve all existing keys
                try:
                    filter_file = os.path.join("data", "filter.json")
                    with open(filter_file, 'r', encoding='utf-8') as file:
                        filter_data = json.load(file)
                except Exception:
                    filter_data = {}
                
                current_words = filter_data.get('B_word_filter', [])
                existing_lc = {w.lower() for w in current_words}
                
                # Add new words (avoid duplicates, case-insensitive)
                new_words_added = []
                for word in words_to_add:
                    if word.lower() not in existing_lc:
                        current_words.append(word)
                        existing_lc.add(word.lower())
                        new_words_added.append(word)
                
                # Write back full filter data, preserving other fields
                filter_data['B_word_filter'] = current_words
                try:
                    with open(filter_file, 'w', encoding='utf-8') as file:
                        json.dump(filter_data, file, indent=4, ensure_ascii=False)
                    # Also update in-memory configs structure used elsewhere
                    configs['filters'] = filter_data
                    if new_words_added:
                        msg = f"Added rude words: {', '.join(new_words_added)}"
                        print(msg)
                        write_log(f"🚫 {msg}")
                    else:
                        print("No new words added (duplicates or empty)")
                except Exception as e:
                    print(f"Error saving filter file: {e}")
                
                log_to_gui(f"{nickname} used {comment}")
                log_to_gui("settings updated confirmation")
                print()  # Add line break for clean formatting
                log_to_gui("")  # Add gap
                return True, None, None

                
    except subprocess.CalledProcessError as e:
        print(f"Error executing voice command: {e}")

    return False, None, None

def save_settings(configs):
    # Save user management file with custom formatting
    user_file = os.path.join("data", "user_management.json")
    try:
        with open(user_file, 'w', encoding='utf-8') as file:
            # Custom format the JSON
            file.write("{\n")
            file.write('    "C_priority_voice": {\n')
            
            # Handle C_priority_voice with special formatting
            priority_items = list(C_priority_voice.items())
            for i, (username, voice_data) in enumerate(priority_items):
                is_last = (i == len(priority_items) - 1)
                comma = "" if is_last else ","
                
                if isinstance(voice_data, dict):
                    # Voice with speed - format on single line
                    voice_speed_json = json.dumps(voice_data, ensure_ascii=False, separators=(',', ': '))
                    file.write(f'        {json.dumps(username, ensure_ascii=False)}: {voice_speed_json}{comma}\n')
                else:
                    # Voice only - simple string
                    file.write(f'        {json.dumps(username, ensure_ascii=False)}: {json.dumps(voice_data, ensure_ascii=False)}{comma}\n')
            
            file.write('    },\n')
            file.write('    "E_name_swap": {\n')
            
            # Handle E_name_swap normally
            name_swap_items = list(E_name_swap.items())
            for i, (original, new_name) in enumerate(name_swap_items):
                is_last = (i == len(name_swap_items) - 1)
                comma = "" if is_last else ","
                file.write(f'        {json.dumps(original, ensure_ascii=False)}: {json.dumps(new_name, ensure_ascii=False)}{comma}\n')
            
            file.write('    }\n')
            file.write("}\n")
            
    except Exception as e:
        print(f"Error saving user management: {e}")

def passes_filters(data, A_ttscode, B_word_filter, B_filter_reply, C_priority_voice, D_voice_map, E_name_swap, configs):
    comment = data.get('comment', '')
    nickname = data.get('nickname', '')
    isModerator = data.get('isModerator', False)
    isSubscriber = data.get('isSubscriber', False)
    topGifterRank = data.get('topGifterRank', None)
    followRole = data.get('followRole', 0)

    # Role descriptions for display
    follow_status_display = {0: "NO", 1: "YES", 2: "FRIEND"}.get(followRole, "UNKNOWN")

    # Store original nickname for priority voice lookup
    original_nickname = nickname
    
    # Check for voice commands first (admin commands take precedence)
    voice_change_result, new_comment, voice = handle_voice_change(comment, nickname, isModerator, configs)
    if voice_change_result:
        return False, None, None, nickname  # Voice command processed, don't send to TTS

    # Block ALL voice commands and emergency stop command from TTS regardless of moderator status
    if comment.startswith(("!vadd", "!vremove", "!vchange", "!vname", "!vnoname", "!vrude", "!restart")):
        return False, None, None, nickname  # Voice command or emergency stop detected, don't send to TTS

    # Print user information in the required format (only for non-blocked commands)
    user_info = f"{nickname} | Subscriber: {isSubscriber} | Moderator: {isModerator} | Top Gifter: {topGifterRank} | Follower: {follow_status_display}"
    print(user_info)
    write_log(user_info)
    log_to_gui(user_info)
    print(f"{comment}")
    write_log(comment)
    log_to_gui(comment)

    # Convert comment to lowercase for case-insensitive comparison
    lower_comment = comment.lower()

    # PRIORITY VOICE CHECK - Uses ORIGINAL nickname for lookup (before name swap)
    priority_entry = C_priority_voice.get(original_nickname, None) if C_priority_voice else None
    
    # Priority voice lookup (debug removed)
    
    if priority_entry:
        # Handle both old format (string) and new format (dict)
        if isinstance(priority_entry, str):
            # Old format: "baker22": "DITCH"
            priority_voice = priority_entry
            priority_speed = None  # Use default speed from config
            voice_info = f"Voice: {priority_voice} | Speed: default"
            print(voice_info)
            write_log(voice_info)
            # Use nameswap name if it exists, otherwise use original nickname
            display_name = E_name_swap.get(original_nickname, nickname) if E_name_swap else nickname
            log_to_gui(f"{display_name} will use voice {priority_voice} at speed default")
            log_to_gui("")  # Add gap after voice selection
        elif isinstance(priority_entry, dict):
            # New format: "baker22": {"DITCH": "1.2"}
            priority_voice = list(priority_entry.keys())[0]  # Get the voice name
            priority_speed = priority_entry[priority_voice]  # Get the speed
            voice_info = f"Voice: {priority_voice} | Speed: {priority_speed}x"
            print(voice_info)
            write_log(voice_info)
            # Use nameswap name if it exists, otherwise use original nickname
            display_name = E_name_swap.get(original_nickname, nickname) if E_name_swap else nickname
            log_to_gui(f"{display_name} will use voice {priority_voice} at speed {priority_speed}")
            log_to_gui("")  # Add gap after voice selection
        else:
            print(f"⚠️ Invalid priority voice format for {nickname}, skipping...")
            priority_voice = None
            priority_speed = None
        
        if priority_voice:
            # Still need to do basic filtering but use priority voice
            voice = priority_voice
                # Filter A: !tts check
        if A_ttscode:
            if not comment.startswith('!tts'):
                # Apply name swap for display (before return)
                display_nickname = nickname
                if E_name_swap and original_nickname in E_name_swap:
                    display_nickname = E_name_swap[original_nickname]
                return False, None, None, display_nickname
            comment = comment[4:].strip()
        
        # For priority users, we still filter bad words but use BadWordVoice (same as everyone else)
        if B_word_filter:  # Check if B_word_filter is not None/empty
            for bad_word in B_word_filter:
                if bad_word and bad_word.lower() in lower_comment:
                    new_comment = f", {load_random_reply(B_filter_reply)}"
                    # Bad word detected - use BadWordVoice regardless of priority voice
                    
                    # Apply name swap for display (before return)
                    display_nickname = nickname
                    if E_name_swap and original_nickname in E_name_swap:
                        display_nickname = E_name_swap[original_nickname]
                    
                    # Select BadWordVoice from D_voice_map (same as non-priority users)
                    voice = D_voice_map.get('BadWordVoice', None)  # Use voice defined for bad word responses
                    if not voice:
                        # If no specific bad word voice, fallback to default
                        voice = D_voice_map.get('Default', None)
                    
                    return True, new_comment, voice, display_nickname
            
        # Apply name swap for display (after priority voice lookup)
        if E_name_swap and original_nickname in E_name_swap:
            nickname = E_name_swap[original_nickname]  # Swap the nickname for display
            name_swap_info = f"Name swap: {original_nickname} -> {nickname}"
            print(name_swap_info)
            write_log(name_swap_info)
        

        
        # Return with priority voice and speed encoded if we have priority voice
        if priority_voice:
            voice_with_speed = f"{priority_voice}|{priority_speed}" if priority_speed else priority_voice
            return True, comment, voice_with_speed, nickname

    # Apply name swap for display (for non-priority users too)
    if E_name_swap and original_nickname in E_name_swap:
        nickname = E_name_swap[original_nickname]  # Swap the nickname for display
        name_swap_info = f"Name swap: {original_nickname} -> {nickname}"
        print(name_swap_info)
        write_log(name_swap_info)

    # Continue with normal filtering only if no priority voice was set
    # Filter A: !tts check
    if A_ttscode:
        pass
        if not comment.startswith('!tts'):
            # If A_ttscode is TRUE and the comment does not start with !tts, skip it
            return False, None, None, nickname

        # If it starts with !tts, strip it off and process the remaining comment
        comment = comment[4:].strip()  # Remove the "!tts" part and trim leading spaces

    # Filter B: Word filter (only for non-priority users)
    if B_word_filter:  # Check if B_word_filter is not None/empty
        for bad_word in B_word_filter:
            if bad_word and bad_word.lower() in lower_comment:  # Check if bad_word is not None/empty
               # Replace comment with a random response
               new_comment = f", {load_random_reply(B_filter_reply)}"
        
               # Select a specific voice for bad word detection from the settings (e.g., "BadWordVoice")
               voice = D_voice_map.get('BadWordVoice', None)  # Use voice defined for bad word responses

               if not voice:
                   # If no specific bad word voice, fallback to default
                   voice = D_voice_map.get('Default', None)

               return True, new_comment, voice, nickname

    # Filter D: Role-based voice mapping (only for non-priority users)
    voice = None  # Initialize voice variable
    
    # Check subscriber first
    if isSubscriber:
        voice = D_voice_map.get('Subscriber', None)

    # If no voice from subscriber, check for moderator
    if not voice and isModerator:
        voice = D_voice_map.get('Moderator', None)

    # If still no voice, check for Top Gifter
    if not voice and topGifterRank is not None:
        try:
            topGifterRank = int(topGifterRank)
            if 1 <= topGifterRank <= 5:
                voice = D_voice_map.get(f'Top Gifter {topGifterRank}', None)
        except ValueError:
            pass  # Invalid rank, continue to next check

    # If still no voice, check follow role, specifically handling 0 as valid
    if not voice and followRole is not None:  # Check explicitly for None, so 0 is allowed
        follow_role_key = f'Follow Role {followRole}'
        voice = D_voice_map.get(follow_role_key, None)

    # Finally, if no voice found after all checks, use default
    if not voice:
        voice = D_voice_map.get('Default', None)

    # If the voice is "NONE", return early
    if voice == "NONE":
        return False, None, None, nickname

    # Log voice selection for non-priority users
    # Use nameswap name if it exists, otherwise use original nickname
    display_name = E_name_swap.get(original_nickname, nickname) if E_name_swap else nickname
    log_to_gui(f"{display_name} will use voice {voice} at speed {configs.get('config', {}).get('playback_speed', 1.0)}")
    log_to_gui("")  # Add gap after voice selection

    # Assert that the return has exactly 4 values
    result = (True, comment, voice, nickname)
    assert len(result) == 4, f"Expected 4 values, but got {len(result)}"
    return result  # Ensure exactly 4 values are returned

def run_tts(nickname, comment, voice):
    """Run TTS with enhanced error handling and logging"""
    try:
        # Here we use the nickname after the swap
        # Get volume from Windows mixer (TTS session volume)
        current_volume = tts_audio_manager.get_session_volume()
        
        # Get default speed from config
        default_speed = configs.get('config', {}).get('playback_speed', 1.0)
        
        # Check if voice contains speed information (format: "VOICE|SPEED")
        if '|' in voice:
            voice_name, speed = voice.split('|', 1)
            command = ['py', '-3.12', 'TTS.pyw', '-t', f"{nickname} says {comment}", '-v', voice_name, '-s', speed, '--volume', str(current_volume), '-play']
        else:
            command = ['py', '-3.12', 'TTS.pyw', '-t', f"{nickname} says {comment}", '-v', voice, '-s', str(default_speed), '--volume', str(current_volume), '-play']
        
        # GUI noise reduction: remove detailed run log
        
        result = subprocess.run(
            command,
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # GUI noise reduction: omit success log
            pass
        else:
            write_log(f"⚠️ TTS.pyw failed with return code {result.returncode}", "WARNING")
            if result.stdout:
                write_log(f"STDOUT: {result.stdout[:200]}{'...' if len(result.stdout) > 200 else ''}")
            if result.stderr:
                write_log(f"STDERR: {result.stderr[:200]}{'...' if len(result.stderr) > 200 else ''}")
                
    except subprocess.TimeoutExpired:
        write_log(f"⚠️ TTS timeout for {nickname} - subprocess took too long", "WARNING")
    except FileNotFoundError:
        write_log(f"❌ TTS.pyw not found - check if file exists", "ERROR")
    except Exception as e:
        write_log(f"❌ TTS error for {nickname}: {e}", "ERROR")
        log_to_gui(f"TTS Error: {e}")
        import traceback
        write_log(f"Traceback: {traceback.format_exc()[:300]}...", "ERROR")

# Background message processor (the "second staff member")
async def process_message_queue():
    """Background worker that processes messages without blocking the main websocket loop"""
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while True:
        try:
            # Get message from queue (waits if empty)
            nickname, comment, voice = await message_queue.get()
            
            # GUI noise reduction: omit per-message processing log
            
            # Process TTS in background with timeout
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, run_tts, nickname, comment, voice
                    ),
                    timeout=30.0  # 30 second timeout for TTS processing
                )
                
                # Reset error counter on success
                consecutive_errors = 0
                
            except asyncio.TimeoutError:
                write_log(f"⚠️ TTS timeout for {nickname} - message too long or API slow", "WARNING")
                consecutive_errors += 1
            except Exception as tts_error:
                write_log(f"❌ TTS error for {nickname}: {tts_error}", "ERROR")
                consecutive_errors += 1
            
            # Mark task as done
            message_queue.task_done()
            
            # Update queue size after processing
            current_queue_size = message_queue.qsize()
            write_log(f"Queue size: {current_queue_size}")
            
        except Exception as e:
            consecutive_errors += 1
            write_log(f"❌ Background processor error #{consecutive_errors}: {e}", "ERROR")
            log_to_gui(f"Background Error: {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                write_log(f"🚨 Too many consecutive errors, pausing processor for 10 seconds", "WARNING")
                await asyncio.sleep(10)
                consecutive_errors = 0
            else:
                await asyncio.sleep(0.1)

# Add message to queue for background processing
async def queue_tts_message(nickname, comment, voice):
    """Add TTS message to background queue"""
    try:
        message_queue.put_nowait((nickname, comment, voice))
        queue_msg = f"Queue size: {message_queue.qsize()}"
        print(queue_msg)
        write_log(queue_msg)
        print()  # Clean break after each message group
        write_log("")  # Add blank line to GUI log
    except asyncio.QueueFull:
        print(f"⚠️ Queue full! Dropping message from {nickname}")
        # Could implement priority dropping here if needed



async def connect_to_websocket():
    global configs  # This is important to keep track of the configurations
    # Initial filters are loaded based on configs
    A_ttscode, B_word_filter, B_filter_reply, C_priority_voice, D_voice_map, E_name_swap = load_filters(configs)

    # Start single background message processor (the "second staff")
    task = asyncio.create_task(process_message_queue())
    processing_tasks.add(task)
    print(f"Started background TTS processor")



    # Always use a fixed 1s reconnect delay (match vendor example)
    retry_delay = 1

    while True:
        websocket = None
        try:
            print("Attempting to connect to TikFinity...")
            write_log("🔌 Attempting to connect to TikFinity...")
            log_to_gui("Attempting to reconnect to Tikfinity")
            # Use robust WebSocket connection with dedicated ping/pong worker
            # Simple WebSocket connection for TikFinity
            websocket = await asyncio.wait_for(
                websockets.connect(
                    websocket_url,
                    ping_interval=23,    # 23 seconds between pings
                    ping_timeout=10,     # 10 second timeout
                    close_timeout=10
                ),
                timeout=10.0
            )
            
            print("Connected to TikFinity")
            write_log("✅ Connected to TikFinity")
            log_to_gui("Connected to Tikfinity")
            log_to_gui("")  # Add gap after connection
            retry_delay = 1  # Reset retry delay on successful connection
            
            async for message in websocket:
                try:
                    # Periodically check for file updates and reload settings if needed
                    updated_filters = check_for_file_updates()
                    if updated_filters:
                        # If the settings file has been updated, use the updated settings
                        A_ttscode, B_word_filter, B_filter_reply, C_priority_voice, D_voice_map, E_name_swap = updated_filters

                    # Ensure message is properly decoded as UTF-8
                    if isinstance(message, bytes):
                        message = message.decode('utf-8', errors='replace')
                    
                    data = json.loads(message)  # Parse incoming message as JSON
                    if data.get("event") == "chat":
                        chat_data = data.get("data", {})

                        # Call passes_filters and handle unpacking safely
                        try:
                            result = passes_filters(
                                chat_data, A_ttscode, B_word_filter, B_filter_reply, C_priority_voice, D_voice_map, E_name_swap, configs
                            )

                            # Ensure that only 4 values are returned
                            if len(result) == 4:
                                passes, comment, voice, nickname = result
                            else:
                                passes, comment, voice, nickname = False, '', None, ''  # Default safe values
                        except ValueError as e:
                            print(f"Error unpacking result from passes_filters: {e}")
                            passes, comment, voice, nickname = False, '', None, ''  # Default safe values

                        if passes:
                            # Strip emojis and icons just before sending to TTS
                            clean_nickname = strip_emojis_and_icons(nickname)
                            clean_comment = strip_emojis_and_icons(comment)
                            await queue_tts_message(clean_nickname, clean_comment, voice)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    pass  # Ignore non-JSON messages
                except UnicodeDecodeError as e:
                    print(f"Unicode decode error: {e}")
                    pass  # Ignore messages with encoding issues
                except Exception as e:
                    print(f"Error processing message: {e}")
                    write_log(f"Message processing error: {e}", "ERROR")
                    
        except asyncio.TimeoutError:
            print("Connection timeout. Retrying in 1 second...")
        except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidStatusCode) as e:
            print(f"Disconnected from TikFinity: {e}")
            print("Reconnecting in 1 second...")
        except ConnectionRefusedError as e:
            print(f"Connection refused: {e}")
            print("Retrying in 1 second...")
        except Exception as e:
            print(f"Unexpected error: {e}")
            log_to_gui(f"Error: {e}")
            print("Retrying in 1 second...")
        finally:
            # Properly close websocket if it exists
            if websocket and not websocket.closed:
                try:
                    await websocket.close()
                except:
                    pass
            
            # Fixed 1s reconnect delay
            await asyncio.sleep(1)


# Main entry point
if __name__ == "__main__":
    import atexit
    import asyncio
    import subprocess
    import os

    # Log start
    write_log("Main.pyw started", "INFO")

    # Register cleanup function
    atexit.register(tts_audio_manager.shutdown)

    try:
        
        # Load initial configurations on startup
        configs = load_settings()

        if configs:
            asyncio.run(connect_to_websocket())

    except KeyboardInterrupt:
        print("\n🛑 Shutting down TTS system...")
        write_log("Shutdown initiated by user (KeyboardInterrupt)", "INFO")
        tts_audio_manager.shutdown()
    except Exception as e:
        print(f"Fatal error: {e}")
        write_log(f"Main execution error: {e}", "ERROR")
        tts_audio_manager.shutdown()
    finally:
        print("TTS system stopped.")
        write_log("Main.pyw stopped", "INFO")
