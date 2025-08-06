#!/usr/bin/env python3
"""
Voice Discovery Script for TikTok TTS APIs
Tests various voice IDs to see which ones are supported by the API endpoints
"""

import requests
import json
import time
from typing import List, Dict, Set
import sys

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

# Known voices from the current implementation
KNOWN_VOICES = [
    # Disney voices
    'en_us_ghostface', 'en_us_chewbacca', 'en_us_c3po', 'en_us_stitch', 
    'en_us_stormtrooper', 'en_us_rocket',
    # English voices  
    'en_male_pirate', 'en_male_ghosthost', 'en_female_madam_leota', 'en_male_wizard',
    'en_male_santa_narration', 'en_female_grandma', 'en_male_cupid', 'en_female_betty',
    'en_male_trevor', 'en_female_pansino', 'en_female_shenna', 'en_male_ukbutler',
    'en_male_ukneighbor', 'en_male_olantekkers', 'en_male_ashmagic', 'en_male_jarvis',
    'en_male_grinch', 'en_female_richgirl', 'en_female_makeup', 'en_male_cody',
    'en_male_jomboy', 'en_male_deadpool',
    # Standard voices
    'en_au_001', 'en_au_002', 'en_uk_001', 'en_uk_003', 'en_us_001', 'en_us_002',
    'en_us_006', 'en_us_007', 'en_us_009', 'en_us_010',
    # Other languages
    'fr_001', 'fr_002', 'de_001', 'de_002', 'es_002', 'es_mx_002', 'br_001', 'br_003',
    'br_004', 'br_005', 'id_001', 'jp_001', 'jp_003', 'jp_005', 'jp_006', 'kr_002',
    'kr_003', 'kr_004',
    # Singing voices
    'en_female_f08_salut_damour', 'en_male_m03_lobby', 'en_female_f08_warmy_breeze',
    'en_male_m03_sunshine_soon',
    # Other
    'en_male_narration', 'en_male_funny', 'en_female_emotional'
]

# Potential new voices to test based on research
POTENTIAL_VOICES = [
    # Mentioned in online sources
    'derek', 'trickster', 'austin_butler', 'news_reporter', 'adam',
    
    # Additional standard voice patterns
    'en_us_011', 'en_us_012', 'en_us_013', 'en_us_014', 'en_us_015',
    'en_uk_004', 'en_uk_005', 'en_au_003', 'en_au_004',
    'en_in_001', 'en_in_002', 'en_ca_001', 'en_ca_002',
    
    # More language variants
    'fr_003', 'fr_004', 'de_003', 'de_004', 'es_001', 'es_003', 'es_004',
    'es_us_001', 'es_us_002', 'es_es_001', 'es_ar_001', 'es_mx_001',
    'pt_001', 'pt_002', 'pt_br_001', 'pt_br_002',
    'it_001', 'it_002', 'it_003',
    'zh_001', 'zh_002', 'zh_003', 'zh_004', 'zh_cn_001', 'zh_cn_002',
    'zh_tw_001', 'zh_tw_002', 'zh_hk_001',
    'ja_001', 'ja_002', 'ja_004', 'jp_007', 'jp_008',
    'ko_001', 'ko_002', 'kr_001', 'kr_005', 'kr_006',
    'ru_001', 'ru_002', 'ru_003',
    'hi_001', 'hi_002', 'hi_003',
    'ar_001', 'ar_002', 'ar_003',
    'th_001', 'th_002', 'vi_001', 'vi_002',
    'nl_001', 'nl_002', 'sv_001', 'no_001', 'da_001',
    
    # Character voice patterns
    'en_us_darth_vader', 'en_us_yoda', 'en_us_batman', 'en_us_joker',
    'en_us_morgan_freeman', 'en_us_spongebob', 'en_us_patrick',
    'en_us_squidward', 'en_us_mr_krabs',
    
    # More personality voices
    'en_female_voice_lady', 'en_male_deep', 'en_female_siri_like',
    'en_male_robot', 'en_female_robot', 'en_male_announcer',
    'en_female_announcer', 'en_male_storyteller', 'en_female_storyteller'
]

def test_voice(endpoint: Dict, voice: str, test_text: str = "Hello world") -> bool:
    """Test if a voice works with a given endpoint"""
    try:
        response = requests.post(
            endpoint["url"], 
            json={"text": test_text, "voice": voice},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if endpoint["response"] in data and data[endpoint["response"]]:
                return True
    except Exception as e:
        pass
    
    return False

def discover_voices(endpoints: List[Dict], voices_to_test: List[str]) -> Dict[str, Set[str]]:
    """Test all voices against all endpoints and return results"""
    results = {}
    
    for i, endpoint in enumerate(endpoints):
        print(f"\nTesting endpoint {i+1}: {endpoint['url']}")
        results[endpoint['url']] = set()
        
        for j, voice in enumerate(voices_to_test):
            print(f"  Testing voice {j+1}/{len(voices_to_test)}: {voice}", end=" ... ")
            
            if test_voice(endpoint, voice):
                print("✓ WORKS")
                results[endpoint['url']].add(voice)
            else:
                print("✗ Failed")
            
            # Small delay to be respectful to the APIs
            time.sleep(0.5)
    
    return results

def main():
    print("TikTok TTS Voice Discovery Script")
    print("=" * 50)
    print(f"Known voices in current implementation: {len(KNOWN_VOICES)}")
    print(f"Potential new voices to test: {len(POTENTIAL_VOICES)}")
    print()
    
    # Test known voices first to verify the script works
    print("Step 1: Verifying known voices work...")
    sample_known = KNOWN_VOICES[:5]  # Test first 5 known voices
    known_results = discover_voices(ENDPOINTS, sample_known)
    
    working_endpoints = []
    for endpoint_url, working_voices in known_results.items():
        if working_voices:
            working_endpoints.append(endpoint_url)
            print(f"✓ Endpoint {endpoint_url} is working ({len(working_voices)} voices confirmed)")
        else:
            print(f"✗ Endpoint {endpoint_url} appears to be down or changed")
    
    if not working_endpoints:
        print("❌ No endpoints are working. APIs may be down or changed.")
        return
    
    print(f"\n✓ {len(working_endpoints)} endpoint(s) are working")
    
    # Test potential new voices
    print(f"\nStep 2: Testing {len(POTENTIAL_VOICES)} potential new voices...")
    
    # Only test with working endpoints
    working_endpoint_configs = [ep for ep in ENDPOINTS if ep['url'] in working_endpoints]
    new_results = discover_voices(working_endpoint_configs, POTENTIAL_VOICES)
    
    # Summarize results
    print("\n" + "=" * 50)
    print("DISCOVERY RESULTS")
    print("=" * 50)
    
    all_new_voices = set()
    for endpoint_url, voices in new_results.items():
        all_new_voices.update(voices)
    
    if all_new_voices:
        print(f"🎉 Found {len(all_new_voices)} NEW working voices:")
        for voice in sorted(all_new_voices):
            print(f"  - {voice}")
        
        print("\nDetailed breakdown by endpoint:")
        for endpoint_url, voices in new_results.items():
            print(f"\n{endpoint_url}:")
            if voices:
                for voice in sorted(voices):
                    print(f"  ✓ {voice}")
            else:
                print("  (no new voices found)")
    else:
        print("😕 No new working voices discovered")
        print("This could mean:")
        print("  - Your current implementation is already comprehensive")
        print("  - The test voice IDs don't match the actual API voice IDs")
        print("  - The APIs have changed their voice offerings")
    
    print(f"\nTotal voices in your current implementation: {len(KNOWN_VOICES)}")
    print(f"Potential new voices discovered: {len(all_new_voices)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)