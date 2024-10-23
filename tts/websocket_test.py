import websocket
import json

# Function to handle messages from the WebSocket
def on_message(ws, message):
    # Parse the incoming message
    data = json.loads(message)
    
    # Check if the event is a chat event
    if data.get("event") == "chat":
        chat_data = data.get("data", {})
        
        # Extract and display the relevant data
        print(f"{chat_data.get('uniqueId')} writes: {chat_data.get('comment')}")
        
        # Prepare the output in the desired format
        formatted_data = {
            "comment": chat_data.get("comment"),
            "userId": chat_data.get("userId"),
            "secUid": chat_data.get("secUid"),
            "uniqueId": chat_data.get("uniqueId"),
            "nickname": chat_data.get("nickname"),
            "profilePictureUrl": chat_data.get("profilePictureUrl"),
            "followRole": chat_data.get("followRole"),
            "userBadges": chat_data.get("userBadges"),
            "userDetails": chat_data.get("userDetails"),
            "followInfo": chat_data.get("followInfo"),
            "isModerator": chat_data.get("isModerator"),
            "isNewGifter": chat_data.get("isNewGifter"),
            "isSubscriber": chat_data.get("isSubscriber"),
            "topGifterRank": chat_data.get("topGifterRank"),
            "msgId": chat_data.get("msgId"),
            "createTime": chat_data.get("createTime")
        }

        # Print formatted data
        print(json.dumps(formatted_data, indent=4))


# Function to handle WebSocket errors
def on_error(ws, error):
    print(f"Error: {error}")

# Function to handle WebSocket closure
def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

# Function to handle WebSocket opening
def on_open(ws):
    print("Connection established")

# Main function to connect to the WebSocket
def start_websocket():
    websocket_url = "ws://localhost:21213/"
    
    # Create a WebSocket object and assign event handlers
    ws = websocket.WebSocketApp(websocket_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    
    # Run the WebSocket in a loop
    ws.run_forever()

if __name__ == "__main__":
    start_websocket()
