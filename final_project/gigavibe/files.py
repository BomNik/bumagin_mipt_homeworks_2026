import re
from pathlib import Path

from gigavibe.errors import FileAttachmentError

MAX_ATTACHMENT_SIZE_BYTES = 5 * 1024 * 1024
FILE_MENTION_PATTERN = re.compile(r'@::(?P<path>.*?)::')


def replace_file_mentions(message: str) -> str:
    _ensure_no_unclosed_file_mention(message)
    return FILE_MENTION_PATTERN.sub(_replace_match_with_file_content, message)


def _replace_match_with_file_content(match: re.Match[str]) -> str:
    raw_path = match.group('path')
    path = Path(raw_path).expanduser()
    return _read_attachment(path)


def _read_attachment(path: Path) -> str:
    if not path.exists():
        raise FileAttachmentError('file does not exist', path)
    if not path.is_file():
        raise FileAttachmentError('path is not a file', path)
    if path.stat().st_size > MAX_ATTACHMENT_SIZE_BYTES:
        raise FileAttachmentError('file is larger than 5 MB', path)

    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError as error:
        raise FileAttachmentError('file is not valid UTF-8 text', path) from error


def _ensure_no_unclosed_file_mention(message: str) -> None:
    search_start = 0
    while True:
        marker_start = message.find('@::', search_start)
        if marker_start == -1:
            return
        marker_end = message.find('::', marker_start + len('@::'))
        if marker_end == -1:
            raise FileAttachmentError('unclosed file mention')
        search_start = marker_end + len('::')
