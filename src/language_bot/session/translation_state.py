from dataclasses import dataclass
import telegram
import langcodes
import logging

from .session_state import SessionState, UnprocessedEvent
from ..service_context import ServiceContext
from ..translators.translation_service_interface import TranslationResult
from .add_words_to_vocabulary_state import AddWordsToVocabularyState
from .select_language_state import SelectLanguageState


logger = logging.getLogger(__name__)


@dataclass
class TranslationState(SessionState):
    translation: TranslationResult

    def create_translation_result_params(
            self, service_context: ServiceContext
    ):
        return {
            "text": service_context.translation_service.translate(
                source_text=f"(Translated from {langcodes.get(self.translation.source_language).language_name()})",
                source_language="en",
                target_language=self.translation.target_language,
            ).target_text + " : " + self.translation.target_text,
            "reply_markup": telegram.InlineKeyboardMarkup([
                [telegram.InlineKeyboardButton(
                    text=service_context.translation_service.translate(
                        source_text="Add words to your vocabulary",
                        source_language="en",
                        target_language=self.translation.target_language,
                    ).target_text,
                    callback_data=f"add2vocab",
                )],
                [telegram.InlineKeyboardButton(
                    text=service_context.translation_service.translate(
                        source_text=f"This is not {langcodes.get(self.translation.source_language).language_name()}",
                        source_language="en",
                        target_language=self.translation.target_language,
                    ).target_text,
                    callback_data=f"change_lang",
                )]
            ])
        }

    async def show(self, service_context: ServiceContext) -> SessionState:
        if service_context.update.message:
            await service_context.update.message.reply_markdown(
                **self.create_translation_result_params(service_context)
            )
        elif service_context.update.callback_query:
            await service_context.update.callback_query.edit_message_text(
                **self.create_translation_result_params(service_context)
            )
        else:
            logger.warning("both message and callback_query are empty")

        return self

    async def on_back(self, service_context: ServiceContext):
        await service_context.update.callback_query.edit_message_text(
            **self.create_translation_result_params(service_context)
        )
        return self

    async def change_language(self, language: langcodes.Language, service_context: ServiceContext) -> SessionState:
        self.translation = service_context.translation_service.translate(
            source_text=self.translation.source_text,
            source_language=language.language,
            target_language=self.session_context.user.language.language
        )
        return await self.show(service_context)

    async def callback_query_handler(self, service_context: ServiceContext) -> "SessionState" or None:
        match service_context.update.callback_query.data:
            case "change_lang":
                return await SelectLanguageState.create(
                    user_language=self.session_context.user.language,
                    session_context=self.session_context,
                    service_context=service_context,
                    on_back=self.show,
                    on_complete=self.change_language,
                )

            case "add2vocab":
                return await AddWordsToVocabularyState.create(
                    session_context=self.session_context,
                    translation=self.translation,
                    service_context=service_context,
                    on_back=self.on_back,
                )

        raise UnprocessedEvent()
