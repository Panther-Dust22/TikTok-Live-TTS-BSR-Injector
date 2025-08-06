#!/usr/bin/env python3
"""
Comprehensive TikTok TTS Voice Discovery Script
Tests extensive voice patterns and saves results to files
"""

import requests
import json
import time
from datetime import datetime
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# API endpoints from the original TTS.py file
ENDPOINTS = [
    {
        "url": "https://tiktok-tts.weilnet.workers.dev/api/generation",
        "response": "data"
    },
    {
        "url": "https://countik.com/api/text/speech", 
        "response": "v_data"
    },
    {
        "url": "https://gesserit.co/api/tiktok-tts",
        "response": "base64"
    }
]

# Known voices from current implementation
KNOWN_VOICES = [
    'en_us_ghostface', 'en_us_chewbacca', 'en_us_c3po', 'en_us_stitch', 
    'en_us_stormtrooper', 'en_us_rocket', 'en_male_pirate', 'en_male_ghosthost', 
    'en_female_madam_leota', 'en_male_wizard', 'en_male_santa_narration', 
    'en_female_grandma', 'en_male_cupid', 'en_female_betty', 'en_male_trevor', 
    'en_female_pansino', 'en_female_shenna', 'en_male_ukbutler', 
    'en_male_ukneighbor', 'en_male_olantekkers', 'en_male_ashmagic', 
    'en_male_jarvis', 'en_male_grinch', 'en_female_richgirl', 'en_female_makeup', 
    'en_male_cody', 'en_male_jomboy', 'en_male_deadpool', 'en_au_001', 'en_au_002', 
    'en_uk_001', 'en_uk_003', 'en_us_001', 'en_us_002', 'en_us_006', 'en_us_007', 
    'en_us_009', 'en_us_010', 'fr_001', 'fr_002', 'de_001', 'de_002', 'es_002', 
    'es_mx_002', 'br_001', 'br_003', 'br_004', 'br_005', 'id_001', 'jp_001', 
    'jp_003', 'jp_005', 'jp_006', 'kr_002', 'kr_003', 'kr_004', 
    'en_female_f08_salut_damour', 'en_male_m03_lobby', 'en_female_f08_warmy_breeze',
    'en_male_m03_sunshine_soon', 'en_male_narration', 'en_male_funny', 'en_female_emotional'
]

# Generate comprehensive test voices
def generate_test_voices():
    voices = []
    
    # 1. Systematic numbered patterns
    languages = ['en_us', 'en_uk', 'en_au', 'en_ca', 'en_in', 'fr', 'de', 'es', 'it', 
                 'pt', 'br', 'jp', 'ja', 'kr', 'ko', 'zh', 'ru', 'hi', 'ar', 'th', 'vi',
                 'nl', 'sv', 'no', 'da', 'pl', 'cs', 'hu', 'ro', 'bg', 'hr', 'sk', 'sl',
                 'et', 'lv', 'lt', 'mt', 'fi', 'el', 'tr', 'uk', 'be', 'mk', 'sq', 'sr',
                 'bs', 'me', 'is', 'fo', 'ga', 'gd', 'cy', 'br', 'co', 'eu', 'ca', 'gl',
                 'pt_br', 'es_mx', 'es_us', 'es_ar', 'fr_ca', 'zh_cn', 'zh_tw', 'zh_hk']
    
    for lang in languages:
        for i in range(1, 21):  # Test 001-020
            voices.append(f"{lang}_{i:03d}")
    
    # 2. Character voices - comprehensive list
    characters = [
        'ghostface', 'chewbacca', 'c3po', 'stitch', 'stormtrooper', 'rocket',
        'darth_vader', 'yoda', 'luke_skywalker', 'princess_leia', 'han_solo',
        'batman', 'joker', 'superman', 'wonder_woman', 'flash', 'aquaman',
        'spongebob', 'patrick', 'squidward', 'mr_krabs', 'sandy', 'plankton',
        'mickey_mouse', 'minnie_mouse', 'donald_duck', 'goofy', 'scrooge',
        'homer_simpson', 'bart_simpson', 'marge_simpson', 'lisa_simpson',
        'peter_griffin', 'stewie_griffin', 'brian_griffin', 'lois_griffin',
        'shrek', 'fiona', 'donkey', 'puss_in_boots',
        'woody', 'buzz_lightyear', 'rex', 'hamm', 'slinky',
        'elsa', 'anna', 'olaf', 'kristoff', 'sven',
        'simba', 'timon', 'pumbaa', 'rafiki', 'scar',
        'pikachu', 'ash_ketchum', 'mewtwo', 'charizard',
        'mario', 'luigi', 'bowser', 'peach', 'toad', 'yoshi',
        'sonic', 'tails', 'knuckles', 'shadow', 'eggman',
        'optimus_prime', 'bumblebee', 'megatron', 'starscream'
    ]
    
    for char in characters:
        voices.extend([f'en_us_{char}', f'en_{char}', char])
    
    # 3. Celebrity/personality voices
    personalities = [
        'morgan_freeman', 'samuel_jackson', 'will_smith', 'dwayne_johnson',
        'scarlett_johansson', 'emma_stone', 'ryan_reynolds', 'robert_downey_jr',
        'chris_hemsworth', 'chris_evans', 'mark_ruffalo', 'jeremy_renner',
        'donald_trump', 'joe_biden', 'barack_obama', 'hillary_clinton',
        'elon_musk', 'bill_gates', 'steve_jobs', 'mark_zuckerberg',
        'gordon_ramsay', 'jamie_oliver', 'anthony_bourdain',
        'david_attenborough', 'morgan_freeman', 'neil_degrasse_tyson',
        'stephen_hawking', 'albert_einstein', 'nikola_tesla',
        'austin_butler', 'derek', 'adam', 'trickster', 'news_reporter'
    ]
    
    for person in personalities:
        voices.extend([f'en_us_{person}', f'en_{person}', person])
    
    # 4. Voice types and descriptors
    descriptors = [
        'male', 'female', 'deep', 'high', 'young', 'old', 'child', 'teen', 'adult',
        'robot', 'alien', 'monster', 'ghost', 'demon', 'angel', 'fairy',
        'narrator', 'announcer', 'storyteller', 'newsreader', 'reporter',
        'comedian', 'serious', 'funny', 'scary', 'spooky', 'creepy',
        'friendly', 'angry', 'sad', 'happy', 'excited', 'calm', 'energetic',
        'whisper', 'shout', 'sing', 'rap', 'opera', 'classical',
        'british', 'american', 'australian', 'canadian', 'irish', 'scottish',
        'southern', 'northern', 'eastern', 'western', 'urban', 'rural',
        'formal', 'casual', 'professional', 'amateur', 'expert', 'beginner'
    ]
    
    for desc in descriptors:
        voices.extend([
            f'en_us_{desc}', f'en_{desc}', f'en_male_{desc}', f'en_female_{desc}',
            f'en_us_male_{desc}', f'en_us_female_{desc}', desc
        ])
    
    # 5. Common TTS voice names patterns
    common_names = [
        'alex', 'alice', 'allison', 'ava', 'bella', 'bruce', 'daniel', 'david',
        'emily', 'emma', 'fiona', 'fred', 'george', 'heather', 'jack', 'jane',
        'john', 'kate', 'karen', 'kevin', 'laura', 'linda', 'lisa', 'mark',
        'mary', 'michael', 'nancy', 'paul', 'peter', 'rachel', 'robert', 'ruth',
        'samantha', 'sarah', 'steve', 'susan', 'thomas', 'tom', 'victoria',
        'william', 'zoe', 'aria', 'ethan', 'luna', 'noah', 'olivia', 'liam',
        'sophia', 'mason', 'isabella', 'jacob', 'mia', 'william', 'charlotte'
    ]
    
    for name in common_names:
        voices.extend([f'en_us_{name}', f'en_{name}', name])
    
    # 6. Special patterns found in research
    special_patterns = [
        'voice_lady', 'deep_voice', 'siri_like', 'alexa_like', 'google_like',
        'cortana_like', 'jessie', 'voice_man', 'storyteller', 'narrator_male',
        'narrator_female', 'commercial_male', 'commercial_female',
        'tutorial_male', 'tutorial_female', 'gaming_male', 'gaming_female'
    ]
    
    for pattern in special_patterns:
        voices.extend([f'en_us_{pattern}', f'en_{pattern}', pattern])
    
    # Remove duplicates and return
    return list(set(voices))

def test_voice_endpoint(endpoint, voice, test_text="Hello world", timeout=5):
    """Test a single voice against a single endpoint"""
    try:
        response = requests.post(
            endpoint["url"],
            json={"text": test_text, "voice": voice},
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if endpoint["response"] in data and data[endpoint["response"]]:
                return True, "SUCCESS"
            else:
                return False, f"Missing {endpoint['response']} field"
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "TIMEOUT"
    except requests.exceptions.RequestException as e:
        return False, f"REQUEST_ERROR: {str(e)}"
    except Exception as e:
        return False, f"ERROR: {str(e)}"

def test_voices_batch(endpoint, voices, results_lock, results, progress_lock, progress):
    """Test a batch of voices against an endpoint"""
    endpoint_url = endpoint["url"]
    endpoint_results = []
    
    for voice in voices:
        success, message = test_voice_endpoint(endpoint, voice)
        
        if success:
            endpoint_results.append(voice)
            print(f"✓ {endpoint_url.split('/')[-2]}: {voice}")
        
        # Update progress
        with progress_lock:
            progress["completed"] += 1
            if progress["completed"] % 100 == 0:
                print(f"Progress: {progress['completed']}/{progress['total']} tested")
        
        time.sleep(0.1)  # Rate limiting
    
    # Store results
    with results_lock:
        results[endpoint_url] = endpoint_results

def main():
    print("=== COMPREHENSIVE TIKTOK TTS VOICE DISCOVERY ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Generate all test voices
    print("Generating test voice patterns...")
    all_test_voices = generate_test_voices()
    print(f"Generated {len(all_test_voices)} voice patterns to test")
    
    # Remove known working voices to focus on discovering new ones
    new_voices_to_test = [v for v in all_test_voices if v not in KNOWN_VOICES]
    print(f"Testing {len(new_voices_to_test)} potentially new voices")
    print(f"Skipping {len(KNOWN_VOICES)} known working voices")
    print()
    
    # Test a few known voices first to verify endpoints work
    print("Step 1: Verifying endpoints with known voices...")
    working_endpoints = []
    sample_known = KNOWN_VOICES[:3]
    
    for endpoint in ENDPOINTS:
        working_count = 0
        for voice in sample_known:
            success, _ = test_voice_endpoint(endpoint, voice)
            if success:
                working_count += 1
        
        if working_count > 0:
            working_endpoints.append(endpoint)
            print(f"✓ {endpoint['url']} - {working_count}/{len(sample_known)} known voices work")
        else:
            print(f"✗ {endpoint['url']} - appears to be down")
    
    if not working_endpoints:
        print("❌ No endpoints are working!")
        return
    
    print(f"\n✓ {len(working_endpoints)} endpoint(s) are working")
    print()
    
    # Main discovery phase
    print("Step 2: Discovering new voices...")
    results = {}
    results_lock = threading.Lock()
    progress = {"completed": 0, "total": len(new_voices_to_test) * len(working_endpoints)}
    progress_lock = threading.Lock()
    
    # Split voices into batches for parallel processing
    batch_size = 50
    voice_batches = [new_voices_to_test[i:i+batch_size] for i in range(0, len(new_voices_to_test), batch_size)]
    
    # Use ThreadPoolExecutor for parallel testing
    with ThreadPoolExecutor(max_workers=len(working_endpoints)) as executor:
        futures = []
        
        for endpoint in working_endpoints:
            for batch in voice_batches:
                future = executor.submit(test_voices_batch, endpoint, batch, results_lock, results, progress_lock, progress)
                futures.append(future)
        
        # Wait for all tasks to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in batch: {e}")
    
    # Compile results
    print("\n" + "=" * 60)
    print("DISCOVERY RESULTS")
    print("=" * 60)
    
    all_new_voices = set()
    for endpoint_url, voices in results.items():
        all_new_voices.update(voices)
    
    # Save results to files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed results
    with open(f"voice_discovery_results_{timestamp}.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "known_voices_count": len(KNOWN_VOICES),
            "tested_voices_count": len(new_voices_to_test),
            "new_voices_found": sorted(list(all_new_voices)),
            "results_by_endpoint": {url: sorted(voices) for url, voices in results.items()},
            "known_voices": KNOWN_VOICES
        }, f, indent=2)
    
    # Save summary report
    with open(f"voice_discovery_summary_{timestamp}.txt", "w") as f:
        f.write("TikTok TTS Voice Discovery Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write(f"Known voices in current implementation: {len(KNOWN_VOICES)}\n")
        f.write(f"New voice patterns tested: {len(new_voices_to_test)}\n")
        f.write(f"NEW voices discovered: {len(all_new_voices)}\n\n")
        
        if all_new_voices:
            f.write("🎉 NEW WORKING VOICES FOUND:\n")
            f.write("-" * 30 + "\n")
            for voice in sorted(all_new_voices):
                f.write(f"  {voice}\n")
            f.write("\nDetailed breakdown by endpoint:\n")
            for endpoint_url, voices in results.items():
                f.write(f"\n{endpoint_url}:\n")
                if voices:
                    for voice in sorted(voices):
                        f.write(f"  ✓ {voice}\n")
                else:
                    f.write("  (no new voices found)\n")
        else:
            f.write("😕 No new working voices discovered\n")
            f.write("This could mean:\n")
            f.write("  - Your current implementation is comprehensive\n")
            f.write("  - The APIs have limited voice offerings\n")
            f.write("  - Voice IDs use different naming patterns\n")
    
    # Console output
    if all_new_voices:
        print(f"🎉 DISCOVERED {len(all_new_voices)} NEW WORKING VOICES!")
        print("\nNEW VOICES:")
        for voice in sorted(all_new_voices):
            print(f"  {voice}")
    else:
        print("😕 No new working voices discovered")
    
    print(f"\nResults saved to:")
    print(f"  - voice_discovery_results_{timestamp}.json")
    print(f"  - voice_discovery_summary_{timestamp}.txt")
    print(f"\nTotal voices in current implementation: {len(KNOWN_VOICES)}")
    print(f"New voices discovered: {len(all_new_voices)}")
    print(f"Completed at: {datetime.now()}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()