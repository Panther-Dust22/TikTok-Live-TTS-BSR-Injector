import argparse
import os
import requests
import base64
import re
from json import load
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from playsound import playsound
from enum import Enum

# Enum to define available voices for text-to-speech conversion
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

    @staticmethod
    def from_string(input_string: str):
        """Function to check if a string matches any enum member name."""
        for voice in Voice:
            if voice.name == input_string:
                return voice
        return None

# Load endpoint data from the endpoints.json file
def load_endpoints() -> List[Dict[str, str]]:
    """Load endpoint configurations from a JSON file."""
    endpoints = [
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
    return endpoints

def tts(
    text: str,
    voice: Voice,
    output_file_path: str = "output.mp3",
    play_sound: bool = False
):
    """Main function to convert text to speech and save to a file."""
    
    # Validate input arguments
    validate_args(text, voice)

    # Load endpoint data
    endpoint_data = load_endpoints()

    # Iterate over endpoints to find a working one
    for endpoint in endpoint_data:
        # Generate audio bytes from the current endpoint
        audio_bytes = fetch_audio_bytes(endpoint, text, voice)
        
        if audio_bytes:
            # Save the generated audio to a file
            save_audio_file(output_file_path, audio_bytes)
        
            # Optionally play the audio file
            if play_sound:
                playsound(output_file_path)
                
                # Delete the audio file after playing
                if os.path.exists(output_file_path):
                    os.remove(output_file_path)
                    print(f"{output_file_path} has been deleted.")
                else:
                    print("The file does not exist.")
                 
            # Stop after processing a valid endpoint
            break

def save_audio_file(output_file_path: str, audio_bytes: bytes):
    """Write the audio bytes to a file."""
    if os.path.exists(output_file_path):
        os.remove(output_file_path)
        
    with open(output_file_path, "wb") as file:
        file.write(audio_bytes)

def fetch_audio_bytes(endpoint: Dict[str, str], text: str, voice: Voice) -> Optional[bytes]:
    """Fetch audio data from an endpoint and decode it."""
    
    text_chunks = split_text(text)
    audio_chunks = ["" for _ in range(len(text_chunks))]

    # Function to generate audio for each text chunk
    def generate_audio_chunk(index: int, text_chunk: str):
        try:
            response = requests.post(endpoint["url"], json={"text": text_chunk, "voice": voice.value})
            response.raise_for_status()
            audio_chunks[index] = response.json()[endpoint["response"]]
        except (requests.RequestException, KeyError):
            return

    # Use ThreadPoolExecutor for better thread management
    with ThreadPoolExecutor() as executor:
        executor.map(generate_audio_chunk, range(len(text_chunks)), text_chunks)

    if any(not chunk for chunk in audio_chunks):
        return None

    # Concatenate and decode audio data from all chunks
    return base64.b64decode("".join(audio_chunks))

def validate_args(text: str, voice: Voice):
    """Validate the input arguments."""
    if not isinstance(voice, Voice):
        raise TypeError("'voice' must be of type Voice")
    
    if not text:
        raise ValueError("text must not be empty")

def split_text(text: str) -> List[str]:
    """Split text into chunks of 300 characters or less."""
    separated_chunks = re.findall(r'.*?[.,!?:;-]|.+', text)
    return separated_chunks

def filter_special_characters(text):
    # Remove special characters using regex
    return re.sub(r'[^A-Za-z0-9 ]+', '', text)

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description='TikTok TTS')
    parser.add_argument('-t', help='text input', type=lambda s: filter_special_characters(s))
    parser.add_argument('-txt', help='text input from a txt file', type=argparse.FileType('r', encoding="utf-8"))
    parser.add_argument('-v', help='voice selection')
    parser.add_argument('-o', help='output filename', default='output.mp3')
    parser.add_argument('-play', help='play sound after generating audio', action='store_true')

    args = parser.parse_args()

    # Check if given values are valid
    if not (args.t or args.txt):
        raise ValueError("Insert a valid text or txt file")
    
    if args.t and args.txt:
        raise ValueError("Only one input type is possible")

    # Read text from file if specified
    text = args.t if args.t else args.txt.read()

    voice = Voice.from_string(args.v)
    if voice is None:
        raise ValueError("No valid voice has been selected.")

    # Execute TTS
    tts(text, voice, args.o, args.play)

if __name__ == "__main__":
    main()
