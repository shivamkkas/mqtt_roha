import json
import threading
import time
import paho.mqtt.client as mqtt
from cache import StatusCache
import logging
slog = logging.getLogger(__name__)
DLTOPIC = "dl_ROHA"
OUTPUT_TOPIC = "sensor_ROHA"
WCR_PREFIX = "WCR"
NAME_PREFIX = "RRPM"
# ---------------- CACHE ---------------- #
cache = StatusCache()


# ---------------- GENERIC SUBSCRIBER ---------------- #
class MQTTTopicSubscriber:
    def __init__(self, broker, port, topic, message_handler, client_id=None):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.message_handler = message_handler

        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            slog.info(f" Connected → Subscribing to {self.topic}")
            client.subscribe(self.topic)
        else:
            slog.error(f"❌ Connection failed for {self.topic}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except Exception as e:
            slog.error(f"Invalid JSON on {self.topic}:", e)
            return

        self.message_handler(payload)

    def stop(self):
        self.client.disconnect()


# ---------------- PUBLISHER CLIENT ---------------- #
publisher = mqtt.Client(client_id="publisher", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
publisher.connect("148.72.206.253", 1883, 60)
publisher.loop_start()

def status_handler(payload):
    name_list = payload.get("NAME")
    status_list = payload.get("STATUS")

    if not name_list or not status_list:
        return

    raw_name = str(name_list[0]).strip()
    value = status_list[0]

    slog.info("Status Update Raw:", raw_name, value)

    # Split by space
    parts = raw_name.split()

    # Check if any part exactly equals "WCR"
    if WCR_PREFIX in parts:
        slog.info(" Found WCR in NAME")

        # If you want to store only WCR (not full string)
        cache.update_status(parts[0], value)

        slog.info(f"Cache Updated: {parts[0]} → {value}")
    else:
        slog.warning("Not WCR, ignoring")

def event_handler(payload):
    slog.info(" Event Topic:", payload)

    name_field = payload.get("NAME")

    if not name_field:
        slog.info(" NAME field missing")
        return

    # If NAME is list → take first value
    if isinstance(name_field, list):
        name_field = name_field[0]

    name_field = str(name_field).strip()

  
    # -------- RRPM Replacement Logic -------- #
    if name_field == NAME_PREFIX:
        time.sleep(2)  # Wait for cache to update
        latest_key = cache.get_latest_operated_key()

        if latest_key:
            slog.info(f" Replacing RRPM with {latest_key}")
            payload["NAME"] = latest_key 
        else:
            slog.warning("⚠ No latest status=1 key found")
            return
        
        publisher.publish(OUTPUT_TOPIC, json.dumps(payload))
        slog.info("Published:", payload)
     
    
if __name__ == "__main__":
    broker = "148.72.206.253"
    port = 1883

    # Status Topic Subscriber
    status_subscriber = MQTTTopicSubscriber(
        broker,
        port,
        OUTPUT_TOPIC,
        event_handler,
        client_id="status_client"
    )

    # Event Topic Subscriber
    event_subscriber = MQTTTopicSubscriber(
        broker,
        port,
        DLTOPIC,
        status_handler,
        client_id="event_client"
    )

    status_subscriber.start()
    event_subscriber.start()

    while True:
        time.sleep(1)