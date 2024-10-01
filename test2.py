import websocket
import json
import uuid
import logging
import struct

# Set up logging
logging.basicConfig(level=logging.INFO)

correlation_id = str(uuid.uuid4())
print(correlation_id)

# Define the WebSocket URL and authentication headers
ws_url = "wss://smartapisocket.angelone.in/smart-stream"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IlM1NTMyOTU3OSIsInJvbGVzIjowLCJ1c2VydHlwZSI6IlVTRVIiLCJ0b2tlbiI6ImV5SmhiR2NpT2lKU1V6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUoxYzJWeVgzUjVjR1VpT2lKamJHbGxiblFpTENKMGIydGxibDkwZVhCbElqb2lkSEpoWkdWZllXTmpaWE56WDNSdmEyVnVJaXdpWjIxZmFXUWlPalFzSW5OdmRYSmpaU0k2SWpNaUxDSmtaWFpwWTJWZmFXUWlPaUkyTXpWa1lqQTFPQzB5TWpSaUxUTXpOalV0T0dFeFppMWhZMk00TTJKaU1HTXdOMkVpTENKcmFXUWlPaUowY21Ga1pWOXJaWGxmZGpFaUxDSnZiVzVsYldGdVlXZGxjbWxrSWpvMExDSndjbTlrZFdOMGN5STZleUprWlcxaGRDSTZleUp6ZEdGMGRYTWlPaUpoWTNScGRtVWlmWDBzSW1semN5STZJblJ5WVdSbFgyeHZaMmx1WDNObGNuWnBZMlVpTENKemRXSWlPaUpUTlRVek1qazFOemtpTENKbGVIQWlPakUzTWpjM09ETXpNalVzSW01aVppSTZNVGN5TnpZNU5qRTBPQ3dpYVdGMElqb3hOekkzTmprMk1UUTRMQ0pxZEdraU9pSmlPR000TXpoaFl5MDRNbU5pTFRRM01Ea3RPR0ZqT0MwME16TXlZbVE0WVRNMU5tSWlmUS5qSlJNZzJCYzg0Q1pyX1Y1NENqNTlRa0paX0k4U0JvTGVOazk1VWJWT0FLaEFwQ2lVa1RJQWN2c01EeUdhNU5PMFFjdTBXVnZaMGNLSGpTRU1FYVJ5ZFRsQzh0a245blB1cmdGQTFQcWNJcXNjQlJ6VFFQMXh6TWFfQnZUQXNvNnAzQ1JrUE9lQUlfNjExLXd3cjhnOXBRYVlrQzVZVlNkWC1hY2YyS3VZbnMiLCJBUEktS0VZIjoiTW9sT1NaVFIiLCJpYXQiOjE3Mjc2OTYyMDgsImV4cCI6MTcyNzc4MzMyNX0.05DIiJr1b-USiJXQ9fB49NKp9e1sHW3rIFgWlgSi0N_rGmfZQn7bxpXFYmkLEVXrKjArDdVXUOd6UnckUKo10w",
    "x-api-key": "T4MHVpXH",
    "x-client-code": "J263557",
    "x-feed-token": "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IlM1NTMyOTU3OSIsImlhdCI6MTcyNzY5NjIwOCwiZXhwIjoxNzI3NzgyNjA4fQ.0DAMPyFALFPY-hYBVvG6JX9xfUqZ8tjJIa4UMtXZRZNUdtCiL6BKMdCH0g6IWiFCT2u2m1snkt-bRVUe_H5Zag"
}

request_json = {
    "correlationID": correlation_id,
    "action": 1,
    "params": {
        "mode": 1,
        "tokenList": [
            {
                "exchangeType": 2,
                "tokens": [
                    "44512",
                ]
            },
        ]
    }
}

def parse_binary_message(message):
    try:
        # Assuming the message structure is:
        # [4 bytes: message length][2 bytes: message type][remaining bytes: payload]
        print(f"message data  ---> {type(message)}")
        message_length = struct.unpack('>I', message[:4])[0]
        message_type = struct.unpack('>H', message[4:6])[0]
        payload = message[6:]

        return {
            "message_length": message_length,
            "message_type": message_type,
            "payload": payload.hex()  # Convert to hex for logging
        }
    except struct.error as e:
        logging.error(f"Failed to parse binary message: {e}")
        return None

def on_message(ws, message):
    try:
        parsed_data = parse_binary_message(message)
        if parsed_data:
            logging.info(f"Received binary message: {parsed_data}")
            #print({parsed_data["payload"][43:]})
        else:
            logging.info(f"Received unknown binary message: {message.hex()}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")

def on_error(ws, error):
    logging.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.info(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")

def on_open(ws):
    logging.info("WebSocket connection opened")
    ws.send(json.dumps(request_json))
    logging.info(f"Request JSON sent: {json.dumps(request_json, indent=4)}")

# Create a WebSocket app instance and run it
ws = websocket.WebSocketApp(
    ws_url,
    header=headers,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.on_open = on_open
ws.run_forever()