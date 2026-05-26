from pathlib import Path

from gigavibe.chunking import chunk_text, parse_filechunk_command
from gigavibe.cli import CommandKind, Console, ConsoleProtocol, parse_command
from gigavibe.config import AppConfig, load_config
from gigavibe.context import ChatHistory, Message
from gigavibe.errors import ChunkingError, ConfigError, FileAttachmentError, LLMError
from gigavibe.files import read_text_file, replace_file_mentions
from gigavibe.llm import InputMessage, LLMProtocol, OpenAICompatibleLLM


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
        if command.kind is CommandKind.FILE_CHUNK:
            self._handle_filechunk_command(command.text)
            return True

        self._handle_chat_message(command.text)
        return True

    def _handle_filechunk_command(self, command_text: str) -> None:
        try:
            options = parse_filechunk_command(command_text)
            self._console.write('Enter file path:')
            file_path = Path(self._console.read(''))
            text = read_text_file(file_path)
            chunks = chunk_text(text, options)
        except (ChunkingError, FileAttachmentError) as error:
            self._console.write(f'File chunk error: {error}')
            return

        self._console.write('Accepted. What should be done for each chunk?')
        user_prompt = self._console.read('')
        self._console.write('Accepted. Starting chunk processing:')

        for index, chunk in enumerate(chunks):
            if index > 0 and not options.auto_confirm:
                next_input = self._console.read('')
                if next_input == r'\q':
                    self._console.write('File processing stopped.')
                    return

            self._process_chunk(user_prompt, chunk)

        self._console.write('File processing complete.')

    def _process_chunk(self, user_prompt: str, chunk: str) -> None:
        try:
            response = self._llm.complete(
                [Message(role='user', content=f'{user_prompt}\n\n{chunk}')],
            )
        except KeyboardInterrupt:
            self._console.write('Request interrupted.')
            return
        except LLMError as error:
            self._console.write(f'LLM error: {error}')
            return

        self._console.write(response)

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
            response_parts: list[str] = []
            for text_part in self._llm.stream_complete(outgoing_messages):
                self._console.write_part(text_part)
                response_parts.append(text_part)
        except KeyboardInterrupt:
            self._console.write('Request interrupted.')
            self._history.remove_last()
            return
        except LLMError as error:
            self._console.write(f'LLM error: {error}')
            self._history.remove_last()
            return

        assistant_response = ''.join(response_parts)
        if not assistant_response:
            self._console.write('LLM error: empty streaming response from model')
            self._history.remove_last()
            return

        self._history.add_assistant(assistant_response)
        self._console.write('')


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
