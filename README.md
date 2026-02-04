# YeaHub Test Automation

Фреймворк для автоматизированного тестирования REST API сервиса YeaHub.

## Описание

Проект содержит автоматизированные тесты для проверки функциональности API, включая:
- Регистрацию и аутентификацию пользователей
- Управление профилем
- Сброс и смену пароля
- Верификацию email

## Установка

```bash
# Создать и активировать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Установить зависимости
pip install -r requirements.txt
```

## Запуск тестов

```bash
# Все тесты
pytest tests/api/

# Конкретный тест
pytest tests/api/test_post_signup_yeahub.py

# С подробным выводом
pytest tests/api/ -v
```

## Структура

- `api/` - API клиенты для взаимодействия с сервисом
- `tests/api/` - Автоматизированные тесты
- `constants/` - Константы и конфигурация
- `conftest.py` - Pytest фикстуры

## API Base URL

`https://api.yeatwork.ru/`

## Использование линтера
- `ruff check .` - Покажет все ошибки
- `ruff check . --fix` - Линтинг + автофикс
- `ruff format . --diff` - Показывает что будет форматировать
- `ruff format .` - Форматирование всего
- `ruff check . --output-format full`  - Детальный отчет

Автоиспользование перед коммитом:
- `pre-commit install` - Автофикс и форматирование автоматически перед коммитом
- Если при попытке коммита он находит и исправляет ошибки, надо снова делать git add .

## Особенности

⚠️ При логине в поле `username` передается email пользователя

