from pydantic import BaseModel, AnyUrl
from typing import Literal, List
import os


class TranslationServiceConfig(BaseModel):
    type: Literal["libretranslate"]
    url: AnyUrl


class Config(BaseModel):
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = "INFO"
    TRANSLATION_SERVICES: List[TranslationServiceConfig]
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_USERNAME: str
    REDIS_PASSWORD: str
    TG_API_KEY: str


def init_config(config_filename: str) -> Config:
    with open(config_filename, 'r') as config_file:
        return Config.model_validate_json(config_file.read())
