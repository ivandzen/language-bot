import telegram
from dataclasses import dataclass

from ..service_context import ServiceContext
from .session_context import SessionContext


class UnprocessedEvent(RuntimeError):
    pass


@dataclass
class SessionState:
    session_context: SessionContext

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        raise UnprocessedEvent()

    async def message_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        raise UnprocessedEvent()


def back_button(
        service_context: ServiceContext,
        language: str,
        action_name: str
) -> telegram.InlineKeyboardButton:
    return telegram.InlineKeyboardButton(
        text=service_context.translation_service.translate(
            source_text=f"Back",
            source_language="en",
            target_language=language,
        ).target_text + " ⬅️",
        callback_data=action_name,
    )
