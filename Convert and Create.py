import json
import time
import sys
import os
import shutil
import datetime

# Directory path definitions
BASE_DIR = os.path.join(os.getcwd(), "TTS BSR v4 13")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
OLD_SETTINGS_DIR = os.path.join(os.getcwd(), "old settings")  # top-level folder

# GUI Communication System
GUI_LOG_FILE = os.path.join(LOGS_DIR, "gui_messages.log")

def log_to_gui(message):
    """Write message to GUI log file for display in the GUI"""
    try:
        from pathlib import Path
        Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
        with open(GUI_LOG_FILE, 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
    except:
        pass

# Function to read content from a text file and return it as a list of lines
def read_lines_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:  # UTF-8 with BOM handling
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"⚠️ Warning: {file_path} not found, using empty list")
        return []

# Function to simulate typing effect in the console
def type_effect(text, delay):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()  # Force the character to be printed immediately
        time.sleep(0.02)  # Simulate the typing speed
    time.sleep(delay)  # Delay before moving to the next line
    print()

# Function to read key-value from text file
def read_key_value(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            content = file.read().strip()
            if '=' in content:
                value = content.split('=', 1)[1].strip()
                # Remove any comments after the value
                if '#' in value:
                    value = value.split('#')[0].strip()
                return value
            return content
    except FileNotFoundError:
        print(f"⚠️ Warning: {file_path} not found, using default value")
        return "FALSE"  # Default value

# Function to read name swap data
def read_name_swap(file_path):
    name_swap_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            for line in file.readlines():
                if '=' in line:
                    name, swap = line.strip().split('=', 1)
                    name_swap_data[name.strip()] = swap.strip()
    except FileNotFoundError:
        print(f"⚠️ Warning: {file_path} not found, using empty dict")
    return name_swap_data

# Function to read priority voice data
def read_priority_voice(file_path):
    priority_voice_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            for line in file.readlines():
                if '=' in line:
                    username, voice = line.strip().split('=', 1)
                    priority_voice_data[username.strip()] = voice.strip()
    except FileNotFoundError:
        print(f"⚠️ Warning: {file_path} not found, using empty dict")
    return priority_voice_data

# Function to read voice map data
def read_voice_map(file_path):
    voice_map_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            for line in file.readlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    role, voice = line.split('=', 1)
                    voice_map_data[role.strip()] = voice.strip()
    except FileNotFoundError:
        print(f"⚠️ Warning: {file_path} not found, using default voice map")
        # Default voice map if file not found
        voice_map_data = {
            "Subscriber": "LORDCRINGE",
            "Moderator": "BAE",
            "Follow Role 0": "MARTY",
            "Follow Role 1": "MARTY",
            "Follow Role 2": "MARTY",
            "Top Gifter 1": "BESTIE",
            "Top Gifter 2": "BESTIE",
            "Top Gifter 3": "BESTIE",
            "Top Gifter 4": "BESTIE",
            "Top Gifter 5": "BESTIE",
            "BadWordVoice": "DEADPOOL",
            "Default": "EN_AU_MALE_1"
        }
    
    # Ensure BadWordVoice is always present
    if "BadWordVoice" not in voice_map_data:
        voice_map_data["BadWordVoice"] = "DEADPOOL"
        type_effect("🔧 Added missing BadWordVoice to voice map...", 0.3)
    
    return voice_map_data

# Function to check if this is a new user (no text files exist)
def is_new_user():
    text_files = ['A_ttscode.txt', 'B_filter_reply.txt', 'B_word_filter.txt', 
                  'C_priority_voice.txt', 'D_voice_map.txt', 'E_name_swap.txt', 'Voice_change.txt']
    return not any(os.path.exists(f) for f in text_files)

# Function to get default filter replies
def get_default_filter_replies():
    return [
        "I'm trying to use a bad word!",
        "We don't use that kind of language here, but I tried anyway!",
        "I am trying to trick TTS into saying something naughty?",
        "Nope! I'm not going to say that!",
        "This Voice is not for your entertainment!",
        "I am not saying that! But here is a cookie for trying.",
        "im trying to bully the TTS, im going to make it rage quit",
        "this sucks, it wont say what i want it to, I think I may take up ballet",
        "I feel like a fairy, but I have no wings",
        "I wanted to go to Narnia!, all I got was a broom closet",
        "harry potter gets more magic moments than me",
        "nothing, just nothing,",
        "I got the whipp for saying that! crack!",
        "I slipped on an ice cube in the Sahara desert",
        "I couldn't give her anymore, I just did n have da power",
        "I got told to stop being a flamingo, I had to put my foot down",
        "I used to have a handle on life, then it broke",
        "when life gives you melons you might be dyslexic"
    ]

# Function to get default word filter
def get_default_word_filter():
    return ["jiss", "cmon", "foc u", "foh q", "fah q", "gape horn", "mike rack",
            "Hugh jess", "Willie stroker", "cheese burger", "Phil Mckraken",
            "Phil Mywang", "Phil Mawank", "Hugh g Rection", "jack mehoff",
            "Dixie Normous", "Yuri Nator", "Tess tickles", "phok", "fok", "fuck"]

# Function to get complete voices data
def get_voices_data():
    return {
        "Voice_List_cheat_sheet": {
            "DISNEY VOICES": [
                {"name": "GHOSTFACE", "code": "en_us_ghostface"},
                {"name": "CHEWBACCA", "code": "en_us_chewbacca"},
                {"name": "C3PO", "code": "en_us_c3po"},
                {"name": "STITCH", "code": "en_us_stitch"},
                {"name": "STORMTROOPER", "code": "en_us_stormtrooper"},
                {"name": "ROCKET", "code": "en_us_rocket"}
            ],
            "OTHER": [
                {"name": "EN_MALE_NARRATION", "code": "en_male_narration"},
                {"name": "EN_MALE_FUNNY", "code": "en_male_funny"},
                {"name": "EN_FEMALE_EMOTIONAL", "code": "en_female_emotional"}
            ],
            "ENGLISH VOICES": [
                {"name": "PIRATE", "code": "en_male_pirate"},
                {"name": "BAE", "code": "en_female_betty"},
                {"name": "MARTY", "code": "en_male_trevor"},
                {"name": "LORDCRINGE", "code": "en_male_ukneighbor"},
                {"name": "DEADPOOL", "code": "en_male_deadpool"},
                {"name": "BESTIE", "code": "en_female_richgirl"},
                {"name": "EN_AU_MALE_1", "code": "en_au_002"},
                {"name": "EN_AU_MALE_2", "code": "en_au_003"},
                {"name": "EN_AU_FEMALE_1", "code": "en_au_female_001"},
                {"name": "EN_AU_FEMALE_2", "code": "en_au_female_002"},
                {"name": "EN_GB_MALE_1", "code": "en_gb_001"},
                {"name": "EN_GB_MALE_2", "code": "en_gb_002"},
                {"name": "EN_GB_FEMALE_1", "code": "en_gb_female_001"},
                {"name": "EN_GB_FEMALE_2", "code": "en_gb_female_002"},
                {"name": "EN_US_MALE_1", "code": "en_us_001"},
                {"name": "EN_US_MALE_2", "code": "en_us_002"},
                {"name": "EN_US_MALE_3", "code": "en_us_003"},
                {"name": "EN_US_MALE_4", "code": "en_us_004"},
                {"name": "EN_US_MALE_5", "code": "en_us_005"},
                {"name": "EN_US_MALE_6", "code": "en_us_006"},
                {"name": "EN_US_MALE_7", "code": "en_us_007"},
                {"name": "EN_US_MALE_8", "code": "en_us_008"},
                {"name": "EN_US_MALE_9", "code": "en_us_009"},
                {"name": "EN_US_MALE_10", "code": "en_us_010"},
                {"name": "EN_US_FEMALE_1", "code": "en_us_female_001"},
                {"name": "EN_US_FEMALE_2", "code": "en_us_female_002"},
                {"name": "EN_US_FEMALE_3", "code": "en_us_female_003"},
                {"name": "EN_US_FEMALE_4", "code": "en_us_female_004"},
                {"name": "EN_US_FEMALE_5", "code": "en_us_female_005"},
                {"name": "EN_US_FEMALE_6", "code": "en_us_female_006"},
                {"name": "EN_US_FEMALE_7", "code": "en_us_female_007"},
                {"name": "EN_US_FEMALE_8", "code": "en_us_female_008"},
                {"name": "EN_US_FEMALE_9", "code": "en_us_female_009"},
                {"name": "EN_US_FEMALE_10", "code": "en_us_female_010"}
            ],
            "EUROPE VOICES": [
                {"name": "FR_MALE_1", "code": "fr_001"},
                {"name": "FR_FEMALE_1", "code": "fr_female_001"},
                {"name": "DE_MALE_1", "code": "de_001"},
                {"name": "DE_FEMALE_1", "code": "de_female_001"},
                {"name": "ES_MALE_1", "code": "es_001"}
            ],
            "AMERICA VOICES": [
                {"name": "MX_MALE_1", "code": "mx_001"},
                {"name": "MX_FEMALE_1", "code": "mx_female_001"},
                {"name": "BR_MALE_1", "code": "br_001"},
                {"name": "BR_FEMALE_1", "code": "br_female_001"},
                {"name": "BR_MALE_2", "code": "br_002"}
            ],
            "ASIA VOICES": [
                {"name": "ID_MALE_1", "code": "id_001"},
                {"name": "ID_FEMALE_1", "code": "id_female_001"},
                {"name": "JP_MALE_1", "code": "jp_001"},
                {"name": "JP_FEMALE_1", "code": "jp_female_001"},
                {"name": "KR_MALE_1", "code": "kr_001"},
                {"name": "KR_FEMALE_1", "code": "kr_female_001"},
                {"name": "KR_MALE_2", "code": "kr_002"},
                {"name": "KR_FEMALE_2", "code": "kr_female_002"}
            ],
            "SINGING VOICES": [
                {"name": "ALTO", "code": "en_female_singing_01"},
                {"name": "TENOR", "code": "en_male_singing_01"},
                {"name": "WARM_BREEZE", "code": "en_female_singing_02"},
                {"name": "SUNSHINE_SOON", "code": "en_male_singing_02"}
            ],
            "NEW VOICES": [
                {"name": "EN_SEASONAL_1", "code": "en_seasonal_001"},
                {"name": "EN_SEASONAL_2", "code": "en_seasonal_002"},
                {"name": "JP_MALE_2", "code": "jp_002"},
                {"name": "JP_FEMALE_2", "code": "jp_female_002"},
                {"name": "PT_MALE_1", "code": "pt_001"},
                {"name": "PT_FEMALE_1", "code": "pt_female_001"},
                {"name": "EN_STREAMING_1", "code": "en_streaming_001"},
                {"name": "EN_STREAMING_2", "code": "en_streaming_002"},
                {"name": "EN_STREAMING_3", "code": "en_streaming_003"},
                {"name": "EN_STREAMING_4", "code": "en_streaming_004"},
                {"name": "EN_STREAMING_5", "code": "en_streaming_005"},
                {"name": "EN_STREAMING_6", "code": "en_streaming_006"},
                {"name": "EN_STREAMING_7", "code": "en_streaming_007"},
                {"name": "EN_STREAMING_8", "code": "en_streaming_008"},
                {"name": "EN_STREAMING_9", "code": "en_streaming_009"},
                {"name": "EN_STREAMING_10", "code": "en_streaming_010"},
                {"name": "EN_STREAMING_11", "code": "en_streaming_011"},
                {"name": "EN_STREAMING_12", "code": "en_streaming_012"},
                {"name": "EN_STREAMING_13", "code": "en_streaming_013"},
                {"name": "EN_STREAMING_14", "code": "en_streaming_014"},
                {"name": "EN_STREAMING_15", "code": "en_streaming_015"},
                {"name": "EN_STREAMING_16", "code": "en_streaming_016"},
                {"name": "EN_STREAMING_17", "code": "en_streaming_017"},
                {"name": "EN_STREAMING_18", "code": "en_streaming_018"},
                {"name": "EN_STREAMING_19", "code": "en_streaming_019"},
                {"name": "EN_STREAMING_20", "code": "en_streaming_020"},
                {"name": "EN_STREAMING_21", "code": "en_streaming_021"},
                {"name": "EN_STREAMING_22", "code": "en_streaming_022"},
                {"name": "EN_STREAMING_23", "code": "en_streaming_023"},
                {"name": "EN_STREAMING_24", "code": "en_streaming_024"},
                {"name": "EN_STREAMING_25", "code": "en_streaming_025"},
                {"name": "EN_STREAMING_26", "code": "en_streaming_026"},
                {"name": "EN_STREAMING_27", "code": "en_streaming_027"},
                {"name": "EN_STREAMING_28", "code": "en_streaming_028"},
                {"name": "EN_STREAMING_29", "code": "en_streaming_029"},
                {"name": "EN_STREAMING_30", "code": "en_streaming_030"}
            ]
        }
    }

def main():
    # Title and header
    type_effect("🎭 Emstar's Magical Settings Converter v2.0 🎭", 1)
    type_effect("=" * 50, 0.5)
    type_effect("Converting your dusty old text files to shiny new JSON!", 1)
    type_effect("=" * 50, 0.5)
    
    # Check if this is a new user
    new_user = is_new_user()
    if new_user:
        type_effect("🆕 New user detected! Creating complete TTS system with defaults...", 1)
    else:
        type_effect("🔄 Converting existing text files to new JSON format...", 1)
    
    # Create data directory structure
    type_effect("📁 Creating directory structure...", 0.5)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not new_user:
        os.makedirs(OLD_SETTINGS_DIR, exist_ok=True)
    
    # Create options.json
    type_effect("🔍 Looking for ancient text files...", 0.5)
    type_effect("🐔 Hmm, this one looks like it was written by a chicken...", 0.3)
    type_effect("🐔 *cluck cluck* - Found the chicken scratch!", 0.3)
    
    options_data = {
        "TT_username": "username",
        "A_ttscode": read_key_value('A_ttscode.txt') if not new_user else "FALSE",
        "Mod_only": "FALSE",
        "Mod_only_commands": ["!cam1", "!cam2"],
        "Voice_change": {
            "Enabled": read_key_value('Voice_change.txt') if not new_user else "FALSE"
        },
        "D_voice_map": read_voice_map('D_voice_map.txt') if not new_user else {
            "Subscriber": "LORDCRINGE",
            "Moderator": "BAE",
            "Follow Role 0": "MARTY",
            "Follow Role 1": "MARTY",
            "Follow Role 2": "MARTY",
            "Top Gifter 1": "BESTIE",
            "Top Gifter 2": "BESTIE",
            "Top Gifter 3": "BESTIE",
            "Top Gifter 4": "BESTIE",
            "Top Gifter 5": "BESTIE",
            "BadWordVoice": "DEADPOOL",
            "Default": "EN_AU_MALE_1"
        }
    }
    
    with open(os.path.join(DATA_DIR, 'options.json'), 'w', encoding='utf-8') as f:
        json.dump(options_data, f, indent=4, ensure_ascii=False)
    
    # Create filter.json
    type_effect("🧹 Wow, this system is dustier than my grandma's attic!", 0.3)
    type_effect("🤧 *sneezes* - Excuse me!", 0.3)
    
    word_filter = read_lines_from_file('B_word_filter.txt') if not new_user else get_default_word_filter()
    # Ensure "fuck" is in the word filter
    if "fuck" not in word_filter:
        word_filter.append("fuck")
    
    filter_data = {
        "B_filter_reply": read_lines_from_file('B_filter_reply.txt') if not new_user else get_default_filter_replies(),
        "B_word_filter": word_filter
    }
    
    with open(os.path.join(DATA_DIR, 'filter.json'), 'w', encoding='utf-8') as f:
        json.dump(filter_data, f, indent=4, ensure_ascii=False)
    
    # Create user_management.json
    type_effect("📊 Loading new settings into the modern JSON format...", 0.5)
    
    user_management_data = {
        "C_priority_voice": read_priority_voice('C_priority_voice.txt') if not new_user else {},
        "E_name_swap": read_name_swap('E_name_swap.txt') if not new_user else {}
    }
    
    with open(os.path.join(DATA_DIR, 'user_management.json'), 'w', encoding='utf-8') as f:
        json.dump(user_management_data, f, indent=4, ensure_ascii=False)
    
    # Create config.json
    type_effect("⚡ Creating JSON structure with the power of lightning!", 0.5)
    
    config_data = {
        "request_timeout": 3,
        "max_retries": 1,
        "retry_delay": 0.2,
        "playback_speed": 1.4,
        "max_concurrent_requests": 5
    }
    
    with open(os.path.join(DATA_DIR, 'config.json'), 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    
    # Create voices.json
    type_effect("🎵 Blending some random things together...", 0.5)
    
    voices_data = get_voices_data()
    
    with open(os.path.join(DATA_DIR, 'voices.json'), 'w', encoding='utf-8') as f:
        json.dump(voices_data, f, indent=4, ensure_ascii=False)
    
    # Create TTSconfig.json
    type_effect("🔧 Creating TTS configuration...", 0.5)
    
    TTSCONFIG_PATH = os.path.join(DATA_DIR, 'TTSconfig.json')
    
    tts_config_data = {
        "api_endpoints": [
            {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data", "name": "weilnet_backup"},
            {"url": "https://gesserit.co/api/tiktok-tts", "response": "base64", "name": "gesserit"},
            {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data", "name": "weilnet"}
        ],
        "last_api_test": datetime.datetime.now().isoformat(),
        "api_test_interval_minutes": 3,
        "request_timeout": 15,
        "performance_test_enabled": False,
        "max_retries": 3,
        "retry_delay": 1.5,
        "playback_speed": 1.3,
        "max_concurrent_requests": 5,
        "performance_test_text": "Hello world, this is a test message for API performance testing.",
        "performance_test_voice": "EN_US_MALE_1",
        "performance_test_timeout": 10,
        "performance_test_retries": 2,
        "reorder_threshold": 3,
        "last_performance_test": {
            "timestamp": "2025-08-06T17:15:20.006264",
            "results": ["Test 1: [OK] Success","Test 2: [OK] Success","Test 3: [OK] Success","Test 4: [OK] Success","Test 5: [OK] Success"],
            "total_tests": 5,
            "successful_tests": 5
        },
        "api_test_results": {
            "timestamp": datetime.datetime.now().isoformat(),
            "test_text": "API monitor test",
            "test_voice": "en_us_006",
            "results": {
                "weilnet_backup": {"response_time": 0, "success": True, "error": "", "rank": 1},
                "gesserit": {"response_time": 0, "success": True, "error": "", "rank": 2},
                "weilnet": {"response_time": 0, "success": True, "error": "", "rank": 3}
            }
        }
    }
    
    with open(TTSCONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(tts_config_data, f, indent=4, ensure_ascii=False)
    
    # Move original files to backup (if they exist)
    if not new_user:
        type_effect("📝 Writing a novel...", 0.3)
        type_effect("😅 Oops, I mean writing to new JSON files...", 0.3)
        type_effect("☁️ Saving files to the cloud...", 0.3)
        type_effect("☁️ Wait, this isn't the cloud, it's just my hard drive!", 0.3)
        type_effect("💾 Actually saving to local files...", 0.3)
        
        text_files = ['A_ttscode.txt', 'B_filter_reply.txt', 'B_word_filter.txt',
                      'C_priority_voice.txt', 'D_voice_map.txt', 'E_name_swap.txt', 'Voice_change.txt']
        
        for file in text_files:
            if os.path.exists(file):
                shutil.move(file, os.path.join(OLD_SETTINGS_DIR, os.path.basename(file)))
    
    # Final messages
    type_effect("🔧 Almost done, just a few more tweaks...", 0.5)
    type_effect("✨ Adding some magic dust...", 0.5)
    type_effect("🎉 TA-DA! Conversion complete!", 1)
    
    if new_user:
        type_effect("🆕 New user setup complete! You now have a fully functional TTS system.", 1)
        type_effect("📁 Check the 'TTS BSR v4 13/data' folder for all your configuration files.", 0.5)
    else:
        type_effect("✅ Conversion complete! Your old text files have been converted to JSON format.", 1)
        type_effect("📁 Original files backed up in 'old settings' folder in main directory.", 0.5)
    
    type_effect("🚀 You're ready to use your TTS system!", 1)

if __name__ == "__main__":
    main() 