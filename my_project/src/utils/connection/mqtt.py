# module/mqtt/client.py

from concurrent.futures import ThreadPoolExecutor
import json
import threading
import logging
import ssl
import time
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from src.config.config import MQTTConfig

# module/mqtt/client.py

class MQTTClient:
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._shutdown = threading.Event()

        self.client = mqtt.Client(client_id=config.client_id)
        self._executor = ThreadPoolExecutor(max_workers=20)

        self._subscriptions: dict[str, tuple[Callable, int]] = {}

        if config.username:
            self.client.username_pw_set(config.username, config.password)

        if config.tls:
            context = ssl.create_default_context()
            self.client.tls_set_context(context)

        self.client.reconnect_delay_set(2, 30)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    # ---------------- PUBLIC API ---------------- #

    def connect(self):
        self.client.connect(
            self.config.host,
            self.config.port,
            self.config.keepalive,
        )
        self.client.loop_start()

    def disconnect(self):
        self.logger.info("Shutting down MQTT client")
        self._shutdown.set()

        self.client.loop_stop()
        self.client.disconnect()

        # Proper executor shutdown
        self._executor.shutdown(wait=True)

    def publish(self, topic: str, payload: dict | str, qos: int = 1):
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        self.client.publish(topic, payload, qos=qos)

    def subscribe(self, topic: str, handler: Callable, qos: int = 1):
        """
        Register topic + handler.
        Can be called before or after connect().
        """
        self._subscriptions[topic] = (handler, qos)

        # If already connected, subscribe immediately
        if self.client.is_connected():
            self._subscribe_topic(topic, handler, qos)

    # ---------------- INTERNAL ---------------- #

    def _subscribe_topic(self, topic: str, handler: Callable, qos: int):
        self.client.subscribe(topic, qos=qos)
        self.client.message_callback_add(topic, self._wrap_handler(handler))
        self.logger.info("Subscribed to topic: %s", topic)

    def _wrap_handler(self, handler: Callable):
        def callback(client, userdata, msg):
            try:
                payload = msg.payload.decode()

                try:
                    payload = json.loads(payload)
                except Exception:
                    pass

                self._executor.submit(handler, msg.topic, payload)

            except Exception:
                self.logger.exception("Error handling message")

        return callback

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("MQTT connected")

            # Re-subscribe everything safely
            for topic, (handler, qos) in self._subscriptions.items():
                self._subscribe_topic(topic, handler, qos)
        else:
            self.logger.error("MQTT connection failed: %s", rc)

    def _on_disconnect(self, client, userdata, rc):
        if not self._shutdown.is_set():
            self.logger.warning("MQTT disconnected unexpectedly (rc=%s)", rc)
        else:
            self.logger.info("MQTT disconnected cleanly")