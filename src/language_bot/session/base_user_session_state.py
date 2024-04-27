import logging
from dataclasses import dataclass
import re
import langcodes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

from .session_state import SessionState, UnprocessedEvent
from ..service_context import ServiceContext
from .translation_state import TranslationState


SELECT_LANGUAGE_COMMAND_RE = re.compile("^([a-z]{2})_translate$")


@dataclass
class BaseUserSessionState(SessionState):
    text: Optional[str] = None

    async def message_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        if service_context.update.callback_query:
            await service_context.update.callback_query.delete_message()

        self.text = service_context.update.message.text
        detected_languages = service_context.translation_service.detect_language(
            source_text=service_context.update.message.text
        )

        if len(detected_languages.root) == 1:
            translation = service_context.translation_service.translate(
                source_text=service_context.update.message.text,
                source_language=detected_languages.root[0].language,
                target_language=self.session_context.user.language.language,
            )

            new_state = TranslationState(session_context=self.session_context, translation=translation)
            await new_state.show(service_context)
            return new_state

        buttons = []
        for detected_lang in detected_languages.root:
            buttons.append([InlineKeyboardButton(
                text=service_context.translation_service.translate(
                    source_text=langcodes.get(detected_lang.language).language_name(),
                    source_language="en",
                    target_language=self.session_context.user.language.language,
                ).target_text + f" - {detected_lang.confidence}%",
                callback_data=f"{detected_lang.language}_translate",
            )])

        await service_context.update.message.reply_text(
            text=service_context.translation_service.translate(
                source_text="I've found several possible languages to which this text may belong. "
                            "Please select the correct one. If you didn't find the right language, "
                            "then I can't translate this text for you, sorry. 😓",
                source_language="en",
                target_language=self.session_context.user.language.language,
            ).target_text,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return self

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        select_language_match = SELECT_LANGUAGE_COMMAND_RE.match(service_context.update.callback_query.data)
        if select_language_match:
            translation = service_context.translation_service.translate(
                source_text=self.text,
                source_language=select_language_match[1],
                target_language=self.session_context.user.language.language,
            )

            new_state = TranslationState(session_context=self.session_context, translation=translation)
            await new_state.show(service_context)
            return new_state

        raise UnprocessedEvent()
