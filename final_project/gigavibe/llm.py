from collections.abc import Iterator
from typing import Iterable, Protocol, Sequence, cast

from openai import OpenAI

from gigavibe.config import AppConfig
from gigavibe.context import Message
from gigavibe.errors import LLMError

ChatMessage = dict[str, str]
InputMessage = Message | ChatMessage


class LLMProtocol(Protocol):
    def complete(self, messages: Sequence[InputMessage]) -> str: ...

    def stream_complete(self, messages: Sequence[InputMessage]) -> Iterable[str]: ...


class ChatCompletionsResource(Protocol):
    def create(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        temperature: float,
        stream: bool = False,
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
                cast(object, OpenAI(api_key=config.api_key, base_url=config.api_host)),
            )
        self._client = client

    def complete(self, messages: Sequence[InputMessage]) -> str:
        prepared_messages = [_message_to_dict(message) for message in messages]

        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                messages=prepared_messages,
                temperature=self._config.temperature,
                stream=False,
            )
        except Exception as error:
            raise LLMError('model request failed') from error

        return _extract_response_text(response)

    def stream_complete(self, messages: Sequence[InputMessage]) -> Iterator[str]:
        prepared_messages = [_message_to_dict(message) for message in messages]

        try:
            stream = cast(
                Iterable[object],
                self._client.chat.completions.create(
                    model=self._config.model,
                    messages=prepared_messages,
                    temperature=self._config.temperature,
                    stream=True,
                ),
            )
            for chunk in stream:
                text_part = _extract_stream_text_part(chunk)
                if text_part:
                    yield text_part
        except Exception as error:
            raise LLMError(f'streaming model request failed: {error}') from error


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


def _extract_stream_text_part(chunk: object) -> str:
    choices = getattr(chunk, 'choices', None)
    if not isinstance(choices, list) or not choices:
        return ''

    first_choice = choices[0]
    delta = getattr(first_choice, 'delta', None)
    content = getattr(delta, 'content', None)
    if not isinstance(content, str):
        return ''

    return content
