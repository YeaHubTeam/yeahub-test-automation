from pydantic import Field

from models.base_model import BaseResponse


class ModelErrorResponse(BaseResponse):
    """
    Класс для валидации бизнес-ошибок API (формат {message, statusCode, description}).

    Встречается на разных доменах — auth (auth.user.verified),
    subscriptions (subscription.subscription.not_found), payment (tbank api error) —
    поэтому вынесена из Subscriptions в общие модели.

    TODO: сервер также возвращает другой формат ошибок для class-validator
    (400 Bad Request от NestJS): {"message": [...список строк...], "error": "...",
    "statusCode": ...} — без поля description, message это list[str], а не str.
    Например password-change с невалидным паролем отдаёт именно такой формат.
    Эта модель его не покрывает; понадобится отдельная ValidationErrorResponse,
    если появится тест, валидирующий подобный ответ через pydantic.
    """

    message: str = Field(..., description="Сообщение об ошибке")
    status_code: int = Field(..., description="Статус код")
    description: str = Field(..., description="Описание ошибки")