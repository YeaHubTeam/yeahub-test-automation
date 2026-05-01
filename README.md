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

- `VERIFIED_USER_EMAIL`
- `VERIFIED_USER_PASSWORD`
- `MAIL_HOST`
- `MAIL_PORT`
- `MAIL_EMAIL`
- `MAIL_PASSWORD`
- `MAIL_FOLDER`
- `RUN_MAIL_INTEGRATION`

### Для чего они нужны

- `VERIFIED_USER_EMAIL`, `VERIFIED_USER_PASSWORD` используются фикстурой `static_user` для subscription/payment integration-тестов
- `MAIL_*` используются mail-слоем для подключения к IMAP-ящику
- `RUN_MAIL_INTEGRATION` включает живой integration-тест для почтового flow

## Запуск тестов

Основные команды:

```bash
uv run pytest
uv run pytest tests/api/
uv run pytest tests/ui/
uv run pytest tests/mail/
uv run pytest tests/api/test_post_signup_yeahub.py
uv run pytest -v
uv run pytest -m smoke
uv run pytest -m "smoke and api"
uv run pytest -m "critical or regression"
uv run pytest -m "unit or pr_safe"
uv run pytest -m "smoke and integration"
uv run pytest -m "integration"
uv run pytest --collect-only
```

`uv run pytest --collect-only` полезен для быстрой проверки импорта и коллекции тестов после изменений в инфраструктуре, зависимостях и конфиге.

## CI Strategy

В проекте используется 2 CI-контура.

`Fast CI` — `.github/workflows/ci.yml`
- запускается автоматически на `push` и `pull_request`
- проверяет `ruff check .`, `ruff format . --check`, preflight API healthcheck (`/subscriptions` + доступность `/auth/refresh`) и `pytest -m "unit or pr_safe"`
- `Allure` для этого контура не используется, чтобы PR-пайплайн оставался быстрым и простым

`Integration CI` — `.github/workflows/integration.yml`
- запускается вручную через `Actions -> Integration (Live) -> Run workflow`
- запускается автоматически ночью по `schedule`
- `scope=smoke` запускает `pytest -m "smoke and integration"`
- `scope=full` и nightly запускают `pytest -m "integration"`
- перед тестами выполняется preflight API healthcheck (`/subscriptions` + доступность `/auth/refresh`)
- после каждого manual/nightly run сохраняются artifacts `allure-results-<run_number>` и `allure-report-<run_number>`

Для `Integration CI` в GitHub Actions должны быть заведены repository secrets:
- `VERIFIED_USER_EMAIL`
- `VERIFIED_USER_PASSWORD`

Artifacts доступны на странице конкретного workflow run в GitHub Actions.

## Markers Guide

Базовые маркеры:

- `unit` - изолированные тесты без зависимости от удаленного стенда
- `pr_safe` - стабильные тесты, разрешенные для запуска в PR-контуре
- `api` - HTTP/API сценарии
- `ui` - браузерные UI сценарии
- `integration` - тесты, которые зависят от реального внешнего окружения: удаленный стенд, почта, платежка, браузерный live-flow
- `smoke` - короткий критичный набор сценариев
- `regression` - более широкий регрессионный набор
- `critical` - сценарии высокого приоритета, если нужен отдельный запуск по приоритету

Комбинации, которые реально используются:

- `smoke and integration` - live smoke на реальном стенде
- `integration` - полный live integration контур
- `unit or pr_safe` - стабильный контур для Fast CI

Важно:
- `smoke` и `integration` не исключают друг друга
- если тест ходит в удаленный стенд, он считается `integration`, даже если это тестовый, а не production контур
- `pr_safe` может пересекаться с `integration`, но такие тесты добавляются в Fast CI только после стабильного baseline-прогона
- для известных backend-багов используется строгий `xfail`: если баг исправлен и тест неожиданно проходит, CI должен подсветить это как сигнал снять `xfail`

## Mail integration tests

Для mail-слоя используется реальный IMAP-ящик. Сейчас подходит `mailbox.org`, но можно использовать любой рабочий IMAP-ящик. Креды хранятся локально в `.env` и читаются через `resources/mail_creds.py`.

Mail integration сейчас покрывает flow письма верификации `Verify Your Email`.

Ограничения:
- письмо с верификацией может попасть в спам
- письмо может вообще не дойти до тестового ящика
- integration-тест не запускается автоматически
- такой тест лучше использовать как ручную live-проверку
- mail credentials сейчас не прокидываются в GitHub Actions: до появления постоянного рабочего mailbox mail flow остается локальным ручным сценарием через `.env`

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

### Проверить форматирование без изменений

```bash
uv run ruff format . --check
```

### Автоматически исправить часть lint-проблем

```bash
uv run ruff check . --fix
```

### Отформатировать весь проект

```bash
uv run ruff format .
```

### Рекомендуемый локальный порядок перед коммитом

```bash
uv run ruff check . --fix
uv run ruff format .
uv run ruff check .
uv run ruff format . --check
uv run pytest --collect-only
```

## Pre-commit

### Установка pre-commit hooks

Важно:
- `pre-commit` hooks не устанавливаются автоматически ни через `git pull`, ни через `uv sync`
- после первого клонирования репозитория hooks нужно установить вручную

```bash
uv run pre-commit install
```

Если hook что-то исправил автоматически:
- проверь изменения
- выполни `git add -A`

Полезные команды:

```bash
uv run pre-commit run --all-files
uv run pre-commit autoupdate
uv sync --python 3.14
uv run pre-commit run --all-files
```

`pre-commit` проверяет и форматирует код до коммита. В CI эти же базовые проверки дублируются шагами `ruff check` и `ruff format --check`.

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
- `uv run pytest -m "unit or pr_safe"`
- для расширения `pr_safe` прогнать `unit or pr_safe` несколько раз подряд и зафиксировать baseline
- при изменениях в live-контуре дополнительно прогнать `smoke and integration` вручную
- ветка обновлена через `merge origin/master`
- новые зависимости добавлены в `pyproject.toml` и `uv.lock`
- если менялись env-переменные, обновлен `.env.example`
- если менялся developer flow, обновлен `README.md`
