import logging
from dataclasses import dataclass
from typing import Dict, Optional
from psycopg2.extensions import cursor

from ..user import User, get_user
from ..external_user import get_external_user, create_external_user
from ..service_context import ServiceContext
from .session_state import SessionState, UnprocessedEvent
from .new_user_initial_state import NewUserInitialState
from .user_menu_state import UserMenuState
from .session_context import SessionContext
from .base_user_session_state import BaseUserSessionState
from ..chatbots.chatbot_service_interface import ChatbotServiceInterface


logger = logging.getLogger(__name__)


@dataclass
class Session:
    session_context: SessionContext
    session_state: Optional[SessionState]

    async def start_command_handler(
            self,
            service_context: ServiceContext,
    ):
        if not self.session_context.user:
            new_state = NewUserInitialState(session_context=self.session_context)
            self.session_state = await new_state.show(service_context)
        else:
            new_state = UserMenuState(session_context=self.session_context)
            self.session_state = await new_state.show(None, service_context)

    async def menu_command_handler(
            self,
            service_context: ServiceContext,
    ):
        if not self.session_context.user:
            new_state = NewUserInitialState(session_context=self.session_context)
            self.session_state = await new_state.show(service_context)
        else:
            new_state = UserMenuState(session_context=self.session_context)
            self.session_state = await new_state.show(None, service_context)

    async def callback_query_handler(
            self,
            service_context: ServiceContext,
    ):
        if not self.session_state:
            if not self.session_context.user:
                new_state = NewUserInitialState(session_context=self.session_context)
                self.session_state = await new_state.show(service_context)
                return
            else:
                new_state = UserMenuState(session_context=self.session_context)
                self.session_state = await new_state.show(None, service_context)
                return

        try:
            self.session_state = await self.session_state.callback_query_handler(service_context)
        except UnprocessedEvent as e:
            new_state = UserMenuState(session_context=self.session_context)
            self.session_state = await new_state.show(None, service_context)
            return

    async def message_handler(
            self,
            service_context: ServiceContext,
    ) -> None:
        if not self.session_state:
            if not self.session_context.user:
                new_state = NewUserInitialState(session_context=self.session_context)
                self.session_state = await new_state.show(service_context)
                return
            else:
                self.session_state = BaseUserSessionState(session_context=self.session_context)

        try:
            self.session_state = await self.session_state.message_handler(service_context)
        except UnprocessedEvent as e:
            self.session_state = BaseUserSessionState(session_context=self.session_context)
            self.session_state = await self.session_state.message_handler(service_context)


SESSIONS: Dict[str, Session] = {}


def get_session(
        platform: str,
        platform_user_id: str,
        chatbot_service: ChatbotServiceInterface,
        cur: cursor
) -> Session:
    external_user = get_external_user(platform, platform_user_id, cur)
    if not external_user:
        external_user = create_external_user(platform, platform_user_id, None, None, cur)
        session = Session(
            session_context=SessionContext(
                chatbot_session=chatbot_service.start_session(''),
                external_user=external_user,
                user=None
            ),
            session_state=None
        )
    else:
        session = SESSIONS.get(external_user.get_user_ref(), None)
        if session:
            return session

        user = get_user(external_user.user_id, cur)
        session = Session(
            session_context=SessionContext(
                chatbot_session=chatbot_service.start_session(''),
                external_user=external_user,
                user=user
            ),
            session_state=None
        )

    SESSIONS[external_user.get_user_ref()] = session
    return session
