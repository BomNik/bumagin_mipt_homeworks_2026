from gigavibe.cli import CommandKind, ParsedCommand, parse_command


def test_parse_command_recognizes_exit() -> None:
    assert parse_command(r'\q') == ParsedCommand(kind=CommandKind.EXIT, text='')


def test_parse_command_recognizes_reset() -> None:
    assert parse_command('/reset') == ParsedCommand(kind=CommandKind.RESET, text='')


def test_parse_command_treats_regular_text_as_chat() -> None:
    assert parse_command('hello') == ParsedCommand(
        kind=CommandKind.CHAT,
        text='hello',
    )


def test_parse_command_strips_command_whitespace() -> None:
    assert parse_command('  /reset  ') == ParsedCommand(kind=CommandKind.RESET, text='')
