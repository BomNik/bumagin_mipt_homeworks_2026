import pytest

from gigavibe.chunking import (
    ChunkMode,
    ChunkOptions,
    chunk_by_length,
    chunk_by_paragraphs,
    parse_filechunk_command,
)
from gigavibe.errors import ChunkingError


def test_parse_filechunk_default_options() -> None:
    assert parse_filechunk_command('/filechunk') == ChunkOptions(
        mode=ChunkMode.PARAGRAPH,
        size=1,
        auto_confirm=False,
    )


def test_parse_file_chunk_alias() -> None:
    assert parse_filechunk_command('/file_chunk') == ChunkOptions(
        mode=ChunkMode.PARAGRAPH,
        size=1,
        auto_confirm=False,
    )


def test_parse_filechunk_paragraph_group_size() -> None:
    assert parse_filechunk_command('/filechunk paragraph=3 -y') == ChunkOptions(
        mode=ChunkMode.PARAGRAPH,
        size=3,
        auto_confirm=True,
    )


def test_parse_filechunk_length_size() -> None:
    assert parse_filechunk_command('/filechunk len=150') == ChunkOptions(
        mode=ChunkMode.LENGTH,
        size=150,
        auto_confirm=False,
    )


@pytest.mark.parametrize(
    'command',
    [
        '/filechunk paragraph=0',
        '/filechunk len=0',
        '/filechunk unknown=1',
        '/filechunk paragraph=2 len=100',
        '/filechunk -x',
    ],
)
def test_parse_filechunk_rejects_invalid_options(command: str) -> None:
    with pytest.raises(ChunkingError):
        parse_filechunk_command(command)


def test_chunk_by_paragraphs_splits_non_empty_paragraphs() -> None:
    text = 'First paragraph\n\nSecond paragraph\n\n\nThird paragraph'

    assert chunk_by_paragraphs(text, paragraphs_per_chunk=1) == [
        'First paragraph',
        'Second paragraph',
        'Third paragraph',
    ]


def test_chunk_by_paragraphs_groups_paragraphs() -> None:
    text = 'A\nB\nC\nD'

    assert chunk_by_paragraphs(text, paragraphs_per_chunk=3) == [
        'A\nB\nC',
        'D',
    ]


def test_chunk_by_length_splits_text_by_character_count() -> None:
    assert chunk_by_length('abcdefghij', max_chars=4) == ['abcd', 'efgh', 'ij']
