# config/settings.py

from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional


class LogConf(BaseModel):
    level: str = "INFO"
    on_console: bool = True
    is_json: bool = False
    max_age: int = 7
    max_size: int = 10  # MB


class MQTTConfig(BaseModel):
    host: str
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    keepalive: int = 60
    tls: bool = False
    
class DbConf(BaseModel):
    enable: bool = True
    name: str
    host: str
    port: int = 5432
    user: str
    password: str
    idle_connection: int = 5
    open_connection: int = 10


class NatsConf(BaseModel):
    enable: bool = False
    host: str = "localhost"
    port: int = 4222
    user: Optional[str] = None
    password: Optional[str] = None
    tls: bool = False

    def validate(self):
        if self.enable and not self.host:
            raise ValueError("NATS host required when enabled")


class AppConf(BaseModel):
    vendor_cloud_code: Optional[str] = None
    dl_topic: str = ""
    output_topic: str = ""
    ttl_seconds: int = 3


class Configuration(BaseSettings):
    app: AppConf
    log: LogConf
    db: DbConf
    mqtt: MQTTConfig
    nats: NatsConf 
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"