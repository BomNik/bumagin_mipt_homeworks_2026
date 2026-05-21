from dataclasses import dataclass
from typing import Literal


MessageRole = Literal['user', 'assistant']


@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str

    def to_dict(self) -> dict[str, str]:
        return {'role': self.role, 'content': self.content}


class ChatHistory:
    def __init__(self, messages: list[Message] | None = None) -> None:
        self._messages = list(messages or [])

    def add_user(self, content: str) -> None:
        self.add_message('user', content)

    def add_assistant(self, content: str) -> None:
        self.add_message('assistant', content)

    def add_message(self, role: MessageRole, content: str) -> None:
        self._messages.append(Message(role=role, content=content))

    def clear(self) -> None:
        self._messages.clear()

    def to_list(self) -> list[Message]:
        return list(self._messages)

    def to_dicts(self) -> list[dict[str, str]]:
        return [message.to_dict() for message in self._messages]

    def trim(
        self,
        *,
        limit_message: int | None,
        limit_chars: int | None,
        system_prompt: str,
    ) -> None:
        self._trim_by_message_count(limit_message)
        self._trim_by_character_count(limit_chars, system_prompt)

    def _trim_by_message_count(self, limit_message: int | None) -> None:
        if limit_message is None:
            return
        if limit_message <= 0:
            self.clear()
            return

        extra_count = len(self._messages) - limit_message
        if extra_count > 0:
            del self._messages[:extra_count]

    def _trim_by_character_count(self, limit_chars: int | None, system_prompt: str) -> None:
        if limit_chars is None:
            return

        history_budget = limit_chars - len(system_prompt)
        if history_budget <= 0:
            self.clear()
            return

        while len(self._messages) > 1 and total_content_length(self._messages) > history_budget:
            del self._messages[0]

        if self._messages and total_content_length(self._messages) > history_budget:
            newest_message = self._messages[-1]
            self._messages[-1] = Message(
                role=newest_message.role,
                content=newest_message.content[-history_budget:],
            )


def total_content_length(messages: list[Message]) -> int:
    return sum(len(message.content) for message in messages)
