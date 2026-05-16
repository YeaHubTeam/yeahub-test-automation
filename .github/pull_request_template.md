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

UI auth smoke (Integration `scope=ui-auth` или локально):

```bash
uv run pytest tests/ui/auth/test_login_email_desktop.py::test_login_with_email_and_password_desktop \
  tests/ui/auth/test_register_verify_email_e2e.py::test_register_page_opens \
  tests/ui/settings/test_change_password_desktop.py::test_change_password_settings_desktop -v
```

Mail + forgot password ТК 115 (нужны `MAIL_*` в `.env`, `RUN_MAIL_INTEGRATION=1`):

```bash
RUN_MAIL_INTEGRATION=1 uv run pytest \
  tests/ui/auth/test_forgot_password_recovery_desktop.py::test_forgot_password_recovery_desktop -v
```

Полный mail-контур (как `scope=mail` / nightly **mail-e2e**): см. [README — CI Strategy](README.md#ci-strategy).

UI payment (нужны `VERIFIED_USER_*`):

```bash
uv run pytest tests/ui/subscription/test_subscription_payment_ui.py -v
```

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
