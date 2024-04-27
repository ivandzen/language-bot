import langcodes
import telegram
from dataclasses import dataclass

from .session_state import SessionState
from ..service_context import ServiceContext
from .user_settings_state import UserSettingsState
from .practice_state import PracticeState


def menu_buttons(service_context: ServiceContext, language: str) -> telegram.InlineKeyboardMarkup:
    return telegram.InlineKeyboardMarkup([
        [
            telegram.InlineKeyboardButton(
                text=service_context.translation_service.translate(
                    source_text=f"Settings",
                    source_language="en",
                    target_language=language,
                ).target_text + " ⚙️",
                callback_data="menu_settings"
            )
        ],
        [
            telegram.InlineKeyboardButton(
                text=service_context.translation_service.translate(
                    source_text=f"Practice",
                    source_language="en",
                    target_language=language,
                ).target_text + " 💪",
                callback_data="menu_practice"
            ),
        ]
    ])


async def menu_params(text: str | None, service_context: ServiceContext, language: langcodes.Language):
    return {
        "text": service_context.translation_service.translate(
            source_text=f"Select action or send me any text and I will translate it for You" if text is None else text,
            source_language="en",
            target_language=language.language,
        ).target_text,
        "reply_markup": menu_buttons(service_context, language.language),
    }


@dataclass
class UserMenuState(SessionState):
    async def show(self, text: str | None, service_context: ServiceContext) -> SessionState:
        params = await menu_params(text, service_context, self.session_context.user.language)
        if service_context.update.callback_query:
            await service_context.update.callback_query.edit_message_text(**params)
        elif service_context.update.message:
            await service_context.update.message.reply_markdown(**params)
        return self

    async def callback_query_handler(self, service_context: ServiceContext) -> "SessionState" or None:
        match service_context.update.callback_query.data:
            case "menu_settings":
                settings_state = UserSettingsState(session_context=self.session_context, on_return=self.show)
                await settings_state.show(service_context)
                return settings_state

            case "menu_practice":
                practice_state = PracticeState(session_context=self.session_context, on_return=self.show)
                await practice_state.show(service_context)
                return practice_state

            case _:
                return await super().callback_query_handler(service_context)
