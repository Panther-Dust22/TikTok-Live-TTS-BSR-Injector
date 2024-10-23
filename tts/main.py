import asyncio
import websockets
import json
import os
import subprocess
import time
import random
import sys

# Custom Welcome Message
welcome_message = r"""
*****************************************
*   BSR Injector and TTS Voice system   *
*       ___ __  __    ___ ________      *
*      | __|  \/  |/\|_  )__ /__ /      *
*      | _|| |\/| >  </ / |_ \|_ \      *
*      |___|_|  |_|\//___|___/___/      *
*Created by Emstar233 And Husband (V2.5)* 
*****************************************
"""
print(welcome_message.strip())  # Use strip() to remove extra newlines around the message

# WebSocket server URL
websocket_url = "ws://localhost:21213/"

# Filters file paths
A_ttscode_file = "A_ttscode.txt"
B_word_filter_file = "B_word_filter.txt"
C_priority_voice_file = "C_priority_voice.txt"
D_voice_map_file = "D_voice_map.txt"
E_name_swap_file = "E_name_swap.txt"  # New file for name swap filter
B_filter_reply_file = "B_filter_reply.txt"  # File for random replies when a bad word is detected
Voice_change_file = "Voice_change.txt"  # File to check if voice change feature is enabled

# Track last modification times for auto-reloading files
file_mod_times = {}

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

def load_filters():
    A_ttscode = load_file(A_ttscode_file).split('=')[-1].strip() == "TRUE"
    B_word_filter = load_file(B_word_filter_file).splitlines()
    C_priority_voice = dict(line.split('=') for line in load_file(C_priority_voice_file).splitlines() if '=' in line)
    D_voice_map = dict(line.split('=') for line in load_file(D_voice_map_file).splitlines() if '=' in line)
    E_name_swap = dict(line.split('=') for line in load_file(E_name_swap_file).splitlines() if '=' in line)  # Load the name swap filter
    return A_ttscode, B_word_filter, C_priority_voice, D_voice_map, E_name_swap

def load_random_reply():
    try:
        with open(B_filter_reply_file, 'r') as file:
            replies = file.read().strip().splitlines()
            return random.choice(replies) if replies else "is trying to make me say a bad word"
    except FileNotFoundError:
        return "is trying to make me say a bad word"

def is_voice_change_enabled():
    try:
        with open(Voice_change_file, 'r') as file:
            for line in file:
                if line.startswith('Enabled='):
                    return line.split('=')[1].strip() == 'TRUE'
    except FileNotFoundError:
        print(f"Error: {Voice_change_file} not found.")
    return False  # Default to False if file is not found or doesn't contain valid data

import subprocess

def handle_voice_change(comment, nickname, isModerator):
    
    # Check if voice change is enabled
    if not is_voice_change_enabled():
        print("Voice change is disabled. Commands will not be processed.")
        return False, None, None  # Exit early if voice change is disabled

    # Only moderators should be able to change voices
    if not isModerator:
        return False, None, None  # If not a moderator, exit early

    # Check if the comment starts with a voice command
    if comment.startswith("!vadd"):
        command_parts = comment.split()
        if len(command_parts) == 3:  # Expecting !vadd name voice
            target_nickname = command_parts[1]
            voice = command_parts[2]
            # Run mod.py with the parameters for adding a voice
            subprocess.run(['python', 'mod.py', '-a', '-n', target_nickname, '-v', voice])
            return True, None, None  # Return early, indicating a voice command was handled
    
    elif comment.startswith("!vremove"):
        command_parts = comment.split()
        if len(command_parts) == 2:  # Expecting !vremove name
            target_nickname = command_parts[1]
            # Run mod.py with parameters for removing a voice
            subprocess.run(['python', 'mod.py', '-r', '-n', target_nickname])
            return True, None, None  # Return early, indicating a voice command was handled
    
    elif comment.startswith("!vchange"):
        command_parts = comment.split()
        if len(command_parts) == 3:  # Expecting !vchange name voice
            target_nickname = command_parts[1]
            voice = command_parts[2]
            # Run mod.py with parameters for changing a voice
            subprocess.run(['python', 'mod.py', '-c', '-n', target_nickname, '-v', voice])
            return True, None, None  # Return early, indicating a voice command was handled

    return False, None, None  # No voice change action was taken

def check_for_file_updates():
    global file_mod_times
    files = [A_ttscode_file, B_word_filter_file, C_priority_voice_file, D_voice_map_file, B_filter_reply_file, Voice_change_file, E_name_swap_file]  # Added E_name_swap_file
    
    files_updated = False
    for file in files:
        try:
            mod_time = os.path.getmtime(file)
            if file not in file_mod_times or mod_time != file_mod_times[file]:
                file_mod_times[file] = mod_time
                files_updated = True
        except FileNotFoundError:
            pass
    
    if files_updated:
        print()
        print("Files updated, reloading filters...")
        print()
        return load_filters()
    
    return None

def passes_filters(data, A_ttscode, B_word_filter, C_priority_voice, D_voice_map, E_name_swap):
    comment = data.get('comment', '')
    nickname = data.get('nickname', '')
    isModerator = data.get('isModerator', False)
    isSubscriber = data.get('isSubscriber', False)
    topGifterRank = data.get('topGifterRank', None)
    followRole = data.get('followRole', 0)

    # Role descriptions for display
    follow_status_display = {0: "NO", 1: "YES", 2: "FRIEND"}.get(followRole, "UNKNOWN")

    # Print user information in the required format
    print(f"{nickname} | Subscriber: {isSubscriber} | Moderator: {isModerator} | Top Gifter: {topGifterRank} | Follower: {follow_status_display}")
    print(f"{comment}")

    # Convert comment to lowercase for case-insensitive comparison
    lower_comment = comment.lower()

    # Apply Name Swap Filter
    if nickname in E_name_swap:
        original_nickname = nickname
        nickname = E_name_swap[nickname]  # Swap the nickname
        print(f"Name swap: {original_nickname} -> {nickname}")
    
    # Check for voice commands first
    voice_change_result, new_comment, voice = handle_voice_change(comment, nickname, isModerator)
    if voice_change_result:
        return True, None, None, nickname  # If a voice change action was taken, return immediately

    # Continue with normal filtering only if no voice change was done
    # Filter A: !tts check
    if A_ttscode and comment.startswith('!tts'):
        comment = comment[4:].strip()  # Remove the "!tts" command and trim leading spaces
    elif A_ttscode:
        return False, None, None, nickname

    # Filter B: Word filter
    for bad_word in B_word_filter:
        if bad_word.lower() in lower_comment:  # Check if the lowercase bad word is in the lowercase comment
            # Replace comment with a random response
            new_comment = f", {load_random_reply()}"
            voice = D_voice_map.get('Default', None)  # Use default voice for this
            print(f"Bad word detected: Replacing comment with: {new_comment}")
            return True, new_comment, voice, nickname

    # Filter C: Priority voice check
    voice = C_priority_voice.get(nickname, None)

    # If voice is found in C_priority_voice, skip remaining filters and use this voice
    if voice:
        print(f"Priority voice found: {nickname} will use voice {voice}")
        return True, comment, voice, nickname

    # Filter D: Voice map
    if not voice:
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
            voice = D_voice_map.get(f'Follow Role {followRole}', None)

        # Finally, if no voice found after all checks, use default
        if not voice:
            voice = D_voice_map.get('Default', None)

    # If the voice is "NONE", return early
    if voice == "NONE":
        return False, None, None, nickname


    # Display passing details
    print(f"Passed filters: {nickname} will use voice {voice}")
    return True, comment, voice, nickname

def run_tts(nickname, comment, voice):
    # Here we use the nickname after the swap
    command = ['python', 'TTS.py', '-t', f"{nickname} says {comment}", '-v', voice, '-p']
    print(f"Running TTS command: {' '.join(command)}")
    subprocess.run(command)
    print()

async def connect_to_websocket():
    # Load filters initially
    A_ttscode, B_word_filter, C_priority_voice, D_voice_map, E_name_swap = load_filters()

    while True:
        try:
            async with websockets.connect(websocket_url) as websocket:
                print("Connected To TikFinity")
                
                async for message in websocket:
                    try:
                        # Check if any filter files have been updated and reload if needed
                        updated_filters = check_for_file_updates()
                        if updated_filters:
                            A_ttscode, B_word_filter, C_priority_voice, D_voice_map, E_name_swap = updated_filters

                        data = json.loads(message)  # Parse incoming message as JSON
                        if data.get("event") == "chat":
                            chat_data = data.get("data", {})

                            # Apply filters
                            passes, comment, voice, nickname = passes_filters(
                                chat_data, A_ttscode, B_word_filter, C_priority_voice, D_voice_map, E_name_swap
                            )
                            
                            if passes:
                                run_tts(nickname, comment, voice)
                    except json.JSONDecodeError:
                        pass  # Ignore non-JSON messages
                    except Exception as e:
                        print(f"Error processing message: {e}")

        except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
            print(f"Disconnected from TikFinity: {e}")
            print("Reconnecting in 2 seconds...")
            await asyncio.sleep(2)  # Wait for 2 seconds before attempting to reconnect

# Main entry point
if __name__ == "__main__":
    asyncio.run(connect_to_websocket())
