from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from gigavibe.app import ChatApplication, build_outgoing_messages, default_config_path
from gigavibe.config import AppConfig
from gigavibe.context import ChatHistory, Message
from gigavibe.errors import LLMError
from gigavibe.llm import InputMessage


class FakeLLM:
    def __init__(self, response: str | BaseException = 'assistant response') -> None:
        self.response = response
        self.calls: list[list[InputMessage]] = []

    def complete(self, messages: Sequence[InputMessage]) -> str:
        self.calls.append(list(messages))
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


@dataclass
class FakeConsole:
    outputs: list[str]
    clear_count: int = 0

    def write(self, text: str) -> None:
        self.outputs.append(text)

    def read(self, prompt: str = '>>> ') -> str:
        raise AssertionError('FakeConsole.read should not be called in these tests')

    def clear(self) -> None:
        self.clear_count += 1


def make_config() -> AppConfig:
    return AppConfig(
        api_key='ollama',
        api_host='http://localhost:11434/v1/',
        model='gemma3',
        limit_message=10,
        limit_chars=2000,
        temperature=0.2,
        system_prompt='You are concise.',
    )


def test_build_outgoing_messages_prepends_system_prompt() -> None:
    messages = build_outgoing_messages(
        system_prompt='System instruction',
        history=[
            Message(role='user', content='Hello'),
            Message(role='assistant', content='Hi'),
        ],
    )

    assert messages == [
        {'role': 'system', 'content': 'System instruction'},
        Message(role='user', content='Hello'),
        Message(role='assistant', content='Hi'),
    ]


def test_build_outgoing_messages_skips_empty_system_prompt() -> None:
    messages = build_outgoing_messages(
        system_prompt='',
        history=[Message(role='user', content='Hello')],
    )

    assert messages == [Message(role='user', content='Hello')]


def test_handle_user_input_sends_chat_and_saves_assistant_response() -> None:
    history = ChatHistory()
    llm = FakeLLM('Hi')
    console = FakeConsole([])
    app = ChatApplication(make_config(), llm, history=history, console=console)

    should_continue = app.handle_user_input('Hello')

    assert should_continue is True
    assert llm.calls == [
        [
            {'role': 'system', 'content': 'You are concise.'},
            Message(role='user', content='Hello'),
        ],
    ]
    assert history.to_list() == [
        Message(role='user', content='Hello'),
        Message(role='assistant', content='Hi'),
    ]
    assert console.outputs == ['Hi']


def test_handle_user_input_replaces_file_mentions_before_sending(tmp_path: Path) -> None:
    source_file = tmp_path / 'main.py'
    source_file.write_text('print(1)\n', encoding='utf-8')
    llm = FakeLLM('done')
    app = ChatApplication(make_config(), llm, console=FakeConsole([]))

    app.handle_user_input(f'Check @::{source_file}::')

    assert llm.calls[0][-1] == Message(role='user', content='Check print(1)\n')


def test_reset_command_clears_history_and_console() -> None:
    history = ChatHistory([Message(role='user', content='old')])
    console = FakeConsole([])
    app = ChatApplication(make_config(), FakeLLM(), history=history, console=console)

    should_continue = app.handle_user_input('/reset')

    assert should_continue is True
    assert history.to_list() == []
    assert console.clear_count == 1


def test_exit_command_stops_loop() -> None:
    app = ChatApplication(make_config(), FakeLLM(), console=FakeConsole([]))

    assert app.handle_user_input(r'\q') is False


def test_file_error_does_not_add_message_to_history() -> None:
    history = ChatHistory()
    console = FakeConsole([])
    app = ChatApplication(make_config(), FakeLLM(), history=history, console=console)

    app.handle_user_input('@::/missing/file.py::')

    assert history.to_list() == []
    assert console.outputs == ['File error: /missing/file.py: file does not exist']


def test_llm_error_does_not_add_assistant_message() -> None:
    history = ChatHistory()
    console = FakeConsole([])
    app = ChatApplication(
        make_config(),
        FakeLLM(LLMError('model request failed')),
        history=history,
        console=console,
    )

    app.handle_user_input('Hello')

    assert history.to_list() == [Message(role='user', content='Hello')]
    assert console.outputs == ['LLM error: model request failed']


def test_keyboard_interrupt_during_llm_request_is_handled() -> None:
    history = ChatHistory()
    console = FakeConsole([])
    app = ChatApplication(
        make_config(),
        FakeLLM(KeyboardInterrupt()),
        history=history,
        console=console,
    )

    app.handle_user_input('Hello')

    assert history.to_list() == [Message(role='user', content='Hello')]
    assert console.outputs == ['Request interrupted.']
