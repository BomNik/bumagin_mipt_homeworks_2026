from pathlib import Path

import pytest

from gigavibe.errors import FileAttachmentError
from gigavibe.files import MAX_ATTACHMENT_SIZE_BYTES, replace_file_mentions


def write_text_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding='utf-8')
    return path


def test_message_without_file_mentions_is_unchanged() -> None:
    message = 'Explain why this Python code fails.'

    assert replace_file_mentions(message) == message


def test_single_file_mention_is_replaced_with_file_content(tmp_path: Path) -> None:
    source_file = write_text_file(tmp_path / 'main.py', 'print(1 / 0)\n')
    message = f'Find the bug: @::{source_file}::'

    result = replace_file_mentions(message)

    assert result == 'Find the bug: print(1 / 0)\n'


def test_multiple_file_mentions_are_replaced(tmp_path: Path) -> None:
    first_file = write_text_file(tmp_path / 'first.py', 'print("first")')
    second_file = write_text_file(tmp_path / 'second.py', 'print("second")')
    message = f'Compare @::{first_file}:: with @::{second_file}::'

    result = replace_file_mentions(message)

    assert result == 'Compare print("first") with print("second")'


def test_missing_file_raises_file_attachment_error(tmp_path: Path) -> None:
    missing_file = tmp_path / 'missing.py'

    with pytest.raises(FileAttachmentError) as raised:
        replace_file_mentions(f'Check @::{missing_file}::')

    assert raised.value.path == missing_file
    assert raised.value.message == 'file does not exist'


def test_directory_raises_file_attachment_error(tmp_path: Path) -> None:
    with pytest.raises(FileAttachmentError) as raised:
        replace_file_mentions(f'Check @::{tmp_path}::')

    assert raised.value.path == tmp_path
    assert raised.value.message == 'path is not a file'


def test_too_large_file_is_rejected_before_reading(tmp_path: Path) -> None:
    large_file = tmp_path / 'large.txt'
    large_file.write_bytes(b'x' * (MAX_ATTACHMENT_SIZE_BYTES + 1))

    with pytest.raises(FileAttachmentError) as raised:
        replace_file_mentions(f'Summarize @::{large_file}::')

    assert raised.value.path == large_file
    assert raised.value.message == 'file is larger than 5 MB'


def test_unclosed_file_marker_raises_file_attachment_error(tmp_path: Path) -> None:
    file_path = tmp_path / 'main.py'

    with pytest.raises(FileAttachmentError) as raised:
        replace_file_mentions(f'Check @::{file_path}')

    assert raised.value.path is None
    assert raised.value.message == 'unclosed file mention'
