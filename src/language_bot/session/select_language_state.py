import langcodes
import telegram
from typing import Callable, Coroutine, Any
from dataclasses import dataclass

from .session_state import SessionState, back_button
from ..service_context import ServiceContext
from .session_context import SessionContext


def create_language_buttons(
        target_language: str,
        service_context: ServiceContext,
) -> telegram.InlineKeyboardMarkup:
    items = []
    for language in sorted(service_context.translation_service.get_supported_target_languages()):
        items.append([telegram.InlineKeyboardButton(
            text=service_context.translation_service.translate(
                source_text=f"{langcodes.get(language).language_name()}",
                source_language="en",
                target_language=target_language,
            ).target_text,
            callback_data=f"{language}_language"
        )])

    items.append([
        back_button(
            service_context=service_context,
            language=target_language,
            action_name="back"
        )
    ])

    return telegram.InlineKeyboardMarkup(items)


@dataclass
class SelectLanguageState(SessionState):
    on_back: Callable[[ServiceContext], Coroutine[Any, Any, SessionState]]
    on_complete: Callable[[langcodes.Language, ServiceContext], Coroutine[Any, Any, SessionState]]

    @staticmethod
    async def create(
            user_language: langcodes.Language,
            session_context: SessionContext,
            service_context: ServiceContext,
            on_back: Callable[[ServiceContext], Coroutine[Any, Any, SessionState]],
            on_complete: Callable[[langcodes.Language, ServiceContext], Coroutine[Any, Any, SessionState]],
    ) -> "SelectLanguageState":
        await service_context.update.callback_query.edit_message_text(
            text=service_context.translation_service.translate(
                source_text=f"Select one of the languages which I know at the moment. "
                "I'm sorry if I still can not speak your native language. "
                "I'm learning hard everyday to be better language bot. ",
                source_language="en",
                target_language=user_language.language,
            ).target_text,
            reply_markup=create_language_buttons(
                user_language.language,
                service_context
            ),
        )

        return SelectLanguageState(
            session_context=session_context,
            on_back=on_back,
            on_complete=on_complete,
        )

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        if service_context.update.callback_query.data == "back":
            return await self.on_back(service_context)

        selected_language = service_context.update.callback_query.data
        if len(selected_language) == 11 and selected_language[2:] == "_language":
            return await self.on_complete(langcodes.get(selected_language[:2]), service_context)

        return self
