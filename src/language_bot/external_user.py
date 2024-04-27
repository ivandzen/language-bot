from pydantic import BaseModel
from uuid import UUID
from typing import Dict, Any, Optional
from psycopg2.extensions import cursor


class ExternalUser(BaseModel):
    platform: str
    platform_user_id: str
    user_id: Optional[UUID]
    additional_info: Optional[Dict[str, Any]] = None

    def get_user_ref(self) -> str:
        return f"{self.platform}/{self.platform_user_id}"

    def set_user(self, user_id: UUID, cur: cursor):
        cur.execute(
            'UPDATE public.external_user SET user_id = %s WHERE platform = %s AND platform_user_id = %s;',
            (user_id, self.platform, self.platform_user_id,)
        )
        self.user_id = user_id


EXTERNAL_USERS: Dict[str, ExternalUser] = {}


def create_external_user(
        platform: str,
        platform_user_id: str,
        user_id: UUID | None,
        additional_info: Dict[str, Any] | None,
        cur: cursor
) -> ExternalUser:
    cur.execute(
        'INSERT INTO public.external_user (platform, platform_user_id, user_id, additional_info) '
        'VALUES (%s, %s, %s, %s);',
        (platform, platform_user_id, user_id, additional_info)
    )

    external_user = ExternalUser(
        platform=platform,
        platform_user_id=platform_user_id,
        user_id=user_id,
        additional_into=None,
    )
    EXTERNAL_USERS[f"{platform}/{platform_user_id}"] = external_user
    return external_user


def get_external_user(platform: str, platform_user_id: str, cur: cursor) -> ExternalUser | None:
    external_user_ref = f"{platform}/{platform_user_id}"
    external_user = EXTERNAL_USERS.get(external_user_ref, None)
    if external_user:
        return external_user

    cur.execute(
        'SELECT platform, platform_user_id, user_id, additional_info '
        'FROM public.external_user '
        'WHERE platform = %s AND platform_user_id = %s;',
        (platform, platform_user_id,)
    )

    entry = cur.fetchone()
    if entry:
        return ExternalUser(
            platform=platform,
            platform_user_id=platform_user_id,
            user_id=entry[2],
            additional_info=entry[3],
        )

    return None


