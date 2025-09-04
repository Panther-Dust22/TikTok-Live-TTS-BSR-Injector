import os
import sys
import time
import threading
import queue
import base64
import mmap
import struct
from datetime import datetime
from pathlib import Path

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

# Hide console window on Windows
try:
    import ctypes
    if os.name == 'nt':  # Windows
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        console_window = kernel32.GetConsoleWindow()
        if console_window:
            user32.ShowWindow(console_window, 0)  # 0 = SW_HIDE
except Exception:
    pass

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available, audio playback disabled")

class AudioQueueServerV2:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.currently_playing = False
        self.running = True
        self.last_audio_hash = None
        self.last_play_time = 0.0
        self.shared_memory_name = "audio_queue_memory"
        self.shared_memory_size = 1024 * 1024  # 1MB buffer
        self.shared_memory = None
        self.shared_memory_lock = threading.Lock()
        
        # Audio playback settings
        self.volume = 1.0
        self.playback_speed = 1.0
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'total_played': 0,
            'queue_overflow': 0,
            'start_time': datetime.now()
        }
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Audio Queue Server v2 starting...")
    
    def start_server(self):
        """Start the audio queue server"""
        # Initialize shared memory
        self._init_shared_memory()
        
        # Start audio player thread
        player_thread = threading.Thread(target=self._audio_player_loop, daemon=True)
        player_thread.start()
        
        # Start shared memory monitor thread
        monitor_thread = threading.Thread(target=self._shared_memory_monitor, daemon=True)
        monitor_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Audio Queue Server v2 stopping...")
        finally:
            self._cleanup_shared_memory()
    
    def _init_shared_memory(self):
        """Initialize shared memory for audio data transfer"""
        try:
            # Create shared memory object
            self.shared_memory = mmap.mmap(-1, self.shared_memory_size, self.shared_memory_name)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Shared memory initialized: {self.shared_memory_name}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to initialize shared memory: {e}")
            self.shared_memory = None
    
    def _cleanup_shared_memory(self):
        """Clean up shared memory"""
        if self.shared_memory:
            try:
                self.shared_memory.close()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Shared memory cleaned up")
            except:
                pass
    
    def _shared_memory_monitor(self):
        """Monitor shared memory for new audio data with enhanced error handling"""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.running:
            try:
                if self.shared_memory:
                    with self.shared_memory_lock:
                        # Check for new data (first 4 bytes contain data length)
                        self.shared_memory.seek(0)
                        length_bytes = self.shared_memory.read(4)
                        
                        if length_bytes != b'\x00\x00\x00\x00':  # Not empty
                            try:
                                data_length = struct.unpack('I', length_bytes)[0]
                                
                                if data_length > 0 and data_length < self.shared_memory_size - 4:
                                    # Read audio data
                                    audio_data = self.shared_memory.read(data_length)
                                    
                                    # Validate audio data
                                    if len(audio_data) != data_length:
                                        print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Audio data length mismatch: expected {data_length}, got {len(audio_data)}")
                                        continue
                                    
                                    # Clear the buffer
                                    self.shared_memory.seek(0)
                                    self.shared_memory.write(b'\x00\x00\x00\x00')
                                    self.shared_memory.flush()
                                    
                                    # Add to queue
                                    audio_item = {
                                        'id': f"audio_{int(time.time())}",
                                        'timestamp': datetime.now().isoformat(),
                                        'audio_data': audio_data,
                                        'volume': self.volume,
                                        'size_bytes': len(audio_data)
                                    }
                                    self._add_to_queue(audio_item)
                                    
                                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Received audio data: {audio_item['id']}, size: {len(audio_data)} bytes")
                                    
                                    # Reset error counter on success
                                    consecutive_errors = 0
                                else:
                                    print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Invalid data length: {data_length}")
                                    # Clear invalid data
                                    self.shared_memory.seek(0)
                                    self.shared_memory.write(b'\x00\x00\x00\x00')
                                    self.shared_memory.flush()
                                    
                            except struct.error as e:
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Failed to unpack data length: {e}")
                                # Clear corrupted data
                                self.shared_memory.seek(0)
                                self.shared_memory.write(b'\x00\x00\x00\x00')
                                self.shared_memory.flush()
                
                time.sleep(0.07)  # Check every 70ms for responsiveness
                
            except Exception as e:
                consecutive_errors += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Shared memory monitor error #{consecutive_errors}: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] CRITICAL: Too many consecutive errors, attempting to reconnect to shared memory")
                    try:
                        self._cleanup_shared_memory()
                        time.sleep(1)
                        self._init_shared_memory()
                        consecutive_errors = 0
                    except Exception as reconnect_error:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to reconnect to shared memory: {reconnect_error}")
                
                time.sleep(1)
    
    def _add_to_queue(self, audio_data):
        """Add audio data to the queue"""
        try:
            if self.audio_queue.qsize() >= 50:  # Reduced queue size for faster processing
                # Remove oldest item if queue is full
                try:
                    self.audio_queue.get_nowait()
                    self.stats['queue_overflow'] += 1
                except queue.Empty:
                    pass
            
            self.audio_queue.put(audio_data)
            self.stats['total_processed'] += 1
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error adding to queue: {e}")
    
    def _audio_player_loop(self):
        """Audio player thread that plays queued audio"""
        if not PYGAME_AVAILABLE:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] pygame not available, audio playback disabled")
            return
        
        # Initialize pygame mixer with better settings for WAV audio
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Audio player initialized")
            
            # Try to set the application name for the audio session
            try:
                import ctypes
                if os.name == 'nt':  # Windows
                    # Set the application name for the audio session
                    ctypes.windll.kernel32.SetConsoleTitleW("TTS Voice System")
                    
                    # Try to set the process name using a different method
                    try:
                        # This might help with the volume mixer display name
                        ctypes.windll.kernel32.SetProcessPreferredUILanguages(0, ["TTS Voice System"], None)
                    except:
                        pass
            except:
                pass
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to initialize audio: {e}")
            return
        
        while self.running:
            try:
                # Get next audio item from queue
                try:
                    audio_item = self.audio_queue.get(timeout=0.1)  # Reduced timeout for responsiveness
                except queue.Empty:
                    continue
                
                self.currently_playing = True
                self._play_audio(audio_item)
                self.currently_playing = False
                self.stats['total_played'] += 1
                
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Audio player error: {e}")
                self.currently_playing = False
    
    def _play_audio(self, audio_item):
        """Play audio from the queue item - optimized for speed with better error handling"""
        try:
            audio_id = audio_item.get('id', 'unknown')
            audio_data = audio_item.get('audio_data')
            volume = audio_item.get('volume', self.volume)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Playing audio: {audio_id}, size: {len(audio_data) if audio_data else 0} bytes, volume: {volume}")
            
            if not audio_data:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: No audio data for {audio_id}")
                return
            
            if len(audio_data) < 100:  # Suspiciously small audio data
                print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Very small audio data for {audio_id}: {len(audio_data)} bytes")
            
            # deduplicate recently sent identical audio (protect against accidental resend)
            import hashlib, io
            audio_hash = hashlib.sha256(audio_data).hexdigest()
            now = time.time()
            if self.last_audio_hash == audio_hash and (now - self.last_play_time) < 0.75:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Skipping duplicate audio within 750ms: {audio_id}")
                return
            self.last_audio_hash = audio_hash
            self.last_play_time = now

            # Create sound from WAV bytes using BytesIO
            import io
            sound = pygame.mixer.Sound(io.BytesIO(audio_data))
            sound.set_volume(volume)
            # Ensure only one channel used; stop any lingering playback before starting
            pygame.mixer.stop()
            sound.play()
            
            # Wait for playback to complete with timeout
            start_time = time.time()
            timeout = 30  # 30 second timeout for audio playback
            
            while pygame.mixer.get_busy():
                if time.time() - start_time > timeout:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: Audio playback timeout for {audio_id}")
                    break
                time.sleep(0.07)  # Reduced sleep for faster response
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Finished playing: {audio_id}")
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] CRITICAL ERROR playing audio: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to recover pygame mixer if it crashed
            try:
                pygame.mixer.quit()
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Recovered pygame mixer after error")
            except Exception as recovery_error:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to recover pygame mixer: {recovery_error}")
    
    def get_stats(self):
        """Get server statistics"""
        uptime = datetime.now() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'queue_size': self.audio_queue.qsize(),
            'currently_playing': self.currently_playing
        }

def main():
    """Main function"""
    # Set process name to "TTS Voice System" for Windows Volume Mixer
    try:
        import ctypes
        if os.name == 'nt':  # Windows
            # Set console title multiple times to ensure it sticks
            ctypes.windll.kernel32.SetConsoleTitleW("TTS Voice System")
            ctypes.windll.kernel32.SetConsoleTitleW("TTS Voice System")
            
            # Try to set process name by modifying the command line
            try:
                # Get current process handle
                process_handle = ctypes.windll.kernel32.GetCurrentProcess()
                # Set process name (this is a more direct approach)
                ctypes.windll.kernel32.SetProcessShutdownParameters(0x3FF, 0)
                
                # Try additional methods to set the process name
                try:
                    ctypes.windll.kernel32.SetProcessPreferredUILanguages(0, ["TTS Voice System"], None)
                except:
                    pass
            except:
                pass
    except:
        pass
    
    server = AudioQueueServerV2()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Audio Queue Server v2 stopped by user")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fatal error: {e}")
    finally:
        server.running = False

if __name__ == "__main__":
    main() 