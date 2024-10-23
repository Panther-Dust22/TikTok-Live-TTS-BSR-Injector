@echo off
cd "%~dp0\bsr-twitch"
start index.html
cd "%~dp0\tts"
py -X utf8 main.py
