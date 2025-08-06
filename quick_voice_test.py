#!/usr/bin/env python3
"""
Quick voice test - tests specific voice patterns that are most likely to exist
"""

import requests
import json
from datetime import datetime

ENDPOINTS = [
    {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data"},
    {"url": "https://countik.com/api/text/speech", "response": "v_data"},
    {"url": "https://gesserit.co/api/tiktok-tts", "response": "base64"}
]

# High-probability voice patterns based on research
HIGH_PRIORITY_VOICES = [
    # Mentioned in online sources
    'derek', 'trickster', 'austin_butler', 'news_reporter', 'adam',
    
    # Sequential numbered patterns
    'en_us_011', 'en_us_012', 'en_us_013', 'en_us_014', 'en_us_015',
    'en_us_003', 'en_us_004', 'en_us_005', 'en_us_008',
    'en_uk_002', 'en_uk_004', 'en_uk_005',
    'en_au_003', 'en_au_004', 'en_au_005',
    
    # Character voice variations
    'en_us_yoda', 'en_us_darth_vader', 'en_us_batman', 'en_us_joker',
    'en_us_spongebob', 'en_us_patrick', 'en_us_squidward',
    
    # Common voice descriptors
    'en_male_deep', 'en_female_young', 'en_male_robot', 'en_female_robot',
    'en_us_storyteller', 'en_us_narrator', 'en_us_announcer',
    
    # Language variants
    'fr_003', 'de_003', 'es_001', 'es_003', 'it_001', 'it_002',
    'pt_001', 'ru_001', 'hi_001', 'ar_001', 'th_001', 'vi_001',
    'zh_001', 'zh_002', 'ja_002', 'ko_001',
    
    # Special patterns
    'en_female_voice_lady', 'jessie', 'voice_lady',
    'en_male_funny_2', 'en_female_emotional_2'
]

def test_voice(endpoint, voice):
    """Test a single voice"""
    try:
        response = requests.post(
            endpoint["url"],
            json={"text": "Testing voice", "voice": voice},
            timeout=8
        )
        
        if response.status_code == 200:
            data = response.json()
            if endpoint["response"] in data and data[endpoint["response"]]:
                return True
        return False
    except:
        return False

def main():
    print("=== QUICK TIKTOK TTS VOICE TEST ===")
    print(f"Testing {len(HIGH_PRIORITY_VOICES)} high-priority voice patterns")
    print()
    
    results = {}
    
    for i, endpoint in enumerate(ENDPOINTS):
        print(f"Testing endpoint {i+1}: {endpoint['url']}")
        endpoint_results = []
        
        for j, voice in enumerate(HIGH_PRIORITY_VOICES):
            print(f"  [{j+1:3d}/{len(HIGH_PRIORITY_VOICES)}] {voice:30}", end=" ... ")
            
            if test_voice(endpoint, voice):
                print("✓ WORKS")
                endpoint_results.append(voice)
            else:
                print("✗")
        
        results[endpoint['url']] = endpoint_results
        print(f"  Found {len(endpoint_results)} working voices on this endpoint\n")
    
    # Summary
    all_working = set()
    for voices in results.values():
        all_working.update(voices)
    
    print("=" * 50)
    print("QUICK TEST RESULTS")
    print("=" * 50)
    
    if all_working:
        print(f"🎉 Found {len(all_working)} NEW working voices:")
        for voice in sorted(all_working):
            print(f"  ✓ {voice}")
    else:
        print("😕 No new voices found in this quick test")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"quick_test_results_{timestamp}.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "tested_voices": HIGH_PRIORITY_VOICES,
            "working_voices": sorted(list(all_working)),
            "results_by_endpoint": {url: voices for url, voices in results.items()}
        }, f, indent=2)
    
    print(f"\nResults saved to: quick_test_results_{timestamp}.json")

if __name__ == "__main__":
    main()