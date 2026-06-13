# python 3.12

import random
import requests
import json
import os
from dotenv import load_dotenv
from paho.mqtt import client as mqtt_client

# Load environment variables from the local .env file
load_dotenv()

# Configuration extracted from the environment with sensible defaults
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))
USERNAME = os.getenv("MQTT_USER")
PASSWORD = os.getenv("MQTT_PASSWORD")
API_URL = os.getenv("BRIDGE_API_URL")

topic = "geolocation/bridge_notification"
# App Topics
TOPIC_LISTEN = "geolocation/bridge_notification"
TOPIC_STATUS = "geolocation/bridge_notification/status"

client_id = f'subscribe-{random.randint(0, 100)}'

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {reason_code}")

    client = mqtt_client.Client(
        client_id=client_id,
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
    )
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.connect(BROKER, PORT)
    return client

def call_bridge_api() -> str:
    """Executes the external API post request and returns a string status message."""
        
    try:
        response = requests.get(API_URL)
        data = response.json()
        print(data["live"]["status"])
                
        # Check if the HTTP status code is 200-299
        if response.status_code == 200:
            # Return a specific string message back to the caller
            return f"The bridge is {data['live']['status']}"
        else:
            return f"Warning: Bridge responded with HTTP status code {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        # If the network fails entirely, return the error message as a string
        return f"Failure: Could not connect to Bridge API. Error details: {e}"

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        payload = msg.payload.decode().strip()
        print(f"Received `{payload}` from `{msg.topic}` topic")
        if payload == "request":
            print(f"request detected")
            # Clear inbound topic 
            client.publish(TOPIC_LISTEN, "", qos=1)
            # Capture the string message returned by the API helper
            api_result_message = call_bridge_api()
            
            # Log or use the returned string
            print(f"[API Log] {api_result_message}")
            client.publish(TOPIC_STATUS, api_result_message, qos=1)
        
        elif payload == "":
            # Safely catch and ignore reset message
            pass    
            
        else:
            print("Message received, but condition not met. Ignoring.")
    client.subscribe(TOPIC_LISTEN)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()