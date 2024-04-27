from dataclasses import dataclass
from typing import Optional

from ..external_user import ExternalUser
from ..user import User
from ..chatbots.chatbot_service_interface import ChatbotSession


@dataclass
class SessionContext:
    chatbot_session: ChatbotSession
    external_user: ExternalUser
    user: Optional[User]
