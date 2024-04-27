from dataclasses import dataclass
import telegram
import langcodes
from typing import Callable, Coroutine, Any, Optional, Dict

from .session_state import SessionState, back_button
from ..service_context import ServiceContext
from ..vocabulary import get_user_vocabularies, get_user_vocabulary, Vocabulary
from .vocabulary_state import VocabularyState


@dataclass
class PracticeState(SessionState):
    on_return: Callable[[str | None, ServiceContext], Coroutine[Any, Any, SessionState]]
    vocabularies: Optional[Dict[str, Vocabulary]] = None

    async def show(self, service_context: ServiceContext):
        self.vocabularies = get_user_vocabularies(self.session_context.user.user_id, service_context.cur)
        if len(self.vocabularies) == 0:
            await service_context.update.callback_query.edit_message_text(
                text=service_context.translation_service.translate(
                    source_text=f"{self.session_context.user.name}, You still don't have any vocabularies. "
                                f"Send text here to translate and I will suggest you new "
                                f"words for learning.",
                    source_language="en",
                    target_language=self.session_context.user.language.language,
                ).target_text,
                reply_markup=telegram.InlineKeyboardMarkup([[
                    back_button(
                        service_context=service_context,
                        language=self.session_context.user.language.language,
                        action_name="practice_back"
                    ),
                ]]),
            )
        else:
            items = [[
                back_button(
                    service_context=service_context,
                    language=self.session_context.user.language.language,
                    action_name="practice_back"
                ),
            ]]

            for _, vocabulary in self.vocabularies.items():
                items.append([telegram.InlineKeyboardButton(
                    text=service_context.translation_service.translate(
                        source_text=f"{langcodes.get(vocabulary.language).language_name()} "
                                    f"- ({vocabulary.word_count} words)",
                        source_language="en",
                        target_language=self.session_context.user.language.language,
                    ).target_text,
                    callback_data=f"{vocabulary.language}_vocab"
                )])

            await service_context.update.callback_query.edit_message_text(
                text=service_context.translation_service.translate(
                    source_text=f"{self.session_context.user.name}, select vocabulary to practice: ",
                    source_language="en",
                    target_language=self.session_context.user.language.language,
                ).target_text,
                reply_markup=telegram.InlineKeyboardMarkup(items),
            )

    async def on_back(self, service_context: ServiceContext) -> SessionState:
        await self.show(service_context)
        return self

    async def callback_query_handler(self, service_context: ServiceContext) -> "SessionState" or None:
        match service_context.update.callback_query.data:
            case "practice_back":
                return await self.on_return(None, service_context)
            case other:
                if len(other) == 8 and other[-6:] == "_vocab":
                    if not self.vocabularies:
                        raise RuntimeError(f"Vocabulary select event received but self.vocabularies is empty")

                    vocabulary = self.vocabularies.get(other[:2])
                    new_session = VocabularyState(
                        session_context=self.session_context,
                        vocabulary=vocabulary,
                        on_back=self.on_back,
                    )
                    await new_session.show(service_context)
                    return new_session

                else:
                    return await super().callback_query_handler(service_context)
