import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import datetime


cl = mqtt.Client(protocol=mqtt.MQTTv5, callback_api_version=CallbackAPIVersion.VERSION2)

def on_publish(*args, **kwargs):
    print("publish", args, kwargs)


def on_message(client, unk, msg: mqtt.MQTTMessage):
    tag_number = int.from_bytes(msg.payload, byteorder='little', signed=False)
    topic = msg.topic

    print(f"[{datetime.datetime.now().time().isoformat()}] message {tag_number=} {topic=}")


cl.on_publish = on_publish
cl.on_message = on_message

errcode = cl.connect('123.124.125.127', 1883)

print(f"cl.connect(...) -> {errcode}")

res = cl.subscribe("furniture_moved/room/#")

print(f"cl.subscribe(...) -> {res}")

try:
    cl.loop_forever()
finally:
    cl.disconnect()


