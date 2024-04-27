from gpt4all import GPT4All
import logging

from .chatbot_service_interface import ChatbotSession, ChatbotServiceInterface


logger = logging.getLogger(__name__)


class GPT4AllSession(ChatbotSession):
    def __init__(self, model: GPT4All):
        self.model = model

    def prompt(self, request: str) -> str:
        with self.model.chat_session():
            return self.model.generate(prompt=request, temp=0)


class GPT4AllService(ChatbotServiceInterface):
    def __init__(self, model_name: str | None = None, device: str | None = None):
        self.model = GPT4All(
            "Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf" if not model_name else model_name,
            device='gpu' if not device else device,
            n_ctx=4096,
        )

    def start_session(self, system_prompt: str | None) -> ChatbotSession:
        return GPT4AllSession(self.model)
