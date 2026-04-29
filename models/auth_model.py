import datetime
from typing import List, Optional

from pydantic import Field, field_validator

from models.base_model import BaseResponse


class AuthModel(BaseResponse):
    """
    Класс для валидации данных залогиненого пользователя
    """

    access_token: str = Field(..., description="Токен пользователя")
    user: UserModel = Field(..., description="Данные пользователя")


class PermissionsRole(BaseResponse):
    """
    Вспомогательный класс для поля permissions
    """

    id: int
    name: str


class UserRoleModel(BaseResponse):
    """
    Вспомогательный класс для поля user_role
    """

    id: int = Field(..., description="ID роли")
    name: str = Field(..., description="Название рооли")
    permissions: List[PermissionsRole]


class UserModel(BaseResponse):
    """
    Вспомогательный класс для поля User
    """

    id: str = Field(..., description="ID пользователя")
    username: str = Field(..., description="Ник пользователя")
    telegram_Username: Optional[str] = Field(
        default=None, description="Ник в телеграмм", alias="telegramUsername"
    )
    phone: Optional[str] = Field(default=None, description="Номер телефона пользователя")
    country: Optional[str] = Field(default=None, description="Страна пользователя")
    city: Optional[str] = Field(default=None, description="Город пользователя")
    email: str = Field(..., description="Email пользователя")
    birthday: Optional[str] = Field(default=None, description="Дата рождения пользователя")
    address: Optional[str] = Field(default=None, description="Адресс пользователя")
    avatar_url: Optional[str] = Field(
        default=None, description="Ссылка на аватар пользователя", alias="avatarUrl"
    )
    updated_At: datetime.datetime = Field(
        ..., description="Дата когда последний раз вносили изменения в профиль", alias="updatedAt"
    )
    created_At: datetime.datetime = Field(
        ..., description="Дата когда был создан профиль", alias="createdAt"
    )
    isVerified: bool = Field(default=False, description="Верифицировн ли пользователь")
    is_Email_Notifications_Enable: bool = Field(
        default=True,
        description="Уведомленгия по электронной почте",
        alias="isEmailNotificationsEnable",
    )
    userRoles: List[UserRoleModel]
