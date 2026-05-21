import os
from dataclasses import dataclass
from enum import Enum


class CommandKind(Enum):
    CHAT = 'chat'
    EXIT = 'exit'
    RESET = 'reset'


@dataclass(frozen=True)
class ParsedCommand:
    kind: CommandKind
    text: str


def parse_command(user_input: str) -> ParsedCommand:
    stripped_input = user_input.strip()

    if stripped_input == r'\q':
        return ParsedCommand(kind=CommandKind.EXIT, text='')
    if stripped_input == '/reset':
        return ParsedCommand(kind=CommandKind.RESET, text='')

    return ParsedCommand(kind=CommandKind.CHAT, text=user_input)


class Console:
    def read(self, prompt: str = '>>> ') -> str:
        return input(prompt)

    def write(self, text: str) -> None:
        print(text)

    def clear(self) -> None:
        command = 'cls' if os.name == 'nt' else 'clear'
        os.system(command)
