import datetime

from pydantic import Field

from models.base_model import BaseResponse
from models.role_model import Role


class UserModel(BaseResponse):
    """
    Вспомогательный класс для поля User
    """

    id: str = Field(..., description="ID пользователя")
    username: str = Field(..., description="Ник пользователя")
    telegram_username: str | None = Field(default=None, description="Ник в телеграмм")
    phone: str | None = Field(default=None, description="Номер телефона пользователя")
    country: str | None = Field(default=None, description="Страна пользователя")
    city: str | None = Field(default=None, description="Город пользователя")
    email: str = Field(..., description="Email пользователя")
    birthday: datetime.date | None = Field(default=None, description="Дата рождения пользователя")
    address: str | None = Field(default=None, description="Адрес пользователя")
    avatar_url: str | None = Field(default=None, description="Ссылка на аватар пользователя")
    updated_at: datetime.datetime = Field(
        ..., description="Дата когда последний раз вносили изменения в профиль"
    )
    created_at: datetime.datetime = Field(..., description="Дата когда был создан профиль")
    is_verified: bool = Field(default=False, description="Верифицирован ли пользователь")
    is_email_notifications_enable: bool = Field(
        default=True, description="Уведомления по электронной почте"
    )
    user_roles: list[Role]

    # NOTE: AuthModel (обёртка access_token/user поверх этого класса) удалена —
    # не имела alias на access_token (сервер отдаёт accessToken) и не использовалась
    # ни в одном тесте. Актуальный контракт логина — models.user_response_model.LoginResponse.
