import asyncio
import json
import time
import requests
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple


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


class APIMonitor:
    def __init__(self, config_path="data/TTSconfig.json"):
        self.config_path = config_path
        self.endpoints = [
            {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data", "name": "weilnet"},
            {"url": "https://gesserit.co/api/tiktok-tts", "response": "base64", "name": "gesserit"},
            {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data", "name": "weilnet_backup"}
        ]
        self.test_text = "API monitor test"
        self.test_voice = "en_us_006"
        self.timeout = 10
        self.retries = 2
        
        # Load existing config
        self.config = self._load_config()
        
        # Initialize logging
        write_log("API Monitor started", "INFO")
    
    def _load_config(self) -> Dict:
        """Load existing configuration file."""
        default_config = {
            "api_endpoints": [],
            "last_api_test": "",
            "api_test_interval_minutes": 7,
            "request_timeout": 8,
            "performance_test_enabled": False  # Disable TTS.pyw testing
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            write_log(f"Error loading config: {e}", "ERROR")
            log_to_gui(f"API Config Error: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                
            write_log("Config saved successfully", "INFO")
                
        except Exception as e:
            write_log(f"Error saving config: {e}", "ERROR")
            log_to_gui(f"API Save Error: {e}")
    
    def _test_single_endpoint(self, endpoint: Dict) -> Tuple[str, float, bool, str]:
        """Test a single endpoint and return performance metrics."""
        endpoint_name = endpoint["name"]
        start_time = time.time()
        success = False
        error_msg = ""
        
        for attempt in range(self.retries):
            try:
                response = requests.post(
                    endpoint["url"],
                    json={"text": self.test_text, "voice": self.test_voice},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Verify we can extract the expected response field
                data = response.json()
                if endpoint["response"] in data:
                    success = True
                    break
                else:
                    error_msg = f"Missing response field: {endpoint['response']}"
                    
            except requests.exceptions.Timeout:
                error_msg = "Request timeout"
            except requests.exceptions.ConnectionError:
                error_msg = "Connection error"
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP error: {e}"
            except (KeyError, json.JSONDecodeError) as e:
                error_msg = f"Response parsing error: {e}"
            except Exception as e:
                error_msg = f"Unexpected error: {e}"
            
            if attempt < self.retries - 1:
                time.sleep(0.5)  # Brief delay between retries
        
        response_time = time.time() - start_time
        return endpoint_name, response_time, success, error_msg
    
    def test_all_endpoints(self) -> List[Dict]:
        """Test all API endpoints and return ranked results."""
        write_log("Testing API endpoints...", "INFO")
        log_to_gui("Testing API endpoints")
        
        results = []
        
        # Test each endpoint
        for endpoint in self.endpoints:
            endpoint_name, response_time, success, error_msg = self._test_single_endpoint(endpoint)
            
            results.append({
                'endpoint': endpoint,
                'name': endpoint_name,
                'response_time': response_time,
                'success': success,
                'error': error_msg
            })
            
            status = "SUCCESS" if success else "FAILED"
            write_log(f"{endpoint_name}: {status} - {response_time:.2f}s {f'({error_msg})' if not success else ''}", "INFO")
        
        # Rank by performance (successful endpoints first, then by response time)
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        # Sort successful results by response time (fastest first)
        successful_results.sort(key=lambda x: x['response_time'])
        
        # Combine successful and failed results
        ranked_results = successful_results + failed_results
        
        write_log(f"API test completed: {len(successful_results)}/{len(results)} working", "INFO")
        log_to_gui(f"api test completed {len(successful_results)}/{len(results)}")
        log_to_gui("")  # Add gap
        if successful_results:
            write_log(f"Fastest: {successful_results[0]['name']} ({successful_results[0]['response_time']:.2f}s)", "INFO")
        
        return ranked_results
    
    def update_config_with_results(self, results: List[Dict]):
        """Update config with new API test results."""
        # Update the API endpoints in config
        self.config['api_endpoints'] = [r['endpoint'] for r in results]
        self.config['last_api_test'] = datetime.now().isoformat()
        self.config['performance_test_enabled'] = False  # Disable TTS.pyw testing
        
        # Add detailed results for reference
        self.config['api_test_results'] = {
            'timestamp': datetime.now().isoformat(),
            'test_text': self.test_text,
            'test_voice': self.test_voice,
            'results': {
                r['name']: {
                    'response_time': r['response_time'],
                    'success': r['success'],
                    'error': r['error'],
                    'rank': i + 1
                } for i, r in enumerate(results)
            }
        }
        
        # Save updated config
        self._save_config()
        
        write_log("Config updated with API test results", "INFO")
    
    def should_run_test(self) -> bool:
        """Check if it's time to run another API test."""
        if 'last_api_test' not in self.config:
            return True
        
        try:
            last_test = datetime.fromisoformat(self.config['last_api_test'])
            interval_minutes = self.config.get('api_test_interval_minutes', 3)
            return datetime.now() - last_test > timedelta(minutes=interval_minutes)
        except:
            return True
    
    async def monitor_loop(self):
        """Main monitoring loop."""
        write_log("API Monitor started", "INFO")
        write_log(f"Config: {self.config_path}", "INFO")
        write_log(f"Interval: {self.config.get('api_test_interval_minutes', 3)} minutes", "INFO")
        write_log(f"Endpoints: {len(self.endpoints)}", "INFO")
        
        while True:
            try:
                if self.should_run_test():
                    # Run API test
                    results = self.test_all_endpoints()
                    self.update_config_with_results(results)
                else:
                    # Wait until next test is due
                    last_test = datetime.fromisoformat(self.config['last_api_test'])
                    interval_minutes = self.config.get('api_test_interval_minutes', 3)
                    next_test = last_test + timedelta(minutes=interval_minutes)
                    wait_seconds = (next_test - datetime.now()).total_seconds()
                    
                    if wait_seconds > 0:
                        await asyncio.sleep(min(wait_seconds, 60))  # Check every minute
                    else:
                        await asyncio.sleep(1)
                        
            except KeyboardInterrupt:
                write_log("API Monitor stopped by user", "INFO")
                break
            except Exception as e:
                write_log(f"Monitor loop error: {e}", "ERROR")
                await asyncio.sleep(30)  # Wait 30 seconds before retrying

def main():
    """Main function."""
    monitor = APIMonitor()
    
    try:
        asyncio.run(monitor.monitor_loop())
    except KeyboardInterrupt:
        write_log("API Monitor stopped", "INFO")
    except Exception as e:
        write_log(f"API Monitor fatal error: {e}", "ERROR")
    finally:
        write_log("API Monitor stopped", "INFO")

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
        write_log(f"Fatal error: {e}", "ERROR") 