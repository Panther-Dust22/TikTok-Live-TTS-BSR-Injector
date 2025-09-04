import argparse 
import requests
import base64
import json
import re
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from enum import Enum
import sys
import os
from pydub import AudioSegment
from pydub.playback import play



# Import audio queue client
try:
    from audio_queue_client_v2 import send_audio_to_queue, is_audio_queue_available
    AUDIO_QUEUE_AVAILABLE = True
except ImportError:
    AUDIO_QUEUE_AVAILABLE = False
    def send_audio_to_queue(audio_data, volume=1.0, priority=1):
        return False
    def is_audio_queue_available():
        return False

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

# Suppress Pygame messages
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

# Copy the Voice enum from original script
class Voice(Enum):
    # DISNEY VOICES
    GHOSTFACE = 'en_us_ghostface'
    CHEWBACCA = 'en_us_chewbacca'
    C3PO = 'en_us_c3po'
    STITCH = 'en_us_stitch'
    STORMTROOPER = 'en_us_stormtrooper'
    ROCKET = 'en_us_rocket'
    # ENGLISH VOICES
    PIRATE = 'en_male_pirate'
    GHOSTHOST = 'en_male_ghosthost'
    MADAMELEOTA = 'en_female_madam_leota'
    MAGICIAN = 'en_male_wizard'
    SANTANARATION = 'en_male_santa_narration'
    GRANNY = 'en_female_grandma'
    CUPID = 'en_male_cupid'
    BAE = 'en_female_betty'
    MARTY = 'en_male_trevor'
    VARSITY = 'en_female_pansino'
    DEBUTANTE = 'en_female_shenna'
    BUTLER = 'en_male_ukbutler'
    LORDCRINGE = 'en_male_ukneighbor'
    OLANTEKKERS = 'en_male_olantekkers'
    ASHMAGIC = 'en_male_ashmagic'
    ALFRED = 'en_male_jarvis'
    TRICKSTER = 'en_male_grinch'
    BESTIE = 'en_female_richgirl'
    BEAUTY = 'en_female_makeup'
    MALESERIOUS = 'en_male_cody'
    GAMEON = 'en_male_jomboy'
    DEADPOOL = 'en_male_deadpool'
    EN_AU_FEMALE_1 = 'en_au_001'
    EN_AU_MALE_1 = 'en_au_002'
    EN_UK_MALE_1 = 'en_uk_001'
    EN_UK_MALE_2 = 'en_uk_003'
    EN_US_FEMALE_1 = 'en_us_001'
    EN_US_FEMALE_2 = 'en_us_002'
    EN_US_MALE_1 = 'en_us_006'
    EN_US_MALE_2 = 'en_us_007'
    EN_US_MALE_3 = 'en_us_009'
    EN_US_MALE_4 = 'en_us_010'
    # EUROPE VOICES
    FR_MALE_1 = 'fr_001'
    FR_MALE_2 = 'fr_002'
    DE_FEMALE = 'de_001'
    DE_MALE = 'de_002'
    ES_MALE = 'es_002'
    # AMERICA VOICES
    ES_MX_MALE = 'es_mx_002'
    BR_FEMALE_1 = 'br_001'
    BR_FEMALE_2 = 'br_003'
    BR_FEMALE_3 = 'br_004'
    BR_MALE = 'br_005'
    # ASIA VOICES
    ID_FEMALE = 'id_001'
    JP_FEMALE_1 = 'jp_001'
    JP_FEMALE_2 = 'jp_003'
    JP_FEMALE_3 = 'jp_005'
    JP_MALE = 'jp_006'
    KR_MALE_1 = 'kr_002'
    KR_FEMALE = 'kr_003'
    KR_MALE_2 = 'kr_004'
    # SINGING VOICES
    EN_FEMALE_ALTO = 'en_female_f08_salut_damour'
    EN_MALE_TENOR = 'en_male_m03_lobby'
    EN_FEMALE_WARMY_BREEZE = 'en_female_f08_warmy_breeze'
    EN_MALE_SUNSHINE_SOON = 'en_male_m03_sunshine_soon'
    # OTHER
    EN_MALE_NARRATION = 'en_male_narration'
    EN_MALE_FUNNY = 'en_male_funny'
    EN_FEMALE_EMOTIONAL = 'en_female_emotional'
    #new voices
    FEMALE_SAMC = 'en_female_samc'
    MALE_XMXS_CHRISTMAS = 'en_male_m2_xhxs_m03_christmas'
    MALE_SING_DEEP_JINGLE = 'en_male_sing_deep_jingle'
    MALE_SANTA_EFFECT = 'en_male_santa_effect'
    FEMALE_HT_NEYEAR = 'en_female_ht_f08_newyear'
    FEMALE_HT_HALLOWEEN = 'en_female_ht_f08_halloween'
    BP_FEMALE_IVETE = 'bp_female_ivete'
    BP_FEMALE_LUDMILLA = 'bp_female_ludmilla'
    PT_FEMALE_LHAYS = 'pt_female_lhays'
    PT_FEMALE_LAIZZA = 'pt_female_laizza'
    PT_MALE_BUENO = 'pt_male_bueno'
    JP_FEMALE_FUJICOCHAN = 'jp_female_fujicochan'
    JP_FEMALE_HASEGAWARIONA = 'jp_female_hasegawariona'
    JP_MALE_KEIICHINAKANO = 'jp_male_keiichinakano'
    JP_FEMALE_OOMAEAIIKA = 'jp_female_oomaeaika'
    JP_MALE_YUJINCHIGUSA = 'jp_male_yujinchigusa'
    JP_MALE_TAMAWAKAZUKI = 'jp_male_tamawakazuki'
    JP_FEMALE_KAORISHOJI = 'jp_female_kaorishoji'
    JP_FEMALE_YAGISHAKI = 'jp_female_yagishaki'
    JP_MALE_HIKAKIN = 'jp_male_hikakin'
    JP_FEMALE_REI = 'jp_female_rei'
    JP_MALE_SHUICHIRO = 'jp_male_shuichiro'
    JP_MALE_MATSUDAKE = 'jp_male_matsudake'
    JP_FEMALE_MACHIKORIIITA = 'jp_female_machikoriiita'
    JP_MALE_MATSUO = 'jp_male_matsuo'
    JP_MALE_OSADA = 'jp_male_osada'
    SING_FEMALE_GLORIOUS = 'en_female_ht_f08_glorious'
    SING_MALE_IT_GOES_UP = 'en_male_sing_funny_it_goes_up'
    SING_MALE_CHIPMUNK = 'en_male_m2_xhxs_m03_silly'
    SING_FEMALE_WONDERFUL_WORLD = 'en_female_ht_f08_wonderful_world'
    SING_MALE_FUNNY_THANKSGIVING = 'en_male_sing_funny_thanksgiving'
    SING_POP_LULLABY ='en_female_f08_twinkle'
    SING_CLASSIC_ELECTRIC ='en_male_m03_classical'
    V_FEMALE_001 ='BV074_streaming'
    V_MALE_001 ='BV075_streaming'

    @staticmethod
    def from_string(input_string: str):
        """Function to check if a string matches any enum member name."""
        for voice in Voice:
            if voice.name == input_string:
                return voice
        return None

class ReliableTTS:
    def __init__(self, config_file: str = "data/TTSconfig.json"):
        self.config = self._load_config(config_file)
        self.all_endpoints = self._load_all_endpoints()
        self.endpoints = []  # Will be populated after performance testing
        self.stats = {
            'api_calls': 0,
            'failed_requests': 0,
            'endpoint_failures': {},
            'total_requests': 0,
            'performance_test_results': {}
        }
        
        # Load API endpoints from config (set by api_monitor.py)
        self._load_api_endpoints_from_config()
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration with defaults."""
        default_config = {
            "request_timeout": 8,
            "max_retries": 1,
            "retry_delay": 0.2,
            "playback_speed": 1.0,
            "max_concurrent_requests": 5,
            "performance_test_enabled": True,
            "performance_test_text": "Hello world, this is a test message.",
            "performance_test_voice": "EN_US_MALE_1",
            "performance_test_timeout": 10,
            "performance_test_retries": 2
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
                pass  # Silently use defaults if config can't be loaded
        
        return default_config
    
    def _load_all_endpoints(self) -> List[Dict[str, str]]:
        """Load all endpoint configurations."""
        return [
            {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data", "name": "weilnet"},
            {"url": "https://gesserit.co/api/tiktok-tts", "response": "base64", "name": "gesserit"},
            {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data", "name": "weilnet_backup"}
        ]
    
    def _load_api_endpoints_from_config(self):
        """Load API endpoints from config file (set by api_monitor.py)."""
        if 'api_endpoints' in self.config and self.config['api_endpoints']:
            # Use endpoints from config (set by api_monitor.py)
            self.endpoints = self.config['api_endpoints']
            print(f"[INFO] Loaded {len(self.endpoints)} API endpoints from config")
            print(f"   Endpoint order: {' -> '.join(e['name'] for e in self.endpoints)}")
        else:
            # Fallback to default endpoints if no config data
            self.endpoints = self.all_endpoints.copy()
            print(f"[INFO] Using default endpoints (no config data)")
            print(f"   Endpoint order: {' -> '.join(e['name'] for e in self.endpoints)}")
    

    

    
    def _make_single_request(self, endpoint: Dict, text: str, voice: Voice) -> Optional[str]:
        """Make a single API request to an endpoint."""
        endpoint_name = endpoint["name"]
        
        try:
            response = requests.post(
                endpoint["url"], 
                json={"text": text, "voice": voice.value},
                timeout=self.config["request_timeout"]
            )
            response.raise_for_status()
            self.stats['api_calls'] += 1
            return response.json()[endpoint["response"]]
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, 
                requests.exceptions.HTTPError, KeyError, json.JSONDecodeError, Exception) as e:
            # Track endpoint failures
            if endpoint_name not in self.stats['endpoint_failures']:
                self.stats['endpoint_failures'][endpoint_name] = 0
            self.stats['endpoint_failures'][endpoint_name] += 1
            
            # Log specific error types for debugging
            if isinstance(e, requests.exceptions.HTTPError):
                print(f"[WARN] {endpoint_name} HTTP {e.response.status_code}: {e}")
            elif isinstance(e, requests.exceptions.Timeout):
                print(f"[WARN] {endpoint_name} timeout after {self.config['request_timeout']}s")
            elif isinstance(e, requests.exceptions.ConnectionError):
                print(f"[WARN] {endpoint_name} connection error")
            
            return None
    
    def _try_all_endpoints_with_retry(self, text: str, voice: Voice) -> Optional[str]:
        """Try all endpoints in order, with incremental retry delays."""
        max_retries = self.config["max_retries"]
        base_delay = self.config["retry_delay"]
        
        for retry_attempt in range(max_retries):
            # Try each endpoint once per retry cycle
            for endpoint in self.endpoints:
                audio_b64 = self._make_single_request(endpoint, text, voice)
                if audio_b64:
                    return audio_b64
            
            # If we get here, all endpoints failed in this retry cycle
            if retry_attempt < max_retries - 1:
                delay = base_delay * (retry_attempt + 1)  # Incremental delay: 1.5s, 3s, 4.5s
                print(f"[RETRY] All endpoints failed, retrying in {delay}s...")
                time.sleep(delay)
        
        # All retries exhausted
        self.stats['failed_requests'] += 1
        print(f"[ERROR] All endpoints failed after {max_retries} retry cycles")
        return None
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into 'username says' and 'comment' chunks."""
        chunks = []
        
        # Check if text follows the pattern "username says comment"
        if " says " in text:
            parts = text.split(" says ", 1)  # Split only on first occurrence
            if len(parts) == 2:
                username, comment = parts
                
                # First chunk: "username says"
                first_chunk = f"{username} says"
                chunks.append(first_chunk)
                
                # Second chunk: the comment (which is max 100 characters)
                if comment.strip():
                    chunks.append(comment.strip())
            else:
                # Fallback to original method if pattern doesn't match
                chunks = re.findall(r'.*?[.,!?:;-]|.+', text)
        else:
            # Fallback to original method for non-standard text
            chunks = re.findall(r'.*?[.,!?:;-]|.+', text)
        
        return chunks
    
    def tts(self, text: str, voice: Voice, play_sound: bool = False, volume: float = 1.0) -> Optional[bytes]:
        """Enhanced TTS with better reliability and proper audio handling."""
        # Validate input
        if not text.strip():
            raise ValueError("Text cannot be empty")
        if not isinstance(voice, Voice):
            raise TypeError("Voice must be of type Voice")
        
        self.stats['total_requests'] += 1
        
        # Log the TTS request
        try:
            from pathlib import Path
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] TTS Request: '{text[:50]}{'...' if len(text) > 50 else ''}' with voice {voice.value}\n")
        except:
            pass
        
        # Split text into chunks
        text_chunks = self._split_text(text)
        audio_chunks = [None for _ in range(len(text_chunks))]
        
        def generate_audio_chunk(index: int, text_chunk: str):
            """Generate audio for a single text chunk with proper error handling"""
            try:
                write_log(f"Processing chunk {index}: '{text_chunk[:30]}{'...' if len(text_chunk) > 30 else ''}'", "DEBUG")
                
                audio_b64 = self._try_all_endpoints_with_retry(text_chunk, voice)
                if audio_b64:
                    audio_chunks[index] = audio_b64
                    write_log(f"Chunk {index} successful, size: {len(audio_b64)} chars", "DEBUG")
                else:
                    write_log(f"Chunk {index} failed to generate audio", "ERROR")
            except Exception as e:
                write_log(f"Chunk {index} exception: {e}", "ERROR")
                print(f"[ERROR] Audio chunk generation failed for chunk {index}: {e}")
        
        # Process chunks concurrently
        with ThreadPoolExecutor(max_workers=self.config["max_concurrent_requests"]) as executor:
            # Use list() to ensure all tasks complete before continuing
            list(executor.map(generate_audio_chunk, range(len(text_chunks)), text_chunks))
        
        # Check if all chunks were successful
        failed_chunks = [i for i, chunk in enumerate(audio_chunks) if chunk is None]
        if failed_chunks:
            write_log(f"Failed chunks: {failed_chunks}, reordering endpoints", "WARNING")
            # If any chunks failed, consider reordering endpoints for future requests
            self._reorder_endpoints_by_reliability()
            return None
        
        # Combine audio chunks properly using pydub
        try:
            write_log(f"Combining {len(audio_chunks)} audio chunks", "DEBUG")
            
            audio_segments = []
            for i, b64_chunk in enumerate(audio_chunks):
                try:
                    audio_bytes = base64.b64decode(b64_chunk)
                    audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
                    audio_segments.append(audio_segment)
                    
                    write_log(f"Decoded chunk {i}: {len(audio_bytes)} bytes, duration: {len(audio_segment)}ms", "DEBUG")
                        
                except Exception as e:
                    write_log(f"Failed to decode chunk {i}: {e}", "ERROR")
                    print(f"[ERROR] Decoding audio chunk {i} failed: {e}")
                    return None
            
            # Combine all audio segments
            if audio_segments:
                combined_audio = sum(audio_segments)
                buffer = io.BytesIO()
                combined_audio.export(buffer, format="mp3")
                buffer.seek(0)
                audio_data = buffer.read()
                
                write_log(f"Combined audio: {len(audio_data)} bytes, duration: {len(combined_audio)}ms", "INFO")
                
                # Play audio if requested
                if play_sound:
                    self._play_audio(audio_data, volume)
                
                return audio_data
            else:
                write_log("No audio segments to combine", "ERROR")
                return None
                
        except Exception as e:
            write_log(f"Error combining audio chunks: {e}", "ERROR")
            print(f"[ERROR] Error combining audio chunks: {e}")
            return None
    
    def _play_audio(self, audio_data: bytes, volume: float = 1.0):
        """Send audio to queue for playback instead of playing directly."""
        try:
            # Apply playback speed if configured
            if self.config["playback_speed"] != 1.0:
                write_log(f"Applying playback speed: {self.config['playback_speed']}x", "DEBUG")
                
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
                new_frame_rate = int(audio_segment.frame_rate * self.config["playback_speed"])
                audio_segment = audio_segment._spawn(audio_segment.raw_data, overrides={"frame_rate": new_frame_rate})
                audio_segment = audio_segment.set_frame_rate(44100)
                buffer = io.BytesIO()
                audio_segment.export(buffer, format="wav")
                buffer.seek(0)
                audio_data = buffer.getvalue()
                
                write_log(f"Speed-adjusted audio: {len(audio_data)} bytes", "DEBUG")
            
            # Send to audio queue with brief retries; do NOT fall back to direct playback
            if AUDIO_QUEUE_AVAILABLE:
                max_attempts = 10
                for attempt in range(max_attempts):
                    if is_audio_queue_available():
                        success = send_audio_to_queue(audio_data, volume)
                        if success:
                            write_log(f"Audio sent to queue: {len(audio_data)} bytes, volume: {volume}", "INFO")
                            return
                    # brief backoff before retrying
                    time.sleep(0.02)
                write_log("Audio queue unavailable/busy after retries; skipping playback to prevent overlap", "WARNING")
                return
            else:
                write_log("Audio queue client not available; skipping playback to prevent overlap", "WARNING")
                return
                
        except Exception as e:
            write_log(f"Audio playback error: {e}", "ERROR")
            print(f"[ERROR] Audio playback error: {e}")
            # Don't re-raise - handle gracefully
    
    def get_stats(self) -> Dict:
        """Get reliability statistics."""
        success_rate = ((self.stats['total_requests'] - self.stats['failed_requests']) / max(self.stats['total_requests'], 1)) * 100
        
        return {
            **self.stats,
            'success_rate': f"{success_rate:.1f}%"
        }
    
    def print_stats(self):
        """Print reliability statistics."""
        stats = self.get_stats()
        print("[INFO] Reliability Statistics:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Successful requests: {stats['total_requests'] - stats['failed_requests']}")
        print(f"   Failed requests: {stats['failed_requests']}")
        print(f"   Success rate: {stats['success_rate']}")
        print(f"   API calls made: {stats['api_calls']}")
        
        if stats['endpoint_failures']:
            print(f"   Endpoint failures:")
            for endpoint, failures in stats['endpoint_failures'].items():
                print(f"     {endpoint}: {failures} failures")
        
        if stats['performance_test_results']:
            print(f"\n[START] Performance Test Results:")
            perf_results = stats['performance_test_results']
            print(f"   Test time: {perf_results['test_time']}")
            print(f"   Test text: {perf_results['test_text']}")
            print(f"   Test voice: {perf_results['test_voice']}")
            
            for endpoint_name, result in perf_results['results'].items():
                status = "[OK]" if result['success'] else "[FAIL]"
                print(f"   {status} {endpoint_name}: {result['response_time']:.2f}s (Rank: {result['rank']})")
                if not result['success']:
                    print(f"      Error: {result['error']}")
    
    def _should_reorder_endpoints(self) -> bool:
        """Check if endpoints should be reordered based on recent failures."""
        total_failures = sum(self.stats['endpoint_failures'].values())
        return total_failures >= self.config.get('reorder_threshold', 3)
    
    def _reorder_endpoints_by_reliability(self):
        """Reorder endpoints based on recent failure rates, prioritizing working ones."""
        if not self._should_reorder_endpoints():
            return
        
        print("[REORDER] Reordering endpoints based on recent failures...")
        
        # Calculate failure rates for each endpoint
        endpoint_reliability = []
        for endpoint in self.all_endpoints:
            endpoint_name = endpoint['name']
            failures = self.stats['endpoint_failures'].get(endpoint_name, 0)
            total_calls = self.stats['api_calls']
            
            # Calculate success rate (higher is better)
            success_rate = max(0, (total_calls - failures) / max(total_calls, 1))
            endpoint_reliability.append((endpoint, success_rate))
        
        # Sort by success rate (most reliable first)
        endpoint_reliability.sort(key=lambda x: x[1], reverse=True)
        
        # Update endpoint order
        self.endpoints = [endpoint for endpoint, _ in endpoint_reliability]
        
        # Log the new order
        new_order = ' -> '.join(e['name'] for e in self.endpoints)
        print(f"[REORDER] New endpoint order: {new_order}")
        
        # Reset failure counters after reordering
        self.stats['endpoint_failures'].clear()
    
    def retest_apis(self):
        """Manually retest all APIs and reorder endpoints."""
        print("[RETEST] Retesting API endpoints...")
        self._test_api_performance()
        
        # Save results to config
        self._save_performance_results()
        print("✅ API performance test completed!")
    
    def _save_performance_results(self):
        """Save current performance test results to config."""
        try:
            if 'performance_test_results' in self.stats:
                results = self.stats['performance_test_results']
                
                # Create a summary of results
                test_results = []
                for endpoint_name, data in results.get('results', {}).items():
                    if data.get('success', False):
                        test_results.append(f"{endpoint_name}: ✅ {data.get('response_time', 0):.2f}s")
                    else:
                        test_results.append(f"{endpoint_name}: ❌ {data.get('error', 'Unknown error')}")
                
                # Update config with results
                self.config['last_performance_test'] = {
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'results': test_results,
                    'total_tests': len(results.get('results', {})),
                    'successful_tests': len([r for r in results.get('results', {}).values() if r.get('success', False)])
                }
                
                # Save to file
                config_file = "data/TTSconfig.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                
                print("💾 Performance test results saved to config")
                
        except Exception as e:
            print(f"⚠️ Error saving performance results: {e}")

def filter_special_characters(text):
    """Remove only truly problematic characters that could break TTS."""
    # Only remove characters that are known to cause issues with TTS APIs
    # Keep all letters, numbers, spaces, and most punctuation
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # Remove only control characters

def main():
    # Log start
    try:
        from pathlib import Path
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] TTS.pyw started\n")
    except:
        pass
    
    parser = argparse.ArgumentParser(description='Reliable TikTok TTS with Enhanced Error Handling')
    parser.add_argument('-t', help='text input', type=str)
    parser.add_argument('-txt', help='text input from a txt file', type=argparse.FileType('r', encoding="utf-8"))
    parser.add_argument('-v', help='voice selection', required=True)
    parser.add_argument('-play', help='play sound after generating audio', action='store_true')
    parser.add_argument('-stats', help='show reliability statistics', action='store_true')
    parser.add_argument('-config', help='config file path', default='data/TTSconfig.json')
    parser.add_argument('-s', '--speed', help='playback speed override', type=float, default=None)
    parser.add_argument('--volume', help='volume level (0.0 to 1.0)', type=float, default=1.0)
    parser.add_argument('--retest', help='retest API endpoints and show performance results', action='store_true')
    
    args = parser.parse_args()
    
    if not (args.t or args.txt):
        raise ValueError("Insert a valid text or txt file")
    
    if args.t and args.txt:
        raise ValueError("Only one input type is possible")
    
    text = args.t if args.t else args.txt.read()
    
    # Apply filtering only to the actual text content, not the entire string
    # This prevents filtering from affecting the "name says" part
    if args.t:
        # For direct text input, apply minimal filtering to preserve readability
        # Temporarily disable filtering to test if this is causing the issue
        # text = filter_special_characters(text)
        pass
    
    voice = Voice.from_string(args.v)
    
    if voice is None:
        raise ValueError("No valid voice has been selected.")
    
    # Initialize reliable TTS
    tts_engine = ReliableTTS(args.config)
    
    # Handle retest option
    if args.retest:
        tts_engine.retest_apis()
        tts_engine.print_stats()
        return
    
    # Override playback speed if provided
    if args.speed is not None:
        tts_engine.config["playback_speed"] = args.speed
    
    # Generate audio with volume control
    audio_data = tts_engine.tts(text, voice, args.play, args.volume)
    
    # Show stats if requested
    if args.stats:
        tts_engine.print_stats()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            from pathlib import Path
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            with open(logs_dir / "full_log.txt", 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] TTS.pyw main execution error: {e}\n")
        except:
            pass
        print(f"Fatal error in TTS.pyw: {e}")
        import traceback
        traceback.print_exc()