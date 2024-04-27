
class ChatbotSession:
    def prompt(self, request: str) -> str:
        raise RuntimeError("ChatbotSession.prompt")


class ChatbotServiceInterface:
    def start_session(self, system_prompt: str | None) -> ChatbotSession:
        raise RuntimeError("ChatbotServiceInterface.start_session")
