from collections.abc import Sequence
from typing import Protocol, cast

from openai import OpenAI

from gigavibe.config import AppConfig
from gigavibe.context import Message
from gigavibe.errors import LLMError

ChatMessage = dict[str, str]
InputMessage = Message | ChatMessage


class ChatCompletionsResource(Protocol):
    def create(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float,
    ) -> object: ...


class ChatResource(Protocol):
    completions: ChatCompletionsResource


class OpenAICompatibleClient(Protocol):
    chat: ChatResource


class OpenAICompatibleLLM:
    def __init__(self, config: AppConfig, client: OpenAICompatibleClient | None = None) -> None:
        self._config = config
        if client is None:
            client = cast(
                OpenAICompatibleClient,
                OpenAI(api_key=config.api_key, base_url=config.api_host),
            )
        self._client = client

    def complete(self, messages: Sequence[InputMessage]) -> str:
        prepared_messages = [_message_to_dict(message) for message in messages]

        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=prepared_messages,
                temperature=self._config.temperature,
            )
        except Exception as error:
            raise LLMError('model request failed') from error

        return _extract_response_text(response)


def _message_to_dict(message: InputMessage) -> ChatMessage:
    if isinstance(message, Message):
        return message.to_dict()
    return dict(message)


def _extract_response_text(response: object) -> str:
    choices = getattr(response, 'choices', None)
    if not isinstance(choices, list) or not choices:
        raise LLMError('empty response from model')

    first_choice = choices[0]
    message = getattr(first_choice, 'message', None)
    content = getattr(message, 'content', None)
    if not isinstance(content, str) or not content:
        raise LLMError('empty response from model')

    return content
