import os
from dataclasses import dataclass
from pathlib import Path

from gigavibe.errors import ConfigError

ENV_TO_CONFIG_KEY = {
    'API_KEY': 'api_key',
    'API_HOST': 'api_host',
    'MODEL': 'model',
    'LIMIT_MESSAGE': 'limit_message',
    'LIMIT_CHARS': 'limit_chars',
    'TEMPERATURE': 'temperature',
}

REQUIRED_KEYS = ('api_key', 'api_host', 'model')
DEFAULT_TEMPERATURE = 0.2


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    api_host: str
    model: str
    limit_message: int | None = None
    limit_chars: int | None = None
    temperature: float = DEFAULT_TEMPERATURE
    system_prompt: str = ''


def load_config(path: Path | str) -> AppConfig:
    config_path = Path(path)
    raw_values: dict[str, str] = {}

    if config_path.exists():
        raw_values.update(parse_flat_yaml(config_path))

    raw_values.update(_read_environment_values())
    if not raw_values:
        raise ExceptionGroup(
            'Invalid configuration',
            [ConfigError('config', 'provide config.yaml or environment variables')],
        )

    errors = [
        ConfigError(key, 'required value is missing')
        for key in REQUIRED_KEYS
        if not raw_values.get(key)
    ]

    limit_message, limit_message_error = _parse_optional_int(raw_values, 'limit_message')
    limit_chars, limit_chars_error = _parse_optional_int(raw_values, 'limit_chars')
    temperature, temperature_error = _parse_temperature(raw_values.get('temperature'))
    system_prompt = raw_values.get('system_prompt', '')

    errors.extend(
        error
        for error in (limit_message_error, limit_chars_error, temperature_error)
        if error is not None
    )

    if limit_chars is not None and len(system_prompt) > limit_chars:
        errors.append(
            ConfigError('system_prompt', 'must not be longer than limit_chars', system_prompt),
        )

    if errors:
        raise ExceptionGroup('Invalid configuration', errors)

    return AppConfig(
        api_key=raw_values['api_key'],
        api_host=raw_values['api_host'],
        model=raw_values['model'],
        limit_message=limit_message,
        limit_chars=limit_chars,
        temperature=temperature,
        system_prompt=system_prompt,
    )


def parse_flat_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}

    for line_number, raw_line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' not in line:
            raise ConfigError('config', f'line {line_number}: expected "key: value"', raw_line)

        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ConfigError('config', f'line {line_number}: key is empty', raw_line)

        values[key] = value

    return values


def _read_environment_values() -> dict[str, str]:
    values: dict[str, str] = {}

    for env_name, config_key in ENV_TO_CONFIG_KEY.items():
        env_value = os.environ.get(env_name)
        if env_value is not None:
            values[config_key] = env_value

    return values


def _parse_optional_int(values: dict[str, str], key: str) -> tuple[int | None, ConfigError | None]:
    raw_value = values.get(key)
    if raw_value is None or raw_value == '':
        return None, None

    try:
        parsed_value = int(raw_value)
    except ValueError:
        return None, ConfigError(key, 'must be an integer', raw_value)

    if parsed_value < 0:
        return None, ConfigError(key, 'must not be negative', raw_value)

    return parsed_value, None


def _parse_temperature(raw_value: str | None) -> tuple[float, ConfigError | None]:
    if raw_value is None or raw_value == '':
        return DEFAULT_TEMPERATURE, None

    try:
        temperature = float(raw_value)
    except ValueError:
        return DEFAULT_TEMPERATURE, ConfigError(
            'temperature',
            'must be a number from 0 to 1',
            raw_value,
        )

    if not 0 <= temperature <= 1:
        return DEFAULT_TEMPERATURE, ConfigError(
            'temperature',
            'must be a number from 0 to 1',
            raw_value,
        )

    return temperature, None
