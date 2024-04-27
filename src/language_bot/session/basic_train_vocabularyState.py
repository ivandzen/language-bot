from dataclasses import dataclass
from typing import Callable, Coroutine, Any
from telegram import InlineKeyboardMarkup

from ..vocabulary import Vocabulary
from .session_state import SessionState, back_button
from ..service_context import ServiceContext


@dataclass
class BasicTrainVocabularyState(SessionState):
    vocabulary: Vocabulary
    on_back: Callable[[ServiceContext], Coroutine[Any, Any, SessionState]]

    async def show(
            self,
            service_context: ServiceContext,
    ) -> SessionState:
        await service_context.update.callback_query.edit_message_text(
            text=service_context.translation_service.translate(
                source_text="Training mode is in process of implementation. "
                            "I'll let you know when ready",
                source_language="en",
                target_language=self.session_context.user.language.language,
            ).target_text,
            reply_markup=InlineKeyboardMarkup([
                [back_button(
                    service_context=service_context,
                    language=self.session_context.user.language.language,
                    action_name="back"
                )]
            ])
        )
        return self

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        match service_context.update.callback_query.data:
            case "back":
                return await self.on_back(service_context)
