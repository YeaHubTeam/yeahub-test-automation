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
- опционально (повторная регистрация на тот же email после удаления): переопределение дефолтов через `REGISTER_SAME_EMAIL_*` — см. `tests/ui/flows/same_email_retry_config.py` и комментарии в `.env.example`

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
- запускается автоматически ночью по `schedule` (основной job + отдельный **mail-e2e**)
- `scope=smoke` запускает `pytest -m "smoke and integration and not ui"` (без Playwright UI)
- `scope=full` и ночной прогон (`schedule`) основного job: `pytest -m "integration and not ui"`, затем UI auth smoke (login ТК 409, register page, смена пароля ТК 113) и UI payment (если заданы `VERIFIED_USER_*`)
- `scope=ui-auth`: Playwright auth/settings smoke — `test_login_email_desktop` (ТК 409), `test_register_page_opens`, `test_change_password_settings_desktop` (ТК 113; `registered_user`, без IMAP) (`--testit`, `APP_BASE_URL` по умолчанию `https://app.yeatwork.ru`)
- `scope=ui-payment`: Playwright `tests/ui/subscription/test_subscription_payment_ui.py` (нужны secrets `VERIFIED_USER_EMAIL`, `VERIFIED_USER_PASSWORD`)
- `scope=mail`: API `test_email_verification_e2e` + Playwright `test_register_and_verify_email_e2e` + онбординг `test_onboarding_full_flow_e2e` с `RUN_MAIL_INTEGRATION=1`, `--testit`, `APP_BASE_URL` по умолчанию `https://app.yeatwork.ru` (тайминги same-email для регистрационного e2e — дефолты в коде, как при локальном запуске)
- ночной job **mail-e2e** (только `schedule`): те же три теста, что и при `scope=mail`, плюс `MAIL_*` secrets и установка Chromium для Playwright
- перед тестами выполняется preflight API healthcheck (`/subscriptions` + доступность `/auth/refresh`)
- после каждого manual/nightly run сохраняются artifacts `allure-results-<run_number>` и `allure-report-<run_number>`

Для `Integration CI` в GitHub Actions должны быть заведены repository secrets:
- `VERIFIED_USER_EMAIL`
- `VERIFIED_USER_PASSWORD`
- для mail / nightly mail-e2e: `MAIL_HOST`, `MAIL_PORT`, `MAIL_EMAIL`, `MAIL_PASSWORD`, `MAIL_FOLDER` (и при использовании Test IT — `TMS_*`, см. workflow)

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
- явные пути UI в Integration CI (`scope=ui-auth`, `scope=ui-payment`, ночной `schedule`, `scope=full`) — не через `-m ui`, чтобы не затянуть mail e2e и нестабильные сценарии

Важно:
- `smoke` и `integration` не исключают друг друга
- если тест ходит в удаленный стенд, он считается `integration`, даже если это тестовый, а не production контур
- `pr_safe` может пересекаться с `integration`, но такие тесты добавляются в Fast CI только после стабильного baseline-прогона
- для известных backend-багов используется строгий `xfail`: если баг исправлен и тест неожиданно проходит, CI должен подсветить это как сигнал снять `xfail`

## Mail integration tests

Для mail-слоя используется реальный IMAP-ящик (например, Яндекс.Почта или любой другой провайдер с IMAP). Креды хранятся локально в `.env` и читаются через `resources/mail_creds.py`.

Ограничения:
- письмо с верификацией может попасть в спам
- письмо может вообще не дойти до тестового ящика
- integration-тест не запускается автоматически
- такой тест лучше использовать как ручную live-проверку
- для CI mail flow: nightly job **mail-e2e** и manual `scope=mail` в Integration workflow (нужны secrets `MAIL_*`); локально — `.env` и `RUN_MAIL_INTEGRATION=1`

### Smoke: проверка IMAP-клиента и парсинга ссылки

Тест проверяет, что:
- IMAP логин работает
- письмо с темой `Verify Your Email` находится
- ссылка `/auth/verify-email?token=...` извлекается
- письмо можно удалить (чтобы ящик не разрастался)

Важно:
- `.env` содержит секреты и **не должен коммититься**
- smoke-тест **не отправляет** письмо сам — он предполагает, что в ящике уже есть письмо верификации

Запуск smoke:

```bash
RUN_MAIL_INTEGRATION=1 uv run pytest tests/mail/test_mail_client_integration.py
```

### E2E верификация email через IMAP (registration → email → verify-email)

В репозитории есть live e2e тест, который проверяет полный backend-flow:
1) регистрация пользователя на email вида `verify-test+<tag>@domain`  
2) `GET /auth/send-verification-email/{user_id}` (с учётом rate limit)  
3) IMAP: ожидание письма `Verify Your Email` и извлечение ссылки `/auth/verify-email?token=...`  
4) `GET /auth/verify-email?token=...`  
5) `GET /auth/profile` → `isVerified=true`

Тест помечен как `integration` и запускается только при `RUN_MAIL_INTEGRATION=1`.

Перед запуском:
- заполнить `MAIL_HOST/MAIL_PORT/MAIL_EMAIL/MAIL_PASSWORD/MAIL_FOLDER` в `.env`
- убедиться, что в почте включён IMAP и используется правильный способ авторизации

Пример для Яндекс.Почты:
- IMAP сервер: `imap.yandex.ru`, порт `993`, папка `INBOX`
- в настройках ящика включить IMAP
- в Яндекс ID создать **пароль приложения** для “Почта / IMAP POP3 SMTP” и использовать его как `MAIL_PASSWORD`

Минимальный пример `MAIL_*`:

```bash
MAIL_HOST=imap.yandex.ru
MAIL_PORT=993
MAIL_FOLDER=INBOX
MAIL_EMAIL=verify-test@yeahub.ru
MAIL_PASSWORD=<app_password>
```

Примечание:
- письмо может приходить с задержкой (обычно до 1–3 минут) — тест e2e умеет ждать письмо с polling
- backend может ограничивать частоту отправки verification email (например, не чаще ~1 раза в 60 секунд) — тест e2e умеет ждать и повторять отправку
- после извлечения ссылки тест удаляет письмо из ящика, чтобы следующий прогон не цеплял старые письма

Запуск e2e (API-контур, без браузера):

```bash
RUN_MAIL_INTEGRATION=1 uv run pytest -q tests/auth/test_auth_verify_email_e2e.py -m "not ui"
```

### UI E2E (Playwright): вход по email и паролю (desktop, ТК 409)

Автотест `tests/ui/auth/test_login_email_desktop.py` — ручной кейс [409](https://team-vz1y.testit.software/browse/409), **шаги 1–4**: форма `/auth/login`, ввод email/пароля, «Вход», переход на `/interview`. Пользователь создаётся через API (`registered_user`), в teardown удаляется (`delete_user`). Постусловие «Выйти» через UI в этом тесте **не** автоматизировано (см. onboarding e2e / `tests/auth/test_auth_logout.py`).

Локальный запуск:

```bash
uv run pytest tests/ui/auth/test_login_email_desktop.py::test_login_with_email_and_password_desktop -v
```

С браузером: `--headed`. Test IT: `--testit` и `TMS_*` в `.env` (см. `pyproject.toml`, `[testit]`). `externalId` в коде: `yeahub-ui-auth-login-email-password-desktop-409`.

CI (Integration workflow, scope `ui-auth` или ночной `schedule` / `scope=full` после API): см. [CI Strategy](#ci-strategy).

В том же scope `ui-auth` дополнительно гоняется лёгкий smoke «открылась страница регистрации»:

```bash
uv run pytest tests/ui/auth/test_register_verify_email_e2e.py::test_register_page_opens -v
```

### UI E2E (Playwright): смена пароля в настройках (desktop, ТК 113)

Автотест `tests/ui/settings/test_change_password_desktop.py` — [113](https://team-vz1y.testit.software/browse/113): `/settings#change-password`, смена пароля, logout, вход с новым паролем. Пользователь: API `registered_user` (верификация email **не** требуется), teardown — `delete_user` с актуальным паролем.

```bash
uv run pytest tests/ui/settings/test_change_password_desktop.py::test_change_password_settings_desktop -v
```

С браузером: `--headed`. Test IT: `--testit`, `externalId`: `yeahub-ui-settings-change-password-desktop-113`. CI: тот же `scope=ui-auth`, что login 409.

### UI E2E (Playwright): оплата подписки (T-Bank)

`tests/ui/subscription/test_subscription_payment_ui.py` — UI оплаты по ссылке из API (`static_user` / `VERIFIED_USER_*` в secrets).

```bash
uv run pytest tests/ui/subscription/test_subscription_payment_ui.py -v
```

CI: Integration workflow, scope `ui-payment` (или ночной `schedule` / `scope=full` после auth smoke, если заданы `VERIFIED_USER_*`).

### UI E2E (Playwright): регистрация в браузере → IMAP → онбординг → удаление → опционально тот же email

Отдельный сценарий в `tests/ui/auth/test_register_verify_email_e2e.py`: форма на `/auth/register`, реальный ящик для письма верификации, затем UI-онбординг, удаление аккаунта в настройках и при необходимости вторая регистрация на тот же адрес (дефолтные тайминги и API-probe — в `tests/ui/flows/same_email_retry_config.py` и `tests/mail/verification_flow.py`; при необходимости переопредели `REGISTER_SAME_EMAIL_*` в `.env` — бэкенд может отвечать `user.user.email.limited_period`).

Пример локального запуска:

```bash
RUN_MAIL_INTEGRATION=1 uv run pytest tests/ui/auth/test_register_verify_email_e2e.py::test_register_and_verify_email_e2e -v
```

С браузером на экране: добавь `--headed`. Отчёт в Test IT: добавь `--testit` и задай `TMS_*` в `.env` (см. `pyproject.toml`, секция `[testit]`). Поле **`@testit.externalId`** в тесте должно **точно совпадать** с «Внешним ID» существующего автотеста в библиотеке TMS (часто это длинная hex-строка); иначе адаптер не попадёт в нужную запись при `automaticCreationTestCases=false`.

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
