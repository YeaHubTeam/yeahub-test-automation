# AGENTS.ru.md - YeaHub Test Automation

Версия: 1.2
Обновлено: 2026-06-28
Язык: Русский (поясняющий)

Если английская и русская версии отличаются, приоритет у `AGENTS.md` (English).

## 1) Миссия
Этот репозиторий содержит автотесты для YeaHub (API и UI).
Основные цели:
- надежные и стабильные прогоны
- понятный и поддерживаемый тестовый код
- быстрый и предсказуемый фидбек в PR

## 2) Технологический стек (источник истины)
- Python: `>=3.14,<3.15`
- Тестовый фреймворк: `pytest`
- API: `requests`, `pydantic`
- UI: `pytest-playwright`
- Отчетность: `allure-pytest`
- Линт/форматирование: `ruff`, `pre-commit`

## 3) Рабочие правила для AI-агента
При выполнении задач агент всегда:
1. Следует существующим паттернам проекта (fixtures, api manager, models, utils).
2. Делает минимальный и целевой diff.
3. Не добавляет зависимости без строгой необходимости и обоснования.
4. Сначала запускает релевантные проверки на узком скоупе, затем шире при необходимости.
5. Соблюдает DRY, KISS, PEP 8 и принцип единственной ответственности.
6. Добавляет или обновляет тесты для ключевых веток и регрессий.
7. Предпочитает детерминированные проверки вместо flaky-ожиданий.
8. Перед изменением общих хелперов (`tests/mail/`, `conftest.py`, page objects из нескольких сьютов) — **пройти всех callers** и краевые случаи (последняя попытка retry, отсутствие env, teardown).
9. Если фикстура или хелпер получает новые **внешние prerequisites** (IMAP, live API, secrets) — для integration-тестов использовать **`pytest.skip` / `skipif` с понятной причиной**, а не голый `assert` в setup (кроме явно unit-only тестов).
10. **Breaking changes** в контракте фикстур или требованиях к env документировать в `README.md` (CI Strategy + секция теста), а не только в тексте PR.

## 4) Правила Git и веток
Формат имени ветки:
`<тип>/<TRACKER-ID>-<краткое-описание>`

Типы:
- `feature/` - новая функциональность или новые тесты
- `fix/` - исправления багов
- `refactor/` - рефакторинг
- `docs/` - документация

Если задачи в трекере нет, использовать `YH-XXX` и запросить создание задачи у лида.

Формат коммита:
`<TRACKER-ID>: <описание на английском>`

Примеры:
- `YH-123: Add login API smoke tests`
- `YH-456: Fix flaky login UI test`

Перед PR и перед финальным merge:
1. `git fetch origin`
2. `git merge origin/master`
3. Разрешить конфликты при наличии
4. Запушить обновления ветки

## 5) Definition of Done для PR
Перед созданием PR проверить:
- линтер проходит
- релевантные тесты проходят локально
- ветка обновлена из `origin/master`
- новые зависимости зафиксированы и задокументированы
- pytest marks проставлены корректно
- новые marks зарегистрированы в pytest-конфиге

В описании PR обязательно:
- ссылка на задачу
- краткий список изменений
- как проверить (точная команда `pytest`)
- новые или изменённые **env prerequisites** (`MAIL_*`, `RUN_MAIL_INTEGRATION`, secrets), если применимо

## 6) Политика pytest marks
Обязательный базовый набор:
1. У каждого теста должен быть явный маркер типа теста (например: `api`, `ui`, `unit`, `integration`, `db`).
2. Для продуктовых API/UI тестов обязателен маркер области: `@pytest.mark.api` или `@pytest.mark.ui`.
3. Для каждого теста по возможности указывать маркер приоритета: `@pytest.mark.smoke` или `@pytest.mark.critical` или `@pytest.mark.regression`.

Опциональные marks по необходимости:
- `slow`
- `negative`
- `integration`
- `db`
- `pr_safe`
- `healthcheck`

## 7) Стандарты дизайна тестов
- Один тест проверяет одно четкое поведение.
- Использовать понятную структуру Arrange / Act / Assert.
- Setup и teardown по возможности выносить в fixtures.
- Тестовые данные делать явными и воспроизводимыми.
- Assertions должны понятно объяснять причину падения.
- Для известных багов backend оставлять TODO со ссылкой на задачу.

### Prerequisites для integration (по всему проекту)
- **Live mail / IMAP** (`MAIL_HOST`, `MAIL_EMAIL`, `MAIL_PASSWORD`, опционально `MAIL_FOLDER`, `MAIL_PORT`): нужны для mail e2e, subscription/payment с verified user через IMAP, фикстур `verified_registered_user`, `verified_subscription_user` и mail-набора в CI `scope=mail`.
- **`RUN_MAIL_INTEGRATION=1`**: включает явные live mail e2e (см. mail/UI тесты с `skipif`); subscription API в CI использует secrets `MAIL_*` без этого флага.
- **Skip vs fail**: без кредов локально integration-тесты должны **skip** с понятным сообщением (паттерн: `tests/mail/test_mail_client_integration.py`, `require_mail_creds` + `skipif` где уместно) — не падать в середине фикстуры с неочевидным assert.
- **CI**: secrets Integration workflow описаны в README CI Strategy; не предполагать, что локальный `.env` совпадает с CI.

### Общие хелперы retry и polling
- **Retry callbacks** (`on_retry`, обновление identity): вызывать только при `attempt < max_attempts - 1`. На **последней** неуспешной попытке не регенерировать users/emails/tags.
- **Polling / settle-after-wait**: если повторный fetch может упасть (например IMAP `find_message` после `wait_for_message`) — обернуть в `try/except` и **сохранить первый успешный результат**, чтобы гонка не роняла всю цепочку.
- После изменения retry/polling — grep по callers (`register_user_with_retries`, `wait_imap_verification_link`, фикстуры в `conftest.py`).

## 8) Learning Mode (рост команды)
AI-агент должен работать как senior-ментор:
- объяснять, почему внесены изменения, а не только что изменено
- предлагать более простой путь, если решение избыточно сложное
- отмечать 1-2 практики индустрии для существенных задач
- избегать оверинжиниринга и длинной теории

## 9) Ограничения по безопасности и стабильности
- Никогда не коммитить секреты, токены и реальные креды.
- Использовать переменные окружения и локальный `.env`-процесс.
- Не выполнять destructive git-операции без явного запроса.
- Не изменять нерелевантные файлы.

## 10) Стиль коммуникации
- кратко и по делу
- пошаговые команды, когда это полезно
- ответы в формате чеклистов для исполнения
- фокус на надежной доставке автотестов

## 11) Политика согласования изменений
- По умолчанию не изменять файлы без явного подтверждения пользователя.
- Сначала дать анализ и предложенный план изменений (или краткое описание diff), затем запросить подтверждение.
- Вносить правки только после четкого ответа "да".
- Исключение: очень маленькие low-risk правки (до 1-2 файлов) можно вносить сразу только если пользователь явно просит делать напрямую.

## 12) Task intake (перед кодом)

Перед нетривиальной задачей уточнить (с пользователем при необходимости):
1. **Done means** — какие тесты/scopes должны быть зелёными (Fast CI, Integration `scope=…`, локальные команды).
2. **Prerequisites** — `MAIL_*`, `RUN_MAIL_INTEGRATION`, Playwright, secrets; что должно **skip**, а что **fail** без них.
3. **Blast radius** — какие фикстуры, workflows и секции README затронуты.
4. **Breaking changes** — например замена static creds на ephemeral/IMAP; задокументировать в README.

Если пользователь не уточнил — вывести из тикета и озвучить допущения до большого diff.

## 13) Чеклист pre-commit / pre-PR (агент)

Запускать, когда пользователь просит **commit**, открыть **PR** или пишет **«готово к коммиту»**, если явно не попросил пропустить проверки.

1. **Scope** — `git diff` / изменённые пути; перечислить области (ui-auth, mail, subscription, `pages/`, CI, docs).
2. **Caller impact** — при правках `tests/mail/`, `conftest.py`, общих `pages/`, workflows: grep callers; проверить последнюю попытку retry и пути без env.
3. **Lint** — `uv run ruff check .` и `uv run ruff format . --check` на затронутых путях (весь репо, если diff небольшой).
4. **Tests** (минимум по области; см. README «Проверки перед PR»):
   - UI auth / interview / `onboarding_modal` → те же пути, что `run_ui_auth_smoke` в `.github/workflows/integration.yml`.
   - Правки `onboarding_modal` или специализации → также mail `test_register_and_verify_email_e2e` при `RUN_MAIL_INTEGRATION=1`, если возможно.
   - Mail / IMAP хелперы или ТК 422/466/115/52 → quartet `scope=mail` или подмножество из README.
   - Subscription API/UI / фикстуры `verified_*` → `tests/api/subscription/` и/или `tests/ui/subscription/` с `MAIL_*` по документации.
   - Только unit / `pr_safe` → `pytest -m "unit or pr_safe"`.
5. **Local without secrets** — для env-зависимых тестов: убедиться в **skip** с понятной причиной (или явно задокументировать необходимость mail); не опираться только на зелёный CI.
6. **Docs** — при изменении CI scopes, имён тестов, `externalId`, контрактов фикстур или env → обновить `README.md` (CI Strategy + секция теста).
7. **Lead-style self-review** — перед PR: семантика retry, skip vs assert, defensive fallbacks в хелперах, README для новых prerequisites, без лишнего diff.
8. **Git** — ветка `type/TRACKER-id-description`; коммит `TRACKER: English summary`; напомнить `git fetch origin` + `git merge origin/master` перед PR.
9. **Report** — итог pass/fail, выполненные команды, пропущенные live-прогоны. **Не** делать `git commit`, если пользователь явно не просил.

Если live pytest в среде агента недоступен (например нет браузеров Playwright) — явно указать это и дать точные команды для локального запуска.
