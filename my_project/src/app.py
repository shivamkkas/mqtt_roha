import sys
import signal
import uvicorn
from fastapi import FastAPI
from src.config.initialize import initialise
from src.mqtt_service.run import MQTTService
from src.mqtt_service.cache.cache import StatusCache
from src.utils.connection.mqtt import MQTTClient, MQTTConfig
def main():
    conf, logger, _, _ = initialise()
    logger.info("Application started")

    # MQTT Setup
    mqtt_conf = MQTTConfig(
        host=conf.mqtt.host,
        port=conf.mqtt.port,
        client_id="mqtt-service2",
    )

    mqtt_client = MQTTClient(mqtt_conf)
    mqtt_client.connect()

    cache = StatusCache(ttl_seconds= conf.app.ttl_seconds)

    service = MQTTService(
        mqtt_client=mqtt_client,
        cache=cache,
        dl_topic=conf.app.dl_topic,
        output_topic=conf.app.output_topic,
    )

    service.start()

    # FastAPI App
    app = FastAPI()

    @app.get("/cache")
    def get_cache():
        return cache.get_all()

    # Graceful shutdown
    def shutdown(sig, frame):
        logger.info("Shutdown signal received")
        mqtt_client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # 🚀 Run API server
    uvicorn.run(app, host="0.0.0.0", port=8000,log_config=None, access_log=False)

if __name__ == "__main__":
    main()