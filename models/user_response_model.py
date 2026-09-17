import datetime

from pydantic import EmailStr, Field, HttpUrl

from models.base_model import BaseResponse
from models.role_model import Role


class TestUser(BaseResponse):
    """Модель валидации исходящих данных случайного пользователя"""

    username: str
    password: str
    email: EmailStr
    phone: str
    country: str
    city: str
    birthday: datetime.date
    address: str
    avatar_url: HttpUrl
    ref_id: str | None = None


class Profiles(BaseResponse):
    id: str
    profile_type: int
    specialization_id: int | None = None
    marking_weight: int
    description: str | None = None
    social_network: str | None = None
    image_src: str | None = None
    is_active: bool | None = None
    profile_skills: list | None = None
    rating_points: int | None = None


class UserCoreFields(BaseResponse):
    """
    Общие поля пользователя, единые для всех auth/profile-эндпоинтов.
    Конкретные эндпоинты дополняют или сужают этот набор в сабклассах ниже —
    см. таблицу отличий по контрактам в комментариях к каждому классу.
    """

    id: str
    username: str
    email: EmailStr
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    birthday: datetime.date | None = None
    address: str | None = None
    avatar_url: str | None = None
    telegram_username: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_email_notifications_enable: bool | None = None


class SignUpUserResponse(UserCoreFields):
    """
    Ответ на POST /auth/signUp.
    Сервер на этом этапе ещё не назначает роли и verified-статус,
    поэтому в отличие от остальных вариантов их тут нет.
    """


class LoginUserResponse(UserCoreFields):
    """Ответ на POST /auth/login"""

    user_roles: list[Role]
    is_verified: bool


class BaseRefreshTokenResponse(UserCoreFields):
    """Ответ на GET /auth/refresh"""

    user_roles: list[Role]
    is_verified: bool


class UserResponse(UserCoreFields):
    """
    Ответ на GET /auth/profile.
    Самый полный контракт — включает профили и подписки, которых нет
    в других auth-ответах.
    """

    user_roles: list[Role] | None = Field(default=None)
    is_verified: bool | None = None
    profiles: list[Profiles] | None = None
    subscriptions: list | None = None


class SignUpResponse(BaseResponse):
    access_token: str
    user: SignUpUserResponse


class LoginResponse(BaseResponse):
    access_token: str
    user: LoginUserResponse


class RefreshTokenResponse(BaseResponse):
    access_token: str
    user: BaseRefreshTokenResponse

# NOTE: CreatedUserResponse (access_token + UserResponse) удалена как неиспользуемый
# дубль SignUpResponse — вызовов вне объявления класса не найдено. Если найдётся
# реальный usage — восстановить и разобраться, какой эндпоинт она валидирует.