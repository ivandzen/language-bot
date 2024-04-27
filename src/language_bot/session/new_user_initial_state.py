import telegram
import langcodes
from typing import Optional
from dataclasses import dataclass
import logging

from .session_state import SessionState
from ..service_context import ServiceContext
from .select_user_name_state import SelectUserNameState
from .select_language_state import SelectLanguageState
from ..user import create_user
from .user_menu_state import UserMenuState


logger = logging.getLogger(__name__)


async def create_menu_params(service_context: ServiceContext, user_language: langcodes.Language):
    return {
        "text": service_context.translation_service.translate(
            source_text=(f"Hello, @{service_context.update.effective_user.username}! "
                         "Please, finish registration procedure to use this bot. "
                         f"I see you are speaking {user_language.language_name()}. "
                         f"{user_language.language_name()} language will be used in explanations and translations. "
                         "Do you want to keep it as your default language or change it?"),
            source_language="en",
            target_language=user_language.language,
        ).target_text,
        "reply_markup": telegram.InlineKeyboardMarkup([[
            telegram.InlineKeyboardButton(
                text=service_context.translation_service.translate(
                    source_text=f"{user_language.language_name()}",
                    source_language="en",
                    target_language=user_language.language,
                ).target_text + " 👌",
                callback_data="keep_language"
            ),
            telegram.InlineKeyboardButton(
                text=service_context.translation_service.translate(
                    source_text=f"Other language",
                    source_language="en",
                    target_language=user_language.language,
                ).target_text + " 🙅‍♂️️",
                callback_data="other_language"
            )
        ]])
    }


@dataclass
class NewUserInitialState(SessionState):
    user_language: Optional[langcodes.Language] = None

    async def show(self, service_context: ServiceContext) -> "SessionState" or None:
        self.user_language = langcodes.get(service_context.update.effective_user.language_code)
        supported_languages = service_context.translation_service.get_supported_target_languages()
        if self.user_language.language in supported_languages:
            await service_context.update.message.reply_markdown(
                **await create_menu_params(service_context, self.user_language)
            )

            return self
        else:
            await service_context.update.message.reply_text(
                text=(f"Hello, @{service_context.update.effective_user.username}! "
                      f"I see you are speaking {self.user_language.language_name()}. "
                      "But unfortunately, I do not support it currently. "
                      "Please, choose the language from the list of available ones. "
                      "It will be used in explanations and translations:")
            )

        return self

    async def start_command_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        self.user_language = langcodes.get(service_context.update.effective_user.language_code)
        supported_languages = service_context.translation_service.get_supported_target_languages()
        if self.user_language.language in supported_languages:
            await service_context.update.message.reply_markdown(
                **await create_menu_params(service_context, self.user_language)
            )

            return self
        else:
            await service_context.update.message.reply_text(
                text=(f"Hello, @{service_context.update.effective_user.username}! "
                      f"I see you are speaking {self.user_language.language_name()}. "
                      "But unfortunately, I do not support it currently. "
                      "Please, choose the language from the list of available ones. "
                      "It will be used in explanations and translations:")
            )

        return self

    async def menu_command_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        await service_context.update.message.reply_text(
            text=service_context.translation_service.translate(
                source_text=f"Please, finish registration procedure to use this bot.",
                source_language="en",
                target_language="en" if self.user_language is None else self.user_language.language
            ).target_text
        )

        return self

    async def create_user(
            self,
            user_language: langcodes.Language,
            username: str,
            service_context: ServiceContext
    ):
        user = create_user(name=username, language=user_language, cur=service_context.cur)
        self.session_context.external_user.set_user(user.user_id, service_context.cur)
        self.session_context.user = user
        new_state = UserMenuState(session_context=self.session_context)
        return await new_state.show(
            text=f"Nice to meet you, {username}! "
            f"Now we are ready for journey into the diverse world of languages."
            f"Just send here any text and I will translate it into "
            f"{user_language.language_name()}."
            "But what is more exciting - I can help you to improve "
            "your vocabulary with periodic tests and advices."
            "Take a look at the menu below to see all possible commands.",
            service_context=service_context
        )

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        if self.user_language is None:
            return self.start_command_handler(service_context)

        match service_context.update.callback_query.data:
            case "keep_language":
                async def on_select_name_back(service_context2: ServiceContext) -> SessionState:
                    await service_context2.update.callback_query.edit_message_text(
                        **await create_menu_params(service_context, self.user_language)
                    )
                    return self

                async def on_select_name_complete(
                        username: str, service_context2: ServiceContext
                ) -> SessionState | None:
                    return await self.create_user(
                        user_language=self.user_language,
                        username=username,
                        service_context=service_context2
                    )

                return await SelectUserNameState.create(
                    session_context=self.session_context,
                    user_language=self.user_language,
                    service_context=service_context,
                    on_back=on_select_name_back,
                    on_complete=on_select_name_complete,
                )

            case "other_language":
                async def on_back(service_context2: ServiceContext) -> SessionState:
                    await service_context2.update.callback_query.edit_message_text(
                        **await create_menu_params(service_context2, self.user_language)
                    )
                    return self

                async def on_complete(
                        selected_language: langcodes.Language,
                        service_context2: ServiceContext,
                ) -> SessionState:
                    async def on_select_name_back(service_context3: ServiceContext) -> SessionState:
                        return await SelectLanguageState.create(
                            session_context=self.session_context,
                            user_language=self.user_language,
                            service_context=service_context3,
                            on_back=on_back,
                            on_complete=on_complete,
                        )

                    async def on_select_name_complete(
                            username: str, service_context2: ServiceContext
                    ) -> SessionState | None:
                        return await self.create_user(
                            user_language=selected_language,
                            username=username,
                            service_context=service_context2
                        )

                    return await SelectUserNameState.create(
                        session_context=self.session_context,
                        user_language=selected_language,
                        service_context=service_context2,
                        on_back=on_select_name_back,
                        on_complete=on_select_name_complete,
                    )

                return await SelectLanguageState.create(
                    user_language=self.user_language,
                    session_context=self.session_context,
                    service_context=service_context,
                    on_back=on_back,
                    on_complete=on_complete,
                )

        return self
