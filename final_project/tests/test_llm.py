from dataclasses import dataclass

import pytest

from gigavibe.config import AppConfig
from gigavibe.context import Message
from gigavibe.errors import LLMError
from gigavibe.llm import ChatCompletionsResource, ChatResource, OpenAICompatibleLLM


@dataclass
class FakeResponseMessage:
    content: str | None


@dataclass
class FakeChoice:
    message: FakeResponseMessage


@dataclass
class FakeResponse:
    choices: list[FakeChoice]


@dataclass
class FakeStreamDelta:
    content: str | None = None


@dataclass
class FakeStreamChoice:
    delta: FakeStreamDelta


@dataclass
class FakeStreamChunk:
    choices: list[FakeStreamChoice]


class FakeCompletions:
    def __init__(self, response: object | Exception) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        stream: bool = False,
    ) -> object:
        self.calls.append(
            {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'stream': stream,
            },
        )
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeChat:
    def __init__(self, completions: FakeCompletions) -> None:
        self.completions: ChatCompletionsResource = completions


class FakeClient:
    def __init__(self, completions: FakeCompletions) -> None:
        self.chat: ChatResource = FakeChat(completions)


def make_config() -> AppConfig:
    return AppConfig(
        api_key='ollama',
        api_host='http://localhost:11434/v1/',
        model='gemma3',
        temperature=0.3,
    )


def test_complete_sends_model_temperature_and_messages() -> None:
    completions = FakeCompletions(FakeResponse([FakeChoice(FakeResponseMessage('Hello'))]))
    llm = OpenAICompatibleLLM(make_config(), client=FakeClient(completions))

    result = llm.complete(
        [
            {'role': 'system', 'content': 'You are concise.'},
            Message(role='user', content='Hi'),
        ],
    )

    assert result == 'Hello'
    assert completions.calls == [
        {
            'model': 'gemma3',
            'messages': [
                {'role': 'system', 'content': 'You are concise.'},
                {'role': 'user', 'content': 'Hi'},
            ],
            'temperature': 0.3,
            'stream': False,
        },
    ]


@pytest.mark.parametrize(
    'response',
    [
        FakeResponse([]),
        FakeResponse([FakeChoice(FakeResponseMessage(None))]),
        FakeResponse([FakeChoice(FakeResponseMessage(''))]),
    ],
)
def test_complete_rejects_empty_or_malformed_response(response: FakeResponse) -> None:
    llm = OpenAICompatibleLLM(make_config(), client=FakeClient(FakeCompletions(response)))

    with pytest.raises(LLMError, match='empty response'):
        llm.complete([Message(role='user', content='Hi')])


def test_complete_wraps_client_errors() -> None:
    client_error = RuntimeError('connection refused')
    llm = OpenAICompatibleLLM(make_config(), client=FakeClient(FakeCompletions(client_error)))

    with pytest.raises(LLMError, match='model request failed') as raised:
        llm.complete([Message(role='user', content='Hi')])

    assert raised.value.__cause__ is client_error


def test_stream_complete_sends_stream_true_and_yields_text_parts() -> None:
    completions = FakeCompletions(
        [
            FakeStreamChunk([FakeStreamChoice(FakeStreamDelta('Hel'))]),
            FakeStreamChunk([FakeStreamChoice(FakeStreamDelta(None))]),
            FakeStreamChunk([FakeStreamChoice(FakeStreamDelta('lo'))]),
            FakeStreamChunk([]),
        ],
    )
    llm = OpenAICompatibleLLM(make_config(), client=FakeClient(completions))

    result = list(llm.stream_complete([Message(role='user', content='Hi')]))

    assert result == ['Hel', 'lo']
    assert completions.calls == [
        {
            'model': 'gemma3',
            'messages': [{'role': 'user', 'content': 'Hi'}],
            'temperature': 0.3,
            'stream': True,
        },
    ]


def test_stream_complete_wraps_client_errors() -> None:
    client_error = RuntimeError('connection refused')
    llm = OpenAICompatibleLLM(make_config(), client=FakeClient(FakeCompletions(client_error)))

    with pytest.raises(LLMError, match='streaming model request failed') as raised:
        list(llm.stream_complete([Message(role='user', content='Hi')]))

    assert raised.value.__cause__ is client_error
