from pathlib import Path

import pytest

from gigavibe.config import AppConfig, load_config, parse_flat_yaml
from gigavibe.errors import ConfigError


def collect_config_errors(error_group: ExceptionGroup[Exception]) -> dict[str, ConfigError]:
    errors: dict[str, ConfigError] = {}
    for error in error_group.exceptions:
        if isinstance(error, ConfigError):
            errors[error.field] = error
    return errors


def write_config(tmp_path: Path, content: str) -> Path:
    config_path = tmp_path / 'config.yaml'
    config_path.write_text(content, encoding='utf-8')
    return config_path


def test_parse_flat_yaml_reads_simple_values_and_urls(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        """
        api_key: ollama
        api_host: http://localhost:11434/v1/
        model: gemma3
        """,
    )

    values = parse_flat_yaml(config_path)

    assert values == {
        'api_key': 'ollama',
        'api_host': 'http://localhost:11434/v1/',
        'model': 'gemma3',
    }


def test_environment_variables_override_yaml_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = write_config(
        tmp_path,
        """
        api_key: yaml-key
        api_host: http://yaml-host/v1/
        model: yaml-model
        limit_message: 10
        limit_chars: 2000
        temperature: 0.1
        system_prompt: YAML prompt
        """,
    )
    monkeypatch.setenv('API_KEY', 'env-key')
    monkeypatch.setenv('MODEL', 'env-model')
    monkeypatch.setenv('LIMIT_CHARS', '3000')

    config = load_config(config_path)

    assert config == AppConfig(
        api_key='env-key',
        api_host='http://yaml-host/v1/',
        model='env-model',
        limit_message=10,
        limit_chars=3000,
        temperature=0.1,
        system_prompt='YAML prompt',
    )


def test_missing_required_config_is_reported(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        """
        api_key: ollama
        """,
    )

    with pytest.raises(ExceptionGroup) as raised:
        load_config(config_path)

    errors = collect_config_errors(raised.value)
    assert set(errors) == {'api_host', 'model'}
    assert errors['api_host'].message == 'required value is missing'
    assert errors['model'].message == 'required value is missing'


def test_missing_file_and_environment_is_reported(tmp_path: Path) -> None:
    config_path = tmp_path / 'missing-config.yaml'

    with pytest.raises(ExceptionGroup) as raised:
        load_config(config_path)

    errors = collect_config_errors(raised.value)
    assert errors['config'].message == 'provide config.yaml or environment variables'


@pytest.mark.parametrize('temperature', ['-0.1', '1.5', 'not-a-float'])
def test_invalid_temperature_is_rejected(tmp_path: Path, temperature: str) -> None:
    config_path = write_config(
        tmp_path,
        f"""
        api_key: ollama
        api_host: http://localhost:11434/v1/
        model: gemma3
        temperature: {temperature}
        """,
    )

    with pytest.raises(ExceptionGroup) as raised:
        load_config(config_path)

    errors = collect_config_errors(raised.value)
    assert errors['temperature'].value == temperature


@pytest.mark.parametrize(
    ('field_name', 'field_value'),
    [
        ('limit_message', '-1'),
        ('limit_chars', '-10'),
        ('limit_message', 'not-an-int'),
        ('limit_chars', '1.5'),
    ],
)
def test_invalid_limits_are_rejected(tmp_path: Path, field_name: str, field_value: str) -> None:
    config_path = write_config(
        tmp_path,
        f"""
        api_key: ollama
        api_host: http://localhost:11434/v1/
        model: gemma3
        {field_name}: {field_value}
        """,
    )

    with pytest.raises(ExceptionGroup) as raised:
        load_config(config_path)

    errors = collect_config_errors(raised.value)
    assert errors[field_name].value == field_value


def test_system_prompt_longer_than_limit_chars_is_rejected(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        """
        api_key: ollama
        api_host: http://localhost:11434/v1/
        model: gemma3
        limit_chars: 5
        system_prompt: too long
        """,
    )

    with pytest.raises(ExceptionGroup) as raised:
        load_config(config_path)

    errors = collect_config_errors(raised.value)
    assert errors['system_prompt'].message == 'must not be longer than limit_chars'
    assert errors['system_prompt'].value == 'too long'


def test_load_config_reports_all_validation_errors_together(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        """
        api_key: ollama
        limit_message: -1
        limit_chars: not-an-int
        temperature: 2
        """,
    )

    with pytest.raises(ExceptionGroup) as raised:
        load_config(config_path)

    errors = collect_config_errors(raised.value)
    assert set(errors) == {'api_host', 'model', 'limit_message', 'limit_chars', 'temperature'}
