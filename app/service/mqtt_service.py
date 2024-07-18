import json
from fastapi import APIRouter, Depends, Request
import paho.mqtt.client as mqtt
from apscheduler.schedulers.background import BackgroundScheduler
from app.stdio import print_error, time_now, print_debug

router = APIRouter(tags=["MQTT"])
# MQTT settings
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_PUBLISH = "/pks_mqtt/device/"
MQTT_SUBSCRIBE = "/pks_mqtt/server/#"


# MQTT client setup
mqtt_client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print_debug("Connected with result code " + str(rc))
    client.subscribe(MQTT_SUBSCRIBE)


def on_message(client, userdata, msg):
    print_debug(msg.topic + " " + str(msg.payload))


def on_subscribe(client, userdata, mid, granted_qos):
    print_debug(f"Subscribed to topic with QoS {granted_qos}")


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_subscribe = on_subscribe


# Background task to keep MQTT client loop running
def start_mqtt():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()


async def startup():
    start_mqtt()


async def shutdown():
    mqtt_client.loop_stop()


def send_to_mqtt():
    data = {
        "server": "FastAPI",
        # "temperature": 24.0,
        # "humidity": 50.0,
        "timestamp": time_now().strftime("%Y-%m-%d %H:%M"),
    }
    payload = json.dumps(data)
    mqtt_client.publish(MQTT_PUBLISH + "broadcast", payload)
    print(f"Published: {payload}")


scheduler = BackgroundScheduler()
scheduler.add_job(send_to_mqtt, "interval", seconds=60)
scheduler.start()


# @app.get("/")
# async def read_root():
#     return {"Hello": "World"}

# @app.post("/publish/")
# async def publish_message(topic: str, message: str):
#     mqtt_client.publish(topic, message)
#     return {"status": "Message published"}
