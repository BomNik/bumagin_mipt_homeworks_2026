from dataclasses import dataclass
from enum import Enum

from gigavibe.errors import ChunkingError


class ChunkMode(Enum):
    PARAGRAPH = 'paragraph'
    LENGTH = 'length'


@dataclass(frozen=True)
class ChunkOptions:
    mode: ChunkMode
    size: int
    auto_confirm: bool = False


def parse_filechunk_command(command: str) -> ChunkOptions:
    parts = command.strip().split()
    if not parts or parts[0] not in {'/filechunk', '/file_chunk'}:
        raise ChunkingError('expected /filechunk or /file_chunk')

    mode = ChunkMode.PARAGRAPH
    size = 1
    auto_confirm = False
    explicit_mode_seen = False

    for option in parts[1:]:
        if option == '-y':
            auto_confirm = True
            continue

        if option.startswith('paragraph='):
            if explicit_mode_seen:
                raise ChunkingError('only one chunk size option is allowed')
            mode = ChunkMode.PARAGRAPH
            size = _parse_positive_int(option, 'paragraph')
            explicit_mode_seen = True
            continue

        if option.startswith('len='):
            if explicit_mode_seen:
                raise ChunkingError('only one chunk size option is allowed')
            mode = ChunkMode.LENGTH
            size = _parse_positive_int(option, 'len')
            explicit_mode_seen = True
            continue

        raise ChunkingError(f'unknown filechunk option: {option}')

    return ChunkOptions(mode=mode, size=size, auto_confirm=auto_confirm)


def chunk_text(text: str, options: ChunkOptions) -> list[str]:
    if options.mode is ChunkMode.PARAGRAPH:
        return chunk_by_paragraphs(text, paragraphs_per_chunk=options.size)
    return chunk_by_length(text, max_chars=options.size)


def chunk_by_paragraphs(text: str, *, paragraphs_per_chunk: int) -> list[str]:
    if paragraphs_per_chunk <= 0:
        raise ChunkingError('paragraphs_per_chunk must be positive')

    paragraphs = [paragraph.strip() for paragraph in text.split('\n') if paragraph.strip()]
    chunks: list[str] = []
    for start in range(0, len(paragraphs), paragraphs_per_chunk):
        chunks.append('\n'.join(paragraphs[start : start + paragraphs_per_chunk]))
    return chunks


def chunk_by_length(text: str, *, max_chars: int) -> list[str]:
    if max_chars <= 0:
        raise ChunkingError('max_chars must be positive')

    return [text[start : start + max_chars] for start in range(0, len(text), max_chars)]


def _parse_positive_int(option: str, name: str) -> int:
    raw_value = option.split('=', 1)[1]
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ChunkingError(f'{name} must be an integer') from error
    if value <= 0:
        raise ChunkingError(f'{name} must be positive')
    return value
