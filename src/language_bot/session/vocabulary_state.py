from dataclasses import dataclass, field
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Callable, Coroutine, Any

from .session_state import SessionState, back_button, UnprocessedEvent
from ..vocabulary import Vocabulary
from ..service_context import ServiceContext
from .basic_train_vocabularyState import BasicTrainVocabularyState

WORDS_PER_PAGE = 30


@dataclass
class VocabularyState(SessionState):
    vocabulary: Vocabulary
    on_back: Callable[[ServiceContext], Coroutine[Any, Any, SessionState]]
    page: int = field(default=0)

    async def build_form(self, service_context: ServiceContext):
        header = service_context.translation_service.translate(
            source_text=f"Total {self.vocabulary.word_count} words",
            source_language="en",
            target_language=self.session_context.user.language.language,
        ).target_text + ". " + service_context.translation_service.translate(
            source_text=f"Page {self.page + 1}",
            source_language="en",
            target_language=self.session_context.user.language.language,
        ).target_text

        navigation_buttons = []
        if self.page > 0:
            navigation_buttons.append(InlineKeyboardButton(
                text="◀️ " + service_context.translation_service.translate(
                    source_text=f"Previous page",
                    source_language="en",
                    target_language=self.session_context.user.language.language,
                ).target_text,
                callback_data="prev_page",
            ))

        if (self.page + 1) * WORDS_PER_PAGE < self.vocabulary.word_count:
            navigation_buttons.append(InlineKeyboardButton(
                text=service_context.translation_service.translate(
                    source_text=f"Next page",
                    source_language="en",
                    target_language=self.session_context.user.language.language,
                ).target_text + " ▶️",
                callback_data="next_page",
            ))

        buttons = [
            navigation_buttons,
            [
                InlineKeyboardButton(
                    text=service_context.translation_service.translate(
                        source_text=f"Start training",
                        source_language="en",
                        target_language=self.session_context.user.language.language,
                    ).target_text + " 💪",
                    callback_data="start_train",
                )
            ],
            #[
            #    InlineKeyboardButton(
            #        text=service_context.translation_service.translate(
            #            source_text=f"Edit words",
            #            source_language="en",
            #            target_language=self.session_context.user.language.language,
            #        ).target_text + " 📝",
            #        callback_data="edit",
            #    )
            #],
            [back_button(
                service_context=service_context,
                language=self.session_context.user.language.language,
                action_name="back",
            )]
        ]

        words = self.vocabulary.get_words(
            offset=self.page * WORDS_PER_PAGE,
            limit=WORDS_PER_PAGE,
            cur=service_context.cur
        )

        await service_context.update.callback_query.edit_message_text(
            text=header + "\n\n" + "\n".join([
                f"{word.word} - "
                f"""{service_context.translation_service.translate(
                    source_text=word.word,
                    source_language=word.language,
                    target_language=self.session_context.user.language.language
                ).target_text}""" for word in words
            ]),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def show(self, service_context: ServiceContext) -> SessionState:
        await self.build_form(service_context)
        return self

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        match service_context.update.callback_query.data:
            case "back":
                return await self.on_back(service_context)

            case "prev_page":
                self.page -= 1
                await self.build_form(service_context)
                return self

            case "next_page":
                self.page += 1
                await self.build_form(service_context)
                return self

            case "start_train":
                new_state = BasicTrainVocabularyState(
                    session_context=self.session_context,
                    vocabulary=self.vocabulary,
                    on_back=self.show,
                )
                return await new_state.show(service_context)

        raise UnprocessedEvent()
