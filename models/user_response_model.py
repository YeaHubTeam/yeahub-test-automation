from pydantic import field_validator,Field, ConfigDict, HttpUrl
from typing import Optional, List
from models.base_model import BaseResponse
import datetime


class TestUser(BaseResponse):
    """Модель валидации исходящих данных случайного пользователя"""
    username: str
    password: str
    email: str
    phone: str
    country: str
    city: str
    birthday: datetime.date
    address: str
    avatarUrl: HttpUrl
    refId: Optional[str] = None

    @field_validator("email")
    def check_email(cls, value: str, info) -> str:
        # Проверяем, совпадение паролей
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Пароли не совпадают")
        return value


class Permission(BaseResponse):
    id: int
    name: str

class UserRole(BaseResponse):
    id: int
    name: str
    permissions: List[Permission]

class Profiles(BaseResponse):
    id: str
    profileType: int
    specializationId: Optional[int] = None
    markingWeight: int
    description: Optional[str] = None
    socialNetwork: Optional[str] = None
    image_src: Optional[str] = None
    isActive: Optional[bool] = None
    profileSkills: Optional[list] = None
    ratingPoints: Optional[int] = None

class UserResponse(BaseResponse):
    """Модель валидации ответа созданного пользователя"""
    id: str
    username: str
    phone: str
    country: str
    city: str
    email:str
    birthday: datetime.date
    address: str
    avatarUrl: str
    telegramUsername: Optional[bool] = None
    createdAt: datetime.datetime = Field(alias='createdAt')
    updatedAt: datetime.datetime = Field(alias='updatedAt')
    userRoles: Optional[List[UserRole]] = None
    isVerified: Optional[bool] = None
    isEmailNotificationsEnable: Optional[bool] = None
    profiles: List[Profiles]
    subscriptions: Optional[list] = None


    model_config = ConfigDict(
        extra='forbid',
        populate_by_name=True,
        from_attributes=True,
        strict=False
    )

class CreatedUserResponse(BaseResponse):
    access_token: str
    user: UserResponse


