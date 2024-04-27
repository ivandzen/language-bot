import datetime
from typing import List, Dict
import logging
import langcodes
import redis
import hashlib

from ..common.config import Config
from .translation_service_interface import (TranslatorInterface, TranslationServiceInterface,
                                            TranslationResult, DetectedLanguages)
from .libretranslate import Libretranslate


logger = logging.getLogger(__name__)
TRANSLATION_EXPIRATION_DAYS = 7


class TranslationServiceAggregator(TranslationServiceInterface):
    def __init__(self, config: Config):
        self.redis = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            username=config.REDIS_USERNAME,
            password=config.REDIS_PASSWORD,
        )

        # maps target_language -> source_language -> list of available translators
        self.translation_table: Dict[str, Dict[str, List[TranslatorInterface]]] = {}
        for translator_config in config.TRANSLATION_SERVICES:
            match translator_config.type:
                case "libretranslate":
                    libretranslate_instance = Libretranslate(url=translator_config.url)
                    for translation_pair in libretranslate_instance.get_supported_pairs():
                        source_language = translation_pair[0]
                        target_language = translation_pair[1]
                        (self.translation_table
                         .setdefault(target_language, {})
                         .setdefault(source_language, [])
                         .append(libretranslate_instance))

    def get_translation_by_id(self, translation_id: str) -> TranslationResult | None:
        cached_serialized = self.redis.get(translation_id)
        if cached_serialized is not None:
            try:
                translation = TranslationResult.model_validate_json(cached_serialized)
                # prolong lifetime of this translation
                self.redis.expire(translation_id, datetime.timedelta(days=TRANSLATION_EXPIRATION_DAYS))
                return translation
            except ValueError as _:
                logger.warning(f"Failed to deserialize cached translation. Will clear cache entry {translation_id}")
                self.redis.delete(translation_id)

        return None

    def detect_language(self, source_text: str) -> DetectedLanguages:
        available_translators: Dict[str, TranslatorInterface] = {}
        for _, source_languages in self.translation_table.items():
            for _, translators in source_languages.items():
                logger.info(translators)
                for translator in translators:
                    available_translators.setdefault(translator.type(), translator)

        for _, translator in available_translators.items():
            return translator.detect_language(source_text=source_text)

        raise RuntimeError(f"Can not detect language")

    def translate(self, source_text: str, source_language: str, target_language: str) -> TranslationResult:
        hasher = hashlib.md5()
        hasher.update((source_text + source_language + target_language).encode('utf-8'))
        translation_id = hasher.hexdigest()
        translation = self.get_translation_by_id(translation_id)
        if translation:
            return translation

        source_languages = self.translation_table.get(target_language, None)
        if not source_languages:
            raise RuntimeError(f"Language {langcodes.get(target_language).language_name()} is not supported")

        available_translators = {}
        translators = source_languages.get(source_language, None)
        if not translators:
            raise RuntimeError(
                f"Translation {langcodes.get(source_language).language_name()} -> "
                f"{langcodes.get(target_language).language_name()} is not supported"
            )
        for translator in translators:
            available_translators.setdefault(translator.type(), translator)

        for _, translator in available_translators.items():
            target_text, source_language = translator.translate(source_text, source_language, target_language)
            result = TranslationResult(
                source_text=source_text,
                source_language=source_language,
                target_text=target_text,
                target_language=target_language,
                translation_id=translation_id,
            )
            self.redis.set(translation_id, result.model_dump_json())
            self.redis.expire(translation_id, datetime.timedelta(days=TRANSLATION_EXPIRATION_DAYS))
            return result

        raise RuntimeError("translate: Unexpected error")

    def get_supported_target_languages(self) -> List[str]:
        return list(self.translation_table.keys())


def init_translation_service(config: Config) -> TranslationServiceInterface:
    return TranslationServiceAggregator(config)
