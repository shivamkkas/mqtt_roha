import json
from logging.handlers import RotatingFileHandler
import os
import signal
import sys
import threading
import time
import logging
import paho.mqtt.client as mqtt
from cache import StatusCache
from dotenv import load_dotenv
import argparse
import time
from datetime import datetime, timezone, timedelta

try:
    load_dotenv()
except ImportError:
    pass

# ---------------- CONFIG ---------------- #
VERSION = os.getenv("RELEASE_VERSION", "dev")
BUILD_TIME = os.getenv("BUILD_TIME", "unknown")
BROKER = os.getenv("MQTT_BROKER", "148.72.206.253")
PORT = int(os.getenv("MQTT_PORT", 1883))
DLTOPIC = os.getenv("DL_TOPIC", "dl_ROHA")

OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "sensor_ROHA")
WCR_PREFIX = "WCR"
NAME_PREFIX = "RRPM"

# ---------------- LOGGING ---------------- #

IST = timezone(timedelta(hours=5, minutes=30))

class ISTFormatter(logging.Formatter):
    def converter(self, timestamp):
        return datetime.fromtimestamp(timestamp, IST).timetuple()


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "app.log")
ENABLE_CONSOLE = os.getenv("ENABLE_CONSOLE_LOG", "false").lower() == "true"

# Root logger
logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
formatter = ISTFormatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

# -------- File Handler --------
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024,backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# -------- Console Handler (Optional) --------
if ENABLE_CONSOLE:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

slog = logging.getLogger(__name__)
slog = logging.getLogger(__name__)



cache = StatusCache()

shutdown_event = threading.Event()

class MQTTTopicSubscriber:
    def __init__(self, topic, handler, client_id):
        self.topic = topic
        self.handler = handler

        self.client = mqtt.Client(client_id=client_id)
        self.client.reconnect_delay_set(min_delay=2, max_delay=30)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while not shutdown_event.is_set():
            try:
                slog.info("Connecting to broker %s:%s", BROKER, PORT)
                self.client.connect(BROKER, PORT, 60)
                self.client.loop_forever()
            except Exception as e:
                slog.exception("MQTT connection error: %s", e)
                time.sleep(5)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            slog.info("Connected → Subscribing to %s", self.topic)
            client.subscribe(self.topic, qos=1)
        else:
            slog.error("Connection failed with code %s", rc)

    def _on_disconnect(self, client, userdata, rc):
        slog.warning("Disconnected from broker (rc=%s)", rc)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            self.handler(payload)
        except Exception:
            slog.exception("Error processing message from %s", self.topic)

    def stop(self):
        self.client.disconnect()


# ---------------- PUBLISHER ---------------- #

publisher = mqtt.Client(client_id="publisher",callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
publisher.reconnect_delay_set(2, 30)
publisher.connect(BROKER, PORT, 60)
publisher.loop_start()


# ---------------- HANDLERS ---------------- #

def status_handler(payload):
    try:
        name_list = payload.get("NAME")
        status_list = payload.get("STATUS")

        if not name_list or not status_list:
            return

        raw_name = str(name_list[0]).strip()
        value = status_list[0]

        slog.info("Status update | name=%s value=%s", raw_name, value)

        parts = raw_name.split()

        if WCR_PREFIX in parts:
            key = parts[0]
            cache.update_status(key, value)
            slog.info("Cache updated | key=%s value=%s", key, value)
        else:
            slog.warning("Not WCR, ignoring| name=%s value=%s", raw_name, value)
    except Exception:
        slog.exception("Error in status_handler")


def event_handler(payload):
    try:
        name_field = payload.get("NAME")
        if not name_field:
            return

        if isinstance(name_field, list):
            name_field = name_field[0]

        name_field = str(name_field).strip()

        if name_field == NAME_PREFIX:
            latest_key = cache.get_latest_operated_key()

            if not latest_key:
                slog.warning("No operated key found for RRPM replacement")
                return

            payload["NAME"] = latest_key

            publisher.publish(OUTPUT_TOPIC,json.dumps(payload),  qos=1)

            slog.info("Published replaced payload | name=%s", latest_key)

    except Exception:
        slog.exception("Error in event_handler")


# ---------------- GRACEFUL SHUTDOWN ---------------- #

def shutdown(sig, frame):
    slog.info("Shutdown signal received...")
    shutdown_event.set()
    publisher.loop_stop()
    publisher.disconnect()
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

def main(version: str, build_time: str):
    slog.info("==========================================")
    slog.info("Starting MQTT Service")
    slog.info("Version     : %s", version)
    slog.info("Build Time  : %s", build_time)
    slog.info("Broker      : %s:%s", BROKER, PORT)
    slog.info("DL Topic    : %s", DLTOPIC)
    slog.info("Output Topic: %s", OUTPUT_TOPIC)
    slog.info("==========================================")

    status_subscriber = MQTTTopicSubscriber(
        OUTPUT_TOPIC,
        event_handler,
        client_id="status_client",
    )

    event_subscriber = MQTTTopicSubscriber(
        DLTOPIC,
        status_handler,
        client_id="event_client",
    )

    status_subscriber.start()
    event_subscriber.start()

    slog.info("MQTT service started successfully")

    while not shutdown_event.is_set():
        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT Service")

    parser.add_argument("--version",default=os.getenv("RELEASE_VERSION", "dev"), help="Application version")

    parser.add_argument("--build-time", default=os.getenv("BUILD_TIME", "unknown"),help="Build timestamp")
    args = parser.parse_args()
    main(args.version, args.build_time)