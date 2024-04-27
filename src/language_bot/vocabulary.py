import datetime
import logging
import langcodes
from pydantic import BaseModel
from uuid import UUID
from psycopg2.extensions import cursor
from typing import List, Tuple, Dict

from .chatbots.chatbot_service_interface import ChatbotSession


logger = logging.getLogger(__name__)


class VocabularyWord(BaseModel):
    word: str
    language: str
    category: str | None
    user_id: UUID
    learning_score: int
    last_check: datetime.datetime

    def save(self, cur: cursor):
        cur.execute(
            'INSERT INTO public.words (word, language, category) '
            'VALUES(%s, %s, %s)'
            'ON CONFLICT DO NOTHING;',
            (self.word, self.language, self.category)
        )

        cur.execute(
            "INSERT INTO public.vocabulary (word, language, user_id, learning_score, last_check) "
            "VALUES (%s, %s, %s, %s, (now() at time zone 'utc')) "
            "ON CONFLICT (user_id, language, word) "
            "DO UPDATE SET learning_score=excluded.learning_score, last_check=excluded.last_check;",
            (self.word, self.language, self.user_id, self.learning_score, )
        )


class Vocabulary(BaseModel):
    user_id: UUID
    language: str
    word_count: int

    def get_unique_words(self, new_words: List[str], cur: cursor) -> Dict[str, VocabularyWord]:
        cur.execute(
            "SELECT nw FROM "
            "unnest(%s) AS nw "
            "LEFT JOIN public.vocabulary AS v "
            "ON nw = v.word AND v.language = %s AND v.user_id = %s "
            "WHERE v.word IS NULL;",
            (new_words, self.language, self.user_id)
        )

        return {
            entry[0]: VocabularyWord(
                word=entry[0],
                language=self.language,
                category=None,
                user_id=self.user_id,
                learning_score=0,
                last_check=datetime.datetime.now()
            ) for entry in cur
        }

    def get_words(self, offset: int, limit: int, cur: cursor) -> List[VocabularyWord]:
        cur.execute(
            'SELECT v.word, v.language, w.category, v.user_id, v.learning_score, v.last_check '
            'FROM public.vocabulary AS v '
            'INNER JOIN public.words AS w '
            'ON v.word = w.word AND v.language = w.language '
            'WHERE v.user_id = %s AND v.language = %s '
            'ORDER BY v.learning_score, v.last_check OFFSET %s LIMIT %s;',
            (self.user_id, self.language, offset, limit,)
        )

        return [
            VocabularyWord(
                word=entry[0], language=entry[1], category=entry[2],
                user_id=entry[3], learning_score=entry[4], last_check=entry[5]
            ) for entry in cur
        ]


def get_user_vocabularies(
        user_id: UUID,
        cur: cursor
) -> Dict[str, Vocabulary]:
    cur.execute(
        'SELECT language, COUNT(word) '
        'FROM public.vocabulary '
        'WHERE user_id = %s '
        'GROUP BY language;',
        (user_id,)
    )

    return {
        entry[0]: Vocabulary(
            user_id=user_id,
            language=entry[0],
            word_count=entry[1],
        ) for entry in cur
    }


def get_user_vocabulary(
        user_id: UUID,
        language: str,
        cur: cursor
) -> Vocabulary:
    cur.execute(
        'SELECT COUNT(word) '
        'FROM public.vocabulary AS v '
        'WHERE v.user_id = %s AND v.language = %s;',
        (user_id, language,)
    )

    return Vocabulary(user_id=user_id, language=language, word_count=cur.fetchone()[0])
