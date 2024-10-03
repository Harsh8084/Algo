import socketio
import hmac
import hashlib
import json
import time

# WebSocket endpoint
socketEndpoint = 'wss://stream.coindcx.com'

# Initialize SocketIO client
sio = socketio.Client()

# Control flag for message processing
processing_enabled = True

# Define a function to handle disconnection
@sio.event
def disconnect():
    print("Disconnected from server")

# Define a function to handle incoming candlestick data
@sio.on('candlestick')
def on_candlestick(response):
    global processing_enabled
    if processing_enabled:
        print("Candlestick data:", response["data"])
        # Disable processing for 10 seconds
        print("Pausing message processing...")
        processing_enabled = False
        time.sleep(10)  # Sleep for 10 seconds
        processing_enabled = True
        print("Resumed message processing.")

# Function to connect and subscribe to the WebSocket
def connect_and_subscribe():
    try:
        # Connect to the WebSocket server
        sio.connect(socketEndpoint, transports='websocket')
        print("Connected to the WebSocket server")

        # API credentials
        key = 'ea28fa11c8193a0cd8e606428bcbc6d437baf36e96a1e8c9'
        secret = '61e9fdb944f218281a2e1eba75af1dc9e3f62af89b47d04c13c5900d3a980959'

        # Generate signature
        secret_bytes = bytes(secret, encoding='utf-8')
        body = {"channel": "B-BTC_USDT_15m-futures"}
        json_body = json.dumps(body, separators=(',', ':'))
        signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

        # Join channel with authentication
        sio.emit('join', {'channelName': 'B-BTC_USDT_15m-futures', 'authSignature': signature, 'apiKey': key})
        print("Subscribed to channel 'B-BTC_USDT_15m-futures'")

        # Keep the script running to listen for messages
        while True:
            time.sleep(1)  # Short sleep to allow other operations to continue

    except KeyboardInterrupt:
        print("Script terminated by user")
    finally:
        sio.disconnect()
        print("Disconnected from the WebSocket server")

# Call the function to connect and subscribe
connect_and_subscribe()
