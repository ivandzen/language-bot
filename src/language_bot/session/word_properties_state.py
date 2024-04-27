from dataclasses import dataclass
from typing import Callable, Coroutine, Any
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from ..service_context import ServiceContext
from .session_state import SessionState, back_button
from ..vocabulary import VocabularyWord


@dataclass
class WordPropertiesState(SessionState):
    word: VocabularyWord
    on_back: Callable[[ServiceContext], Coroutine[Any, Any, SessionState]]
    on_store: Callable[[VocabularyWord, ServiceContext], Coroutine[Any, Any, SessionState]]

    async def show(self, service_context: ServiceContext):
        await service_context.update.callback_query.edit_message_text(
            text=self.word.word + " - " + service_context.translation_service.translate(
                source_text=f"{self.word.word}",
                source_language="en",
                target_language=self.session_context.user.language.language,
            ).target_text,
            reply_markup=InlineKeyboardMarkup([
                [back_button(
                    service_context=service_context,
                    language=self.session_context.user.language.language,
                    action_name="word_back",
                )],
                [InlineKeyboardButton(
                    text=service_context.translation_service.translate(
                        source_text=f"Remember",
                        source_language="en",
                        target_language=self.session_context.user.language.language,
                    ).target_text + " 🧠",
                    callback_data="word_store",
                )]
            ])
        )

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        match service_context.update.callback_query.data:
            case "word_back":
                return await self.on_back(service_context)
            case "word_store":
                return await self.on_store(self.word, service_context)
