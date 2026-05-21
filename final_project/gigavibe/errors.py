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
