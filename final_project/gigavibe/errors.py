from pathlib import Path


class ConfigError(Exception):
    """Configuration is missing or contains an invalid value."""

    def __init__(self, field: str, message: str, value: str | None = None) -> None:
        self.field = field
        self.message = message
        self.value = value
        super().__init__(str(self))

    def __str__(self) -> str:
        text = f'{self.field}: {self.message}'
        if self.value is not None:
            text = f'{text}, got {self.value!r}'
        return text


class FileAttachmentError(Exception):
    """A file mention cannot be safely replaced with file contents."""

    def __init__(self, message: str, path: Path | None = None) -> None:
        self.message = message
        self.path = path
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.path is None:
            return self.message
        return f'{self.path}: {self.message}'


class LLMError(Exception):
    """The model request failed or returned an invalid response."""
