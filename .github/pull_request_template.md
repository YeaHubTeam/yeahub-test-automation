## Задача
`YH-123`: <вставь ссылку на задачу>

## Что сделано
- 
- 
- 

## Как проверить
- `pytest tests/path/to/tests/`
- `pytest -m "smoke and api"`
- UI auth smoke: `uv run pytest tests/ui/auth/test_login_email_desktop.py tests/ui/auth/test_register_verify_email_e2e.py::test_register_page_opens -v`
- UI payment: `uv run pytest tests/ui/subscription/test_subscription_payment_ui.py -v` (нужны `VERIFIED_USER_*`)

## Чеклист
- [ ] Линтер пройден (`ruff check .` и `ruff format --check .`)
- [ ] Релевантные тесты проходят локально
- [ ] Ветка обновлена из `origin/master`
- [ ] Обязательные pytest marks проставлены корректно
- [ ] Новые marks добавлены в pytest-конфиг (если применимо)
- [ ] Зависимости обновлены и зафиксированы (если применимо)

## Комментарий для ревьюера
- Риски/ограничения:
- Зоны фокуса в ревью:
