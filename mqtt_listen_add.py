import re
from datetime import datetime, UTC, timezone
import paho.mqtt.client as mqtt

from app import app
from models import db, Furniture

# --------------------------------------------------
# Setup Flask App Context (required for DB access)
# --------------------------------------------------
app.app_context().push()
# --------------------------------------------------
# MQTT CALLBACKS
# --------------------------------------------------

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe("furniture_moved/room/#")
        print("Subscribed to furniture_moved/room/#")
    else:
        print(f"Failed to connect. Return code {rc}")


def on_message(client, userdata, msg):
    try:
        print("\n Message received")
        print("Topic:", msg.topic)
        print("Raw Payload:", msg.payload)

        # Convert 4-byte little-endian payload to integer
        furniture_id = int.from_bytes(msg.payload, byteorder="little", signed=False)

        # Extract room from topic
        scanned_room = msg.topic.split("/")[-1]

        print(f"Extracted -> Furniture ID: {furniture_id}, Room: {scanned_room}")

        # Check if furniture exists
        furniture = Furniture.query.filter_by(id=furniture_id).first()
    
        if furniture:
            if scanned_room == furniture.current_room: #leaving the room while chair is inside it already
                furniture.current_room = "Corridor" 
                furniture.previous_room = scanned_room
                furniture.last_moved = datetime.now()
            
            elif furniture.current_room == "Corridor":
                furniture.previous_room = furniture.current_room
                furniture.current_room = scanned_room
                furniture.last_moved = datetime.now()
                print(f"Furniture {furniture_id} entered {scanned_room} from Corridor")
               
        else:
            print("Creating new furniture record")
            furniture = Furniture(
                id=furniture_id,
                furniture_type="Chair",  # default
                previous_room="Corridor",
                current_room=scanned_room,
                last_moved=datetime.now()
            )
            db.session.add(furniture)
        

        db.session.commit()

        print(f"Database updated: {furniture_id} → {scanned_room}")

    except Exception as e:
        print(" Error message:", e)


# --------------------------------------------------
# MQTT CLIENT SETUP
# --------------------------------------------------

client = mqtt.Client(protocol=mqtt.MQTTv5)

client.on_connect = on_connect
client.on_message = on_message

# Replace with your broker IP
client.connect("123.124.125.127", 1883)

print("MQTT Listener Started...")

client.loop_forever()