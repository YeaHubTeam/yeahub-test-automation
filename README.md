# YeaHub Test Automation

Фреймворк для автоматизированного тестирования REST API сервиса YeaHub.

## О проекте

Проект покрывает основные пользовательские сценарии API:
- регистрацию и аутентификацию пользователей
- работу с профилем
- сброс и смену пароля
- верификацию email
- mail-flow через IMAP для проверки писем верификации

## Технологии

- Python `3.14.x`
- `uv` для управления зависимостями и виртуальным окружением
- `pytest` для запуска тестов
- `ruff` для линтинга и форматирования
- `allure-pytest` для отчетов

## Быстрый старт

### 1. Установить Python и uv

Убедись, что на машине установлены Python `3.14.x` и `uv`.

Пример для macOS:

```bash
brew install python@3.14
brew install uv
```

Проверка:

```bash
python3.14 --version
uv --version
```

### 2. Поднять окружение проекта

```bash
uv sync --python 3.14
```

Что делает команда:
- создает или обновляет `.venv`
- устанавливает зависимости из `pyproject.toml`
- использует `uv.lock`, чтобы окружение было воспроизводимым

### 3. Установить браузер для Playwright UI-тестов

```bash
uv run playwright install chromium
```

Что делает команда:
- скачивает Chromium для Playwright
- нужен для запуска UI-тестов локально и в CI
- без этого UI-тесты с `pytest-playwright` не смогут стартовать

### 4. Подготовить переменные окружения

Создай локальный `.env` на основе `.env.example`.

Пример:

```bash
cp .env.example .env
```

Что важно:
- `.env.example` хранится в репозитории
- `.env` хранит локальные секреты и не должен коммититься

## Переменные окружения

Проект использует следующие переменные:

- `SUPER_ADMIN_USERNAME`
- `SUPER_ADMIN_PASSWORD`
- `MAIL_HOST`
- `MAIL_PORT`
- `MAIL_EMAIL`
- `MAIL_PASSWORD`
- `MAIL_FOLDER`
- `RUN_MAIL_INTEGRATION`

### Для чего они нужны

- `SUPER_ADMIN_USERNAME`, `SUPER_ADMIN_PASSWORD` используются для тестов, которым нужны учетные данные супер-админа
- `MAIL_*` используются mail-слоем для подключения к IMAP-ящику
- `RUN_MAIL_INTEGRATION` включает живой integration-тест для почтового flow

## Запуск тестов

### Все тесты

```bash
uv run pytest
```

### Только API-тесты

```bash
uv run pytest tests/api/
```

### Только UI-тесты

```bash
uv run pytest tests/ui/
```

### Только mail-тесты

```bash
uv run pytest tests/mail/
```

### Конкретный тестовый файл

```bash
uv run pytest tests/api/test_post_signup_yeahub.py
```

### С подробным выводом

```bash
uv run pytest -v
```

### Запуск по pytest marks

```bash
uv run pytest -m smoke
uv run pytest -m "smoke and api"
uv run pytest -m "critical or regression"
```

### Проверка только коллекции тестов

```bash
uv run pytest --collect-only
```

Для чего это нужно:
- быстро проверить, что тесты импортируются и собираются
- полезно после изменений в инфраструктуре, зависимостях и конфиге

## Mail integration tests

Для mail-слоя используется реальный IMAP-ящик.

Сейчас в проекте как тестовый ящик удобно использовать `mailbox.org`, потому что он поддерживает IMAP и подходит для проверки `MailClient`. Если у команды появится другой рабочий IMAP-ящик, можно использовать его.

### Mail credentials

Креды для IMAP хранятся локально в `.env` и читаются через `resources/mail_creds.py`.

`resources/mail_creds.py` нужен как конфигурационный слой, чтобы не хранить секреты прямо в коде.

На текущий момент integration-тест покрывает flow письма верификации (`Verify Your Email`). Если позже появятся другие mail-flow, для них лучше добавлять отдельные тесты и отдельные описания.

Что важно:
- письмо с верификацией может попасть в спам
- письмо может вообще не дойти до тестового ящика
- integration-тест не запускается автоматически
- этот тест лучше запускать вручную, когда нужно проверить живой mail-flow
- если письмо со стенда приходит в другой ящик, его можно переслать или заново отправить на рабочий IMAP-ящик, который читает `MailClient`

Перед запуском:
1. Подготовить рабочий mailbox с IMAP-доступом
2. Убедиться, что переменные `MAIL_*` заполнены в `.env`
3. Отправить письмо верификации на этот ящик
4. Запустить integration-тест вручную

Запуск:

```bash
RUN_MAIL_INTEGRATION=1 uv run pytest tests/mail/test_mail_client_integration.py
```

Если нужно прогнать только mail-тесты:

```bash
uv run pytest tests/mail/
```

## Линтинг и форматирование

### Проверить lint-правила

```bash
uv run ruff check .
```

Для чего:
- проверяет импорты, базовые style-ошибки и другие lint-правила
- используется как обязательная проверка перед коммитом и в CI

### Проверить форматирование без изменений

```bash
uv run ruff format . --check
```

Для чего:
- показывает, соответствует ли код текущему форматированию
- полезно перед PR и в CI
- если команда падает, значит `ruff format .` хочет что-то переформатировать

### Автоматически исправить часть lint-проблем

```bash
uv run ruff check . --fix
```

Для чего:
- автоматически исправляет безопасные lint-проблемы, которые `ruff` умеет чинить сам
- удобно использовать перед коммитом

### Отформатировать весь проект

```bash
uv run ruff format .
```

Для чего:
- приводит код к единому стилю форматирования
- обычно запускается после `uv run ruff check . --fix`

### Рекомендуемый локальный порядок перед коммитом

```bash
uv run ruff check . --fix
uv run ruff format .
uv run ruff check .
uv run ruff format . --check
uv run pytest --collect-only
```

## Pre-commit

Установка git hooks:

```bash
uv run pre-commit install
```

Если hook что-то исправил автоматически:
- снова проверь изменения
- снова выполни `git add -A`

## Структура проекта

- `api/` - API-клиенты для взаимодействия с сервисом
- `mail/` - работа с IMAP-почтой, поиск verification email и удаление писем
- `models/` - Pydantic-модели ответов API
- `payloads/` - генерация и шаблоны payloads
- `resources/` - конфигурационные слои для env-переменных
- `tests/api/` - API-тесты
- `tests/auth/` - тесты auth-сценариев
- `tests/mail/` - unit и integration тесты mail-слоя
- `conftest.py` - общие pytest fixtures

## Полезные замечания

- При логине в поле `username` передается email пользователя
- Базовый URL сервиса: `https://api.yeatwork.ru/`
- Swagger UI backend: `https://api.yeatwork.ru/api#`

## Workflow для разработчика

Обычный локальный цикл работы:
1. Обновить `master`
2. Создать рабочую ветку от `master`
3. Выполнить `uv sync --python 3.14`
4. Заполнить `.env`
5. Написать или обновить тесты
6. Прогнать `ruff` и `pytest`
7. Перед PR обновить ветку через `git fetch origin` и `git merge origin/master`

## Проверки перед PR

- `uv run ruff check .`
- `uv run ruff format . --check`
- `uv run pytest`
- ветка обновлена через `merge origin/master`
- новые зависимости добавлены в `pyproject.toml` и `uv.lock`
- если менялись env-переменные, обновлен `.env.example`
- если менялся developer flow, обновлен `README.md`
