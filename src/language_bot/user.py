from uuid import UUID
from dataclasses import dataclass
import langcodes
from psycopg2.extensions import cursor


@dataclass
class User:
    user_id: UUID
    name: str
    language: langcodes.Language

    def set_language(self, language: langcodes.Language, cur: cursor):
        cur.execute(
            'UPDATE public.botuser SET language = %s WHERE user_id = %s;',
            (language.language, self.user_id,)
        )
        self.language = language

    def set_name(self, name: str, cur: cursor):
        cur.execute(
            'UPDATE public.botuser SET name = %s WHERE user_id = %s;',
            (name, self.user_id,)
        )
        self.name = name


def create_user(name: str, language: langcodes.Language, cur: cursor) -> User:
    cur.execute(
        'INSERT INTO public.botuser (name, language) VALUES (%s, %s) RETURNING user_id;',
        (name, language.language,)
    )

    entry = cur.fetchone()
    if not entry:
        raise RuntimeError(f"Failed to create new user")

    return User(
        user_id=entry[0],
        name=name,
        language=language
    )


def get_user(user_id: UUID, cur: cursor) -> User | None:
    cur.execute(
        'SELECT user_id, name, language FROM public.botuser WHERE user_id = %s;',
        (user_id,)
    )

    entry = cur.fetchone()
    if not entry:
        return None

    return User(user_id=entry[0], name=entry[1], language=langcodes.get(entry[2]))
