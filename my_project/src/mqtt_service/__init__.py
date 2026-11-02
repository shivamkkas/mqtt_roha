        # src/mqtt_service/config/settings.py

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    VERSION = os.getenv("RELEASE_VERSION", "dev")
    BUILD_TIME = os.getenv("BUILD_TIME", "unknown")

    BROKER = os.getenv("MQTT_BROKER", "148.72.206.253")
    PORT = int(os.getenv("MQTT_PORT", 1883))
    DLTOPIC = os.getenv("DL_TOPIC", "dl_ROHA")
    OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "sensor_ROHA")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    ENABLE_CONSOLE = os.getenv("ENABLE_CONSOLE_LOG", "false").lower() == "true"