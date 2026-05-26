# GigaVibeMiptCode

Консольный ИИ-ассистент для общения с большими языковыми моделями через OpenAI-совместимое API.

## Установка и запуск

Версия Python: 3.13+.

Зависимости управляются в корневом `pyproject.toml`.

В примерах используются `uv` и `ollama`.

**1. Установка зависимостей**

```bash
uv sync --all-groups
```

**2. Настройка Ollama**

Загрузите [Ollama](https://ollama.com/) и запустите модель в отдельном терминале:

```bash
ollama serve
ollama pull gemma3:270m
```

**3. Конфигурация**

Создайте файл `config.yaml` в директории `final_project/` на основе `config.example.yaml` или передайте настройки через
переменные окружения (они имеют приоритет).

Пример `config.yaml`:

```yaml
api_key: ollama
api_host: http://localhost:11434/v1/
model: gemma3:270m
limit_message: 20
limit_chars: 2000
temperature: 0.2
system_prompt: You are a helpful assistant.
```

**4. Запуск приложения**

```bash
uv run python final_project/main.py
```


Все настройки можно передать через переменные окружения:

```bash
export API_KEY=ollama
export API_HOST=http://localhost:11434/v1/
export MODEL=gemma3:270m
export LIMIT_MESSAGE=20
export LIMIT_CHARS=2000
export TEMPERATURE=0.2
uv run python final_project/main.py
```

## Использование и команды

- **Обычный чат с ИИ**: Просто вводите свой запрос.
- **Прикрепление файла**: Используйте синтаксис `@::путь/к/файлу::`.
    - Пример: *Расскажи, что делает этот скрипт: @::main.py::*
- `\q` — выйти из интерактивного режима.
- `/reset` — очистить историю сообщений и стереть остатки прошлого чата с экрана (начать новую сессию).
- `/file_chunk` или `/filechunk` — режим интерактивной обработки файлов по частям.
    - Поддерживает флаги разбиения: `paragraph=N` (по абзацам), `len=N` (по длине).
    - Флаг `-y` включает автоматическую обработку всех чанков без подтверждения.
    - Пример: `/filechunk paragraph=3 -y`
- **Прерывание (Ctrl+C)**: Нажатие `Ctrl+C` во время генерации ответа модели прерывает поток и возвращает вас к вводу
  нового сообщения.

## Тестирование и проверки линтерами

Запуск тестов с отчетом о покрытии:

```bash
uv run python -m pytest final_project/tests --cov=final_project/gigavibe --cov-report=html:final_project/coverage_html --cov-report=term
```

Запуск линтеров:

```bash
uv run python -m ruff check --config final_project/ruff.toml final_project
uv run python -m mypy final_project
```

HTML-отчет покрытия генерируется в `final_project/coverage_html/index.html`.
