## Задача
`YH-123`: <вставь ссылку на задачу>

## Что сделано
- 
- 
- 

## Как проверить

Fast CI (обязательно для PR):

```bash
uv run ruff check .
uv run ruff format . --check
uv run pytest -m "unit or pr_safe"
```

UI auth smoke (Integration `scope=ui-auth` или локально; **`MAIL_*` не нужны**):

```bash
export APP_BASE_URL="${APP_BASE_URL:-https://app.yeatwork.ru}"
uv run pytest tests/ui/auth/test_login_email_desktop.py::test_login_with_email_and_password_desktop \
  tests/ui/auth/test_register_form_desktop.py::test_register_form_desktop \
  tests/ui/interview/test_onboarding_flow_e2e.py::test_onboarding_after_register_desktop \
  tests/ui/auth/test_register_verify_email_e2e.py::test_register_page_opens \
  tests/ui/settings/test_change_password_desktop.py::test_change_password_settings_desktop \
  tests/ui/settings/test_delete_account_desktop.py::test_delete_account_from_settings_desktop -v
```

Mail (нужны `MAIL_*` в `.env`, `RUN_MAIL_INTEGRATION=1`):

```bash
# ТК 422 — email verify в settings (~1.5–2 min)
RUN_MAIL_INTEGRATION=1 uv run pytest \
  tests/ui/auth/test_email_verify_desktop.py::test_email_verify_registered_user_desktop -v

# ТК 115 — forgot password
RUN_MAIL_INTEGRATION=1 uv run pytest \
  tests/ui/auth/test_forgot_password_recovery_desktop.py::test_forgot_password_recovery_desktop -v
```

Полный mail-контур (как `scope=mail` / nightly **mail-e2e**): см. [README — Проверки перед PR](README.md#проверки-перед-pr) и [CI Strategy](README.md#ci-strategy).

UI payment — API link (`VERIFIED_USER_*` в `.env` или secrets):

```bash
uv run pytest tests/ui/subscription/test_subscription_payment_ui.py -v
```

UI payment — ТК 116, полный checkout (`MAIL_*` в `.env`, `RUN_MAIL_INTEGRATION=1`):

```bash
RUN_MAIL_INTEGRATION=1 uv run pytest tests/ui/subscription/test_subscription_tariff_card_desktop.py -v
```

На stage с заглушкой тарифов ожидай **SKIPPED** (runtime skip, TODO YH-2137 в `select_tariff_page.py`).

Integration CI до PR: push ветки → `Actions → Integration (Live) → Run workflow` → выбрать ветку → `scope=ui-payment` / `scope=mail`.

Integration `scope=ui-payment`: нужны оба набора — `VERIFIED_USER_*` и `MAIL_*`; payment и TC 116 в **одном** `pytest`.

## Чеклист
- [ ] Линтер пройден (`ruff check .` и `ruff format --check .`)
- [ ] Релевантные тесты проходят локально
- [ ] Ветка обновлена из `origin/master`
- [ ] Обязательные pytest marks проставлены корректно
- [ ] Новые marks добавлены в pytest-конфиг (если применимо)
- [ ] Зависимости обновлены и зафиксированы (если применимо)
- [ ] При изменениях env — обновлён `.env.example`; при изменении CI/docs — `README.md`

## Комментарий для ревьюера
- Риски/ограничения:
- Зоны фокуса в ревью:
