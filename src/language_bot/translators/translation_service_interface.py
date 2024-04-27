from typing import List, Tuple
from pydantic import BaseModel, RootModel


class TranslationResult(BaseModel):
    source_text: str
    source_language: str
    target_text: str
    target_language: str
    translation_id: str


class DetectedLanguage(BaseModel):
    language: str
    confidence: int


class DetectedLanguages(RootModel):
    root: List[DetectedLanguage]


class TranslatorInterface:
    def type(self) -> str:
        raise RuntimeError("TranslationServiceInterface.type")

    def detect_language(self, source_text: str) -> DetectedLanguages:
        raise RuntimeError("TranslationServiceInterface.detect_language")

    def translate(self, source_text: str, source_language: str | None, target_language: str) -> Tuple[str, str]:
        """
        :param source_text:
        :param source_language:
        :param target_language:
        :return: translated text and source language
        """
        raise RuntimeError("TranslationServiceInterface.translate")

    def get_supported_pairs(self) -> List[Tuple[str, str]]:
        raise RuntimeError("TranslationServiceInterface.get_supported_pairs")


class TranslationServiceInterface:
    def type(self) -> str:
        raise RuntimeError("TranslationServiceInterface.type")

    def detect_language(self, source_text: str) -> DetectedLanguages:
        raise RuntimeError("TranslationServiceInterface.detect_language")

    def translate(self, source_text: str, source_language: str | None, target_language: str) -> TranslationResult:
        raise RuntimeError("TranslationServiceInterface.translate")

    def get_supported_target_languages(self) -> List[str]:
        raise RuntimeError("TranslationServiceInterface.get_supported_target_languages")

    def get_supported_pairs(self) -> List[Tuple[str, str]]:
        raise RuntimeError("TranslationServiceInterface.get_supported_pairs")

    def get_translation_by_id(self, translation_id: str) -> TranslationResult | None:
        raise RuntimeError("TranslationServiceInterface.get_translation_by_id")
