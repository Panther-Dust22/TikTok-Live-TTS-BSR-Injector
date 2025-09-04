#!/usr/bin/env python3
"""
Audio Queue Client v2 - Client-side interface for audio queue server
Handles sending audio data to the audio queue server via shared memory.
"""

import os
import sys
import time
import threading
import mmap
import struct
from datetime import datetime
from pathlib import Path


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


class AudioQueueClientV2:
    """Client for sending audio data to the audio queue server"""
    
    def __init__(self):
        self.shared_memory_name = "audio_queue_memory"
        self.shared_memory_size = 1024 * 1024  # 1MB buffer
        self.shared_memory = None
        self.shared_memory_lock = threading.Lock()
        self.connected = False
        
        # Initialize logging
        write_log("Audio Queue Client v2 initialized", "INFO")
        
        # Try to connect to shared memory
        self._connect_to_shared_memory()
    
    def _connect_to_shared_memory(self):
        """Connect to the shared memory used by the audio queue server"""
        try:
            # Try to open existing shared memory
            self.shared_memory = mmap.mmap(-1, self.shared_memory_size, self.shared_memory_name)
            self.connected = True
            
            write_log(f"Connected to shared memory: {self.shared_memory_name}", "INFO")
                
        except Exception as e:
            self.connected = False
            write_log(f"Failed to connect to shared memory: {e}", "WARNING")
    
    def send_audio(self, audio_data: bytes, volume: float = 1.0, priority: int = 1) -> bool:
        """Send audio data to the queue server via shared memory with short busy-wait retries."""
        if not self.connected:
            # Try to reconnect
            self._connect_to_shared_memory()
            if not self.connected:
                write_log("Cannot send audio - not connected to shared memory", "ERROR")
                return False
        
        try:
            max_attempts = 50  # total ~1s with 20ms sleep
            for attempt in range(max_attempts):
                with self.shared_memory_lock:
                    # Check if buffer is available (first 4 bytes should be 0)
                    self.shared_memory.seek(0)
                    length_bytes = self.shared_memory.read(4)
                    
                    if length_bytes == b'\x00\x00\x00\x00':
                        # Check if audio data fits in buffer
                        if len(audio_data) > self.shared_memory_size - 4:
                            write_log(f"Audio data too large: {len(audio_data)} bytes", "ERROR")
                            return False
                        
                        # Write data length first
                        self.shared_memory.seek(0)
                        self.shared_memory.write(struct.pack('I', len(audio_data)))
                        
                        # Write audio data
                        self.shared_memory.write(audio_data)
                        self.shared_memory.flush()
                        
                        write_log(f"Sent audio: {len(audio_data)} bytes, volume: {volume}", "INFO")
                        
                        return True
                # buffer busy, brief sleep before retry
                time.sleep(0.02)
            # after attempts, give up
            write_log("Audio buffer remained busy; dropping audio to avoid overlap", "WARNING")
            return False
                
        except Exception as e:
            write_log(f"Error sending audio: {e}", "ERROR")
            
            # Try to reconnect on error
            self.connected = False
            return False
    
    def is_available(self) -> bool:
        """Check if the audio queue server is available"""
        if not self.connected:
            self._connect_to_shared_memory()
        return self.connected
    
    def close(self):
        """Close the shared memory connection"""
        if self.shared_memory:
            try:
                self.shared_memory.close()
                write_log("Shared memory connection closed", "INFO")
            except:
                pass
        self.connected = False

# Global client instance
_audio_client = None

def get_audio_client():
    """Get or create the global audio client instance"""
    global _audio_client
    if _audio_client is None:
        _audio_client = AudioQueueClientV2()
    return _audio_client

def send_audio_to_queue(audio_data: bytes, volume: float = 1.0, priority: int = 1) -> bool:
    """Send audio data to the queue server"""
    client = get_audio_client()
    return client.send_audio(audio_data, volume, priority)

def is_audio_queue_available() -> bool:
    """Check if the audio queue server is available"""
    client = get_audio_client()
    return client.is_available()

def close_audio_queue():
    """Close the audio queue client"""
    global _audio_client
    if _audio_client:
        _audio_client.close()
        _audio_client = None

# Cleanup on exit
import atexit
atexit.register(close_audio_queue)

if __name__ == "__main__":
    # Test the client
    print("Audio Queue Client v2 - Test Mode")
    client = AudioQueueClientV2()
    
    if client.is_available():
        print("✅ Audio queue server is available")
        
        # Test with dummy audio data
        test_audio = b"test_audio_data" * 100
        success = client.send_audio(test_audio, volume=0.5)
        
        if success:
            print("✅ Audio sent successfully")
        else:
            print("❌ Failed to send audio")
    else:
        print("❌ Audio queue server is not available")
    
    client.close()
