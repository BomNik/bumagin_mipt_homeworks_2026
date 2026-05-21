from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from gigavibe.cli import CommandKind, Console, parse_command
from gigavibe.config import AppConfig, load_config
from gigavibe.context import ChatHistory, Message
from gigavibe.errors import ConfigError, FileAttachmentError, LLMError
from gigavibe.files import replace_file_mentions
from gigavibe.llm import InputMessage, OpenAICompatibleLLM


class ConsoleProtocol(Protocol):
    def read(self, prompt: str = '>>> ') -> str: ...

    def write(self, text: str) -> None: ...

    def clear(self) -> None: ...


class LLMProtocol(Protocol):
    def complete(self, messages: Sequence[InputMessage]) -> str: ...


class ChatApplication:
    def __init__(
        self,
        config: AppConfig,
        llm: LLMProtocol,
        *,
        history: ChatHistory | None = None,
        console: ConsoleProtocol | None = None,
    ) -> None:
        self._config = config
        self._llm = llm
        self._history = history or ChatHistory()
        self._console = console or Console()

    def run(self) -> None:
        while True:
            user_input = self._console.read()
            if not self.handle_user_input(user_input):
                return

    def handle_user_input(self, user_input: str) -> bool:
        command = parse_command(user_input)

        if command.kind is CommandKind.EXIT:
            return False
        if command.kind is CommandKind.RESET:
            self._history.clear()
            self._console.clear()
            return True

        self._handle_chat_message(command.text)
        return True

    def _handle_chat_message(self, user_input: str) -> None:
        try:
            prepared_input = replace_file_mentions(user_input)
        except FileAttachmentError as error:
            self._console.write(f'File error: {error}')
            return

        self._history.add_user(prepared_input)
        self._history.trim(
            limit_message=self._config.limit_message,
            limit_chars=self._config.limit_chars,
            system_prompt=self._config.system_prompt,
        )

        outgoing_messages = build_outgoing_messages(
            system_prompt=self._config.system_prompt,
            history=self._history.to_list(),
        )

        try:
            assistant_response = self._llm.complete(outgoing_messages)
        except KeyboardInterrupt:
            self._console.write('Request interrupted.')
            return
        except LLMError as error:
            self._console.write(f'LLM error: {error}')
            return

        self._history.add_assistant(assistant_response)
        self._console.write(assistant_response)


def build_outgoing_messages(system_prompt: str, history: list[Message]) -> list[InputMessage]:
    messages: list[InputMessage] = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.extend(history)
    return messages


def default_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / 'config.yaml'


def run(config_path: Path | str | None = None) -> None:
    console = Console()
    path = Path(config_path) if config_path is not None else default_config_path()

    try:
        config = load_config(path)
    except ExceptionGroup as error_group:
        _write_config_error_group(console, error_group)
        return
    except ConfigError as error:
        console.write(f'Config error: {error}')
        return

    app = ChatApplication(config, OpenAICompatibleLLM(config), console=console)
    app.run()


def _write_config_error_group(
    console: ConsoleProtocol,
    error_group: ExceptionGroup[Exception],
) -> None:
    console.write('Invalid configuration:')
    for error in error_group.exceptions:
        console.write(f'- {error}')
