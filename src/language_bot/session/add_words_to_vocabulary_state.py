import logging
from dataclasses import dataclass
from typing import List, Dict, Callable, Coroutine, Any
import langcodes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from nltk.tokenize.nist import NISTTokenizer
import logging

from .word_properties_state import WordPropertiesState
from .session_state import SessionState, back_button
from ..vocabulary import get_user_vocabulary, Vocabulary, VocabularyWord
from ..translators.translation_service_interface import TranslationResult
from ..service_context import ServiceContext
from .session_context import SessionContext
from ..chatbots.chatbot_service_interface import ChatbotSession


logger = logging.getLogger(__name__)
tokenizer = NISTTokenizer()

NON_WESTERN_LANGS = ["ar", "bn", "fa", "he", "hi", "id", "ja", "ko", "ms", "th", "tl", "ur", "zh"]


def prepare_word_button_params(
        target_language: str,
        words: Dict[str, VocabularyWord],
        service_context: ServiceContext
) -> InlineKeyboardMarkup:
    word_buttons = [InlineKeyboardButton(
        text=word,
        callback_data=word
    ) for word in words.keys()]

    buttons = [[back_button(service_context=service_context, language=target_language, action_name="add_words_back")]]
    for i in range(0, len(word_buttons), 2):
        buttons.append(word_buttons[i:i + 2])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def determine_word_category(
        word: VocabularyWord,
        chatbot_session: ChatbotSession
) -> str:
    response = chatbot_session.prompt(
        f"Determine category of the {langcodes.get(word.language).language_name()} "
        f"word: {word.word}. Output answer as a single word"
    )

    return response


@dataclass
class AddWordsToVocabularyState(SessionState):
    translation: TranslationResult
    vocabulary: Vocabulary
    unique_words: Dict[str, VocabularyWord]
    on_back: Callable[[ServiceContext], Coroutine[Any, Any, SessionState]]

    @staticmethod
    async def create(
            session_context: SessionContext,
            translation: TranslationResult,
            service_context: ServiceContext,
            on_back: Callable[[ServiceContext], Coroutine[Any, Any, SessionState]],
    ) -> "AddWordsToVocabularyState":
        new_words = set()
        if translation.source_language in NON_WESTERN_LANGS:
            words = tokenizer.international_tokenize(text=translation.source_text)
        else:
            words = tokenizer.tokenize(text=translation.source_text)

        for word in words:
            if len(word) == 1:
                continue
            new_words.add(word.lower())

        vocabulary = get_user_vocabulary(
            user_id=session_context.user.user_id,
            language=translation.source_language,
            cur=service_context.cur,
        )

        unique_words = vocabulary.get_unique_words(new_words=list(new_words), cur=service_context.cur)
        await service_context.update.callback_query.edit_message_text(
            text=service_context.translation_service.translate(
                source_text=f"(Translated from {langcodes.get(translation.source_language).language_name()})",
                source_language="en",
                target_language=session_context.user.language.language,
            ).target_text + " : " + translation.target_text,
            reply_markup=prepare_word_button_params(
                target_language=session_context.user.language.language,
                words=unique_words,
                service_context=service_context,
            )
        )

        return AddWordsToVocabularyState(
            session_context=session_context,
            translation=translation,
            vocabulary=vocabulary,
            unique_words=unique_words,
            on_back=on_back,
        )

    async def show_menu(self, service_context: ServiceContext):
        await service_context.update.callback_query.edit_message_text(
            text=service_context.translation_service.translate(
                source_text=f"(Translated from {langcodes.get(self.translation.source_language).language_name()})",
                source_language="en",
                target_language=self.session_context.user.language.language,
            ).target_text + " : " + self.translation.target_text,
            reply_markup=prepare_word_button_params(
                target_language=self.session_context.user.language.language,
                words=self.unique_words,
                service_context=service_context,
            )
        )

    async def on_word_back(self, service_context: ServiceContext) -> SessionState:
        await self.show_menu(service_context)
        return self

    async def on_word_store(self, word: VocabularyWord, service_context: ServiceContext) -> SessionState:
        word.save(service_context.cur)
        del self.unique_words[word.word]
        await self.show_menu(service_context)
        return self

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ) -> "SessionState" or None:
        if service_context.update.callback_query.data == "add_words_back":
            return await self.on_back(service_context)

        word = self.unique_words.get(service_context.update.callback_query.data, None)
        if not word:
            logger.warning(f"Word {service_context.update.callback_query.data} not found")
            return self

        if word.category is None:
            word.category = determine_word_category(word, self.session_context.chatbot_session)

        new_state = WordPropertiesState(
            session_context=self.session_context,
            word=word,
            on_back=self.on_word_back,
            on_store=self.on_word_store,
        )
        await new_state.show(service_context=service_context)
        return new_state
