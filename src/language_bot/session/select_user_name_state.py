import telegram
from dataclasses import dataclass
import langcodes
from typing import Callable, Coroutine, Any

from .session_state import SessionState, back_button
from ..service_context import ServiceContext
from .session_context import SessionContext


@dataclass
class SelectUserNameState(SessionState):
    user_language: langcodes.Language
    on_back: Callable[[ServiceContext], Coroutine[Any, Any, SessionState]]
    on_complete: Callable[[str, ServiceContext], Coroutine[Any, Any, SessionState]]

    @staticmethod
    async def create(
            session_context: SessionContext,
            user_language: langcodes.Language,
            service_context: ServiceContext,
            on_back: Callable[[ServiceContext], Coroutine[Any, Any, SessionState]],
            on_complete: Callable[[str, ServiceContext], Coroutine[Any, Any, SessionState]],
    ) -> "SelectUserNameState":
        await service_context.update.callback_query.edit_message_text(
            text=service_context.translation_service.translate(
                source_text=f"@{service_context.update.effective_user.username} please, "
                f"send message here, how should I address You? "
                "Note: this name shouldn't be longer than 30 symbols.",
                source_language="en",
                target_language=user_language.language,
            ).target_text,
            reply_markup=telegram.InlineKeyboardMarkup([[back_button(
                service_context=service_context,
                language=user_language.language,
                action_name="back"
            )]]),
        )

        return SelectUserNameState(
            session_context=session_context,
            user_language=user_language,
            on_back=on_back,
            on_complete=on_complete,
        )

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        if service_context.update.callback_query.data == "back":
            return await self.on_back(service_context)

    async def message_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        username = service_context.update.message.text
        if len(username) > 30:
            await service_context.update.message.reply_text(
                text=service_context.translation_service.translate(
                    source_text=f"This is name is too long. Name should be shorter than 30 symbols. Try again please.",
                    source_language="en",
                    target_language=self.user_language.language,
                ).target_text,
            )

            return self

        return await self.on_complete(username, service_context)
