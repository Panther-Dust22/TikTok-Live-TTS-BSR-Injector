```
****************************************
*  BSR Injector and TTS Voice system   *
*      ___ __  __    ___ ________      *
*     | __|  \/  |/\|_  )__ /__ /      *
*     | _|| |\/| >  </ / |_ \|_ \      *
*     |___|_|  |_|\//___|___/___/      *
*Created by Emstar233 And Husband (V 2)*
****************************************
```


This is the UPDATED bsr injector with TTS now combined, streamer.bot is no longer needed and everything is ran through python and a browser. TIKFINITY APP, BEATSABER PLUS(if playing beatsaber) & TWITCH ACCOUNT STILL REQUIRED!

#1 Run the "Setup" file this will install Python, once complete click close on the python window and some more black windows will flash up, wait for them to finish, this is just installing extra bits needed to make this system work

#2 once complete run/double click "Start".

#NOTE# you will have 2 windows open, one CMD window (black) and one browser, the following instructions are for the browser. (both can be minimised once setup is completed)

FOR THE BROWSER WINDOW (BSR injector)

#3 leave the left details as Default
#3b Click Get OAuth Token link and follow instructions
#3c copy the 0Auth Token, Tick the "enable Twitch IRC" box and paste your token into OAuth text box without the "oauth:" bit (just letters and numbers)
#4d in the other 2 boxes add your twitch username, twitch.tv/USERNAME (just the username part(your one not this one)) and hit save

click the connect box, start TikFinity and both sides should say connected. (if not hit refresh) (you will need to tick the "enable twitch IRC checkbox each time you start)

#NOTE# users should still request a song in beatsaber with "bsr code" without the !, BeatsaberPlus must be installed, now ONLY MODS (and yourself) can open and close the queue with the !open and !close commands, if anyone else tries it will be ignored (set open and close commands to ALL in BS+), all songs will be tagged by the requester automatically (hover over request queue to see who sent it).

THATS IT! you are running (if you don't want TTS just close the CMD(black) window, if you don't want bsr injector/twitch passthrough close the browser (both can be run on their own, Just TTS when playing other games, just bsr if you don't want TTS, or together for the full experience) if errors occur and tikfinity or twitch disconnects they should auto reconnect themselves, some comments can be missed due to the nature of how this works.

now to customise it... (TTS ONLY)

run/double click the "Edit TTS Filters" file, this will open all editable files in notepad, when you make a change press ctrl+s or file and save, the changes will automatically update in TTS within 30 seconds, no need to restart it.

there are 7 files you can edit and a Voice list (cheat sheet) all reference to names in the following are for Nick Names aka Display names, if you reply to someone's comment in TikTok, the @name is the bit you need, without the @, copy and paste is your friend here

A-ttscode.txt - set to TRUE if users need to use !tts to talk, otherwise set to FALSE

B_word_filter.txt - List of words that are not allowed to go through the TTS system (some words can be spelt differently to sound bad) (add as many as you want, 1 word per line) (these are not case sensitive)

B_filter_reply.txt - sentences used to replace bad words at random, this is used to "humiliate" those that try to mess with TTS(add as many as you want, 1 sentence per line)

C_priority_voices.txt - used to give voices to your favourite people if they are not a mod/sub etc for example, me, when im in your live :)

D_voice_map.txt used for voices for Mods, Subs, Top 5 Gifters, follow status and the default voice, if the default voice is set to NONE then ONLY those previous statuses will get voices, if a default voice is set then everyone gets that voice unless otherwise stated by other settings

E_name_swap.txt - this is used for names that TTS cannot pronounce because it uses symbols for example, to use this just copy in the display name and write what you want TTS to say the name as for that user.

Voice_change.txt - when set to TRUE, MODS ONLY (and yourself) may change the voices of your viewers, this is all done using the Priority voices file, Your mods will be able to add, remove and change someone's voice using the commands !vadd !vremove !vchange for example (moderator eddy) !vadd cookie TRICKSTER
cookie would then get that voice until changed or deleted, you may use this as rewards for in game challenges or as an incentive for better interaction, or anything you can think of.
(note this doesn't ALWAYS work because of TIKTOK filters)

the other text file that opens is the Voice List Cheat Sheet, use the first (CAPS) section of any of the names in the list in the respective areas where you want to use those voices, I would also recommend putting a copy of the voice list as well as the commands for adding, changing and removing voices on your discord for moderators and viewers to see.


REMEMBER TO SAVE FILES FOR CHANGES TO TAKE EFFECT!
