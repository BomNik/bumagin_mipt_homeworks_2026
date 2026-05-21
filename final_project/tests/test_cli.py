from gigavibe.cli import CommandKind, ParsedCommand, parse_command


def test_parse_command_recognizes_exit() -> None:
    assert parse_command(r'\q') == ParsedCommand(kind=CommandKind.EXIT, text='')


def test_parse_command_recognizes_reset() -> None:
    assert parse_command('/reset') == ParsedCommand(kind=CommandKind.RESET, text='')


def test_parse_command_recognizes_filechunk() -> None:
    assert parse_command('/filechunk paragraph=3 -y') == ParsedCommand(
        kind=CommandKind.FILE_CHUNK,
        text='/filechunk paragraph=3 -y',
    )


def test_parse_command_recognizes_file_chunk_alias() -> None:
    assert parse_command('/file_chunk') == ParsedCommand(
        kind=CommandKind.FILE_CHUNK,
        text='/file_chunk',
    )


def test_parse_command_recognizes_file_chunk_alias_with_options() -> None:
    assert parse_command('/file_chunk paragraph=3 -y') == ParsedCommand(
        kind=CommandKind.FILE_CHUNK,
        text='/file_chunk paragraph=3 -y',
    )


def test_parse_command_treats_regular_text_as_chat() -> None:
    assert parse_command('hello') == ParsedCommand(
        kind=CommandKind.CHAT,
        text='hello',
    )


def test_parse_command_strips_command_whitespace() -> None:
    assert parse_command('  /reset  ') == ParsedCommand(kind=CommandKind.RESET, text='')
