import logging
import requests
from typing import List, Tuple, Dict
from pydantic import AnyUrl, RootModel, BaseModel

from .translation_service_interface import TranslatorInterface, DetectedLanguages


logger = logging.getLogger(__name__)


class SupportedLanguages(BaseModel):
    code: str
    targets: List[str]


class SupportedLanguagesResponse(RootModel):
    root: List[SupportedLanguages]


class Libretranslate(TranslatorInterface):
    def __init__(self, url: AnyUrl):
        logger.info(f"Initializing LibreTranslate at {url}")
        self.session = requests.Session()
        self.url = str(url)
        response = self.session.get(url=f"{self.url}/languages")
        if response.status_code != 200:
            raise RuntimeError(f"Unable to get supported language pairs: {response.content}")

        self.languages = SupportedLanguagesResponse.model_validate(response.json())

    def type(self) -> str:
        return "libretranslate"

    def detect_language(self, source_text: str) -> DetectedLanguages:
        response = self.session.post(
            url=f"{self.url}/detect",
            data={"q": source_text}
        )

        if response.status_code != 200:
            raise RuntimeError(f"Unable to determine language: {response.content}")

        return DetectedLanguages.model_validate(response.json())

    def translate(
            self,
            source_text: str,
            source_language: str,
            target_language: str
    ) -> Tuple[str, str]:
        response = self.session.post(
            url=f"{self.url}/translate",
            data={"q": source_text, "source": source_language, "target": target_language}
        )

        if response.status_code != 200:
            raise RuntimeError(f"Unable to determine language: {response.content}")

        return response.json()["translatedText"], source_language

    def get_supported_pairs(self) -> List[Tuple[str, str]]:
        result = []
        for source_language in self.languages.root:
            for target_language in source_language.targets:
                result.append((source_language.code, target_language,))

        return result
