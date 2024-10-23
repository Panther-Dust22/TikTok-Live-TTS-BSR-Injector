import asyncio
import websockets
import json
import random
import threading
from time import time

# Global variable to hold all websocket connections
connected_clients = set()  # A set to store active WebSocket connections

def get_user_input(loop):
    """Function to handle user input in a separate thread."""
    print("Enter comments to send (type 'exit' to quit):")
    while True:
        comment = input()  # Get user input
        if comment.lower() == 'exit':
            print("Exiting...")
            break  # Exit if user types 'exit'

        # Generate random user details
        user_id = str(random.randint(1000000000000000000, 9999999999999999999))
        sec_uid = "<redacted>"
        unique_id = "zerodytester"
        nickname = "roger100"
        profile_picture_url = "https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0...webp"

        # User badges
        user_badges = [
            {
                "type": "pm_mt_moderator_im",
                "name": "Moderator"
            },
            {
                "type": "image",
                "displayType": 1,
                "url": "https://p19-webcast.tiktokcdn.com/webcast-va/rankl...image"
            },
            {
                "type": "image",
                "displayType": 1,
                "url": "https://p19-webcast.tiktokcdn.com/webcast-va/....~...image"
            }
        ]

        # User details
        user_details = {
            "createTime": str(int(time())),  # Current timestamp
            "bioDescription": "",
            "profilePictureUrls": [
                profile_picture_url,
                profile_picture_url,
                profile_picture_url
            ]
        }

        # Follow info
        follow_info = {
            "followingCount": 10000,
            "followerCount": 606,
            "followStatus": 0,
            "pushStatus": 0
        }

        # Create the message payload in the required structure
        message = {
            "event": "chat",
            "data": {
                "comment": comment,
                "userId": user_id,
                "secUid": sec_uid,
                "uniqueId": unique_id,
                "nickname": nickname,
                "profilePictureUrl": profile_picture_url,
                "followRole": 0,  # 0 = none
                "userBadges": user_badges,
                "userDetails": user_details,
                "followInfo": follow_info,
                "isModerator": False,  # Change made here: now a string
                "isNewGifter": False,  # Also changed to string if necessary
                "isSubscriber": False,   # Also changed to string if necessary
                "topGifterRank": 0,
                "msgId": str(random.randint(1000000000000000000, 9999999999999999999)),  # Random message ID
                "createTime": str(int(time()))  # Current timestamp
            }
        }
        # Broadcast the message to all connected clients
        if connected_clients:  # Ensure there are active connections
            asyncio.run_coroutine_threadsafe(broadcast_message(message), loop)
        else:
            print("No active WebSocket connections.")

async def broadcast_message(message):
    """Send the message to all connected clients."""
    message_json = json.dumps(message)  # Convert message to JSON string
    if connected_clients:  # Check if there are any connected clients
        # Send the message to each connected client
        for websocket in connected_clients:
            try:
                await websocket.send(message_json)
                print(f"Sent to client: {message}")  # Log the sent message
            except Exception as e:
                print(f"Error sending message to a client: {e}")

async def handler(websocket, path):
    """Main handler for the WebSocket connection."""
    connected_clients.add(websocket)  # Add the new websocket connection to the set
    print("WebSocket connection established.")  # Debug statement
    try:
        await websocket.wait_closed()  # Keep the connection open until closed
    finally:
        connected_clients.remove(websocket)  # Remove the websocket connection when closed
        print("WebSocket connection closed.")  # Debug statement

async def main():
    """Start the WebSocket server."""
    async with websockets.serve(handler, "localhost", 21213):
        print("WebSocket server running on ws://localhost:21213/")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)  # Set the new loop as the current loop

    # Start the WebSocket server in a separate thread
    server_thread = threading.Thread(target=lambda: loop.run_until_complete(main()))
    server_thread.start()

    # Start the user input thread in the main thread
    get_user_input(loop)
