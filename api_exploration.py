#!/usr/bin/env python3
"""
TikTok TTS API Exploration Script
Attempts to find proper voice listing endpoints or parameters
"""

import requests
import json
from urllib.parse import urljoin

ENDPOINTS = [
    "https://tiktok-tts.weilnet.workers.dev/api/generation",
    "https://countik.com/api/text/speech", 
    "https://gesserit.co/api/tiktok-tts"
]

def explore_endpoint(base_url):
    """Explore an endpoint for voice listing capabilities"""
    print(f"\n🔍 Exploring: {base_url}")
    print("=" * 60)
    
    # 1. Try common voice listing endpoints
    voice_endpoints = [
        "/voices", "/api/voices", "/list", "/api/list", 
        "/models", "/api/models", "/available", "/api/available",
        "/info", "/api/info", "/status", "/api/status"
    ]
    
    for endpoint in voice_endpoints:
        try:
            url = urljoin(base_url, endpoint)
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ GET {endpoint} -> {response.status_code}")
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            elif response.status_code != 404:
                print(f"🔸 GET {endpoint} -> {response.status_code}")
        except:
            pass
    
    # 2. Try OPTIONS request to see available methods
    try:
        response = requests.options(base_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ OPTIONS -> {response.status_code}")
            print(f"   Allow header: {response.headers.get('Allow', 'Not set')}")
            print(f"   Headers: {dict(response.headers)}")
    except:
        pass
    
    # 3. Try GET request to main endpoint
    try:
        response = requests.get(base_url, timeout=5)
        print(f"🔸 GET main -> {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:300]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
    except:
        pass
    
    # 4. Try POST with empty body or help request
    help_requests = [
        {"help": True},
        {"action": "list"},
        {"action": "voices"},
        {"method": "voices"},
        {"command": "list"},
        {"list": True},
        {"voices": True},
        {},  # Empty request
    ]
    
    for req_data in help_requests:
        try:
            response = requests.post(base_url, json=req_data, timeout=5)
            if response.status_code == 200:
                print(f"✅ POST {req_data} -> {response.status_code}")
                try:
                    data = response.json()
                    if "voices" in str(data).lower() or "list" in str(data).lower():
                        print(f"   🎯 Potential voice data: {json.dumps(data, indent=2)}")
                    else:
                        print(f"   Response: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
        except:
            pass
    
    # 5. Try common query parameters
    query_params = [
        "?voices", "?list", "?help", "?info", "?available",
        "?action=list", "?action=voices", "?method=voices"
    ]
    
    for param in query_params:
        try:
            response = requests.get(base_url + param, timeout=5)
            if response.status_code == 200:
                print(f"✅ GET {param} -> {response.status_code}")
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
        except:
            pass

def check_tiktok_official_docs():
    """Check if there are any official TikTok TTS documentation endpoints"""
    print("\n🔍 Checking for TikTok TTS documentation...")
    print("=" * 60)
    
    # Try common TikTok/ByteDance endpoints
    tiktok_endpoints = [
        "https://api.tiktok.com/tts",
        "https://api.tiktok.com/v1/tts", 
        "https://tts.tiktok.com",
        "https://tts-api.tiktok.com",
        "https://api16-normal-c-useast1a.tiktokv.com/tts",
        "https://api22-normal-c-useast1a.tiktokv.com/tts"
    ]
    
    for endpoint in tiktok_endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"🔸 {endpoint} -> {response.status_code}")
            if response.status_code == 200:
                print(f"   Content: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ {endpoint} -> {str(e)[:50]}...")

def analyze_known_working_voice():
    """Analyze a known working voice request to understand the API structure"""
    print("\n🔍 Analyzing known working voice request structure...")
    print("=" * 60)
    
    # Test with a known working voice to see response structure
    test_voice = "en_us_ghostface"
    test_text = "Hello"
    
    for i, endpoint_info in enumerate([
        {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data"},
        {"url": "https://countik.com/api/text/speech", "response": "v_data"},
        {"url": "https://gesserit.co/api/tiktok-tts", "response": "base64"}
    ]):
        print(f"\nEndpoint {i+1}: {endpoint_info['url']}")
        try:
            response = requests.post(
                endpoint_info["url"],
                json={"text": test_text, "voice": test_voice},
                timeout=10
            )
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response keys: {list(data.keys())}")
                    
                    # Look for any metadata that might indicate available voices
                    for key, value in data.items():
                        if key != endpoint_info["response"]:  # Skip the audio data
                            print(f"  {key}: {value}")
                    
                    # Check if there are any error messages that might give hints
                    if "error" in data:
                        print(f"  Error info: {data['error']}")
                        
                except Exception as e:
                    print(f"  JSON parse error: {e}")
                    print(f"  Raw response: {response.text[:200]}...")
            else:
                print(f"  Error response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"  Request failed: {e}")

def test_invalid_voice():
    """Test with an invalid voice to see if we get useful error messages"""
    print("\n🔍 Testing with invalid voice to analyze error responses...")
    print("=" * 60)
    
    invalid_voice = "definitely_not_a_real_voice_12345"
    test_text = "Hello"
    
    for i, endpoint_info in enumerate([
        {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data"},
        {"url": "https://countik.com/api/text/speech", "response": "v_data"},
        {"url": "https://gesserit.co/api/tiktok-tts", "response": "base64"}
    ]):
        print(f"\nEndpoint {i+1}: {endpoint_info['url']}")
        try:
            response = requests.post(
                endpoint_info["url"],
                json={"text": test_text, "voice": invalid_voice},
                timeout=10
            )
            print(f"Status: {response.status_code}")
            
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
                
        except Exception as e:
            print(f"Request failed: {e}")

def main():
    print("=== TIKTOK TTS API EXPLORATION ===")
    print("Looking for proper voice listing endpoints...")
    
    # Explore each endpoint
    for endpoint in ENDPOINTS:
        explore_endpoint(endpoint)
    
    # Check for official TikTok docs
    check_tiktok_official_docs()
    
    # Analyze working requests
    analyze_known_working_voice()
    
    # Test invalid voice
    test_invalid_voice()
    
    print("\n" + "=" * 60)
    print("EXPLORATION COMPLETE")
    print("=" * 60)
    print("If no voice listing endpoints were found, the APIs may not")
    print("provide a way to enumerate available voices programmatically.")
    print("This would explain why brute-force testing is commonly used.")

if __name__ == "__main__":
    main()