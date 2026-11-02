# mqtt_service/service.py
import time

from src.config.config import MQTTConfig
from src.utils.connection.mqtt import MQTTClient
from .cache.cache import StatusCache
import logging


class MQTTService:
    def __init__(self, mqtt_client:MQTTClient, cache:StatusCache, dl_topic:str, output_topic:str):
        self.logger = logging.getLogger(__name__)
        self.mqtt = mqtt_client
        self.cache = cache
        self.dl_topic = dl_topic
        self.output_topic = output_topic

        self.WCR_PREFIX = "WCR"
        self.NAME_PREFIX = "RRPM"

    def start(self):
        self.logger.info("Registering MQTT subscriptions")

        self.mqtt.subscribe(self.dl_topic, self.status_handler)
        self.mqtt.subscribe(self.output_topic, self.event_handler)

    # -------- HANDLERS -------- #

    def status_handler(self, topic, payload):
        try:
            name_list = payload.get("NAME")
            status_list = payload.get("STATUS")

            if not name_list or not status_list:
                return

            raw_name = str(name_list[0]).strip()
            value = status_list[0]

            self.logger.debug("Status update | name=%s value=%s", raw_name, value)

            parts = raw_name.split()

            if self.WCR_PREFIX in parts and value == "1":
                key = parts[0]
                self.cache.update_status(key, value)
                self.logger.info("Cache updated | key=%s value=%s", key, value)

        except Exception:
            self.logger.exception("Error in status_handler")

    def event_handler(self, topic, payload):
        try:
            self.logger.info("Event received | topic=%s payload=%s", topic, payload)
            name_field = payload.get("NAME")
            if not name_field:
                return

            if isinstance(name_field, list):
                name_field = name_field[0]

            name_field = str(name_field).strip()

            if name_field == self.NAME_PREFIX:
                max_retries = 3
                retry_delay = 0.6
                latest_key = None

                for attempt in range(max_retries):
                    latest_key = self.cache.get_latest_operated_key()
                    if latest_key:
                        break

                    self.logger.debug("No operated key found, retrying... attempt=%d", attempt + 1)
                    time.sleep(retry_delay)

                if not latest_key:
                    self.logger.warning("No operated key found after retries")
                    return

                payload["NAME"] = latest_key
                self.mqtt.publish(self.output_topic, payload, qos=1)

                self.logger.info("Published replaced payload | name=%s", latest_key)

        except Exception:
            self.logger.exception("Error in event_handler")