import telegram
import langcodes
from dataclasses import dataclass
from typing import Callable, Coroutine, Any

from .session_state import SessionState, back_button
from ..service_context import ServiceContext
from ..user import User
from .select_language_state import SelectLanguageState
from .select_user_name_state import SelectUserNameState


async def settings_params(service_context: ServiceContext, user: User):
    return {
        "text": service_context.translation_service.translate(
            source_text=f"Settings of your account",
            source_language="en",
            target_language=user.language.language,
        ).target_text,
        "reply_markup": telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton(
                text=service_context.translation_service.translate(
                    source_text=f"Default language ({langcodes.get(user.language).language_name()})",
                    source_language="en",
                    target_language=user.language.language
                ).target_text,
                callback_data="change_user_language"
            )],
            [telegram.InlineKeyboardButton(
                text=service_context.translation_service.translate(
                    source_text=f"Name",
                    source_language="en",
                    target_language=user.language.language
                ).target_text + f" - {user.name}",
                callback_data="change_user_name"
            )],
            [back_button(
                service_context=service_context,
                language=user.language.language,
                action_name="settings_back"
            )]
        ]),
    }


@dataclass
class UserSettingsState(SessionState):
    on_return: Callable[[str | None, ServiceContext], Coroutine[Any, Any, SessionState]]

    async def show(self, service_context: ServiceContext):
        await service_context.update.callback_query.edit_message_text(
            **await settings_params(service_context, self.session_context.user)
        )

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        match service_context.update.callback_query.data:
            case "change_user_language":
                async def on_back(service_context2: ServiceContext) -> SessionState:
                    await service_context2.update.callback_query.edit_message_text(
                        **await settings_params(service_context2, self.session_context.user)
                    )
                    return self

                async def on_complete(
                        selected_language: langcodes.Language,
                        service_context2: ServiceContext,
                ) -> SessionState:
                    self.session_context.user.set_language(selected_language, service_context2.cur)
                    return await self.on_return(
                        f"{self.session_context.user.name}, now I will speak to You in {selected_language.language_name()}."
                        f"What will we do next?",
                        service_context2
                    )

                return await SelectLanguageState.create(
                    session_context=self.session_context,
                    user_language=self.session_context.user.language,
                    service_context=service_context,
                    on_back=on_back,
                    on_complete=on_complete
                )

            case "change_user_name":
                async def on_back(service_context2: ServiceContext) -> SessionState:
                    await service_context2.update.callback_query.edit_message_text(
                        **await settings_params(service_context2, self.session_context.user)
                    )
                    return self

                async def on_complete(
                        user_name: str,
                        service_context2: ServiceContext,
                ) -> SessionState:
                    self.session_context.user.set_name(user_name, service_context2.cur)
                    return await self.on_return(
                        f"Good, {self.session_context.user.name}. What will we do next?",
                        service_context2
                    )

                return await SelectUserNameState.create(
                    session_context=self.session_context,
                    user_language=self.session_context.user.language,
                    service_context=service_context,
                    on_back=on_back,
                    on_complete=on_complete,
                )

            case "settings_back":
                return await self.on_return(None, service_context)

            case _:
                return await super().callback_query_handler(service_context)
