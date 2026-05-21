import os
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class CommandKind(Enum):
    CHAT = 'chat'
    EXIT = 'exit'
    FILE_CHUNK = 'file_chunk'
    RESET = 'reset'


@dataclass(frozen=True)
class ParsedCommand:
    kind: CommandKind
    text: str


class ConsoleProtocol(Protocol):
    def read(self, prompt: str = '>>> ') -> str: ...

    def write(self, text: str) -> None: ...

    def write_part(self, text: str) -> None: ...

    def clear(self) -> None: ...


class Console:
    def read(self, prompt: str = '>>> ') -> str:
        return input(prompt)

    def write(self, text: str) -> None:
        print(text)

    def write_part(self, text: str) -> None:
        print(text, end='', flush=True)

    def clear(self) -> None:
        command = 'cls' if os.name == 'nt' else 'clear'
        os.system(command)


def parse_command(user_input: str) -> ParsedCommand:
    stripped_input = user_input.strip()

    if stripped_input == r'\q':
        return ParsedCommand(kind=CommandKind.EXIT, text='')
    if stripped_input == '/reset':
        return ParsedCommand(kind=CommandKind.RESET, text='')
    if stripped_input == '/file_chunk' or stripped_input.startswith('/filechunk'):
        return ParsedCommand(kind=CommandKind.FILE_CHUNK, text=stripped_input)

    return ParsedCommand(kind=CommandKind.CHAT, text=user_input)
