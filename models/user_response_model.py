import datetime
from typing import List, Optional

from pydantic import ConfigDict, EmailStr, Field, HttpUrl, field_validator

from models.base_model import BaseResponse


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
    avatarUrl: HttpUrl
    refId: Optional[str] = None


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
    email: EmailStr
    birthday: datetime.date
    address: str
    avatarUrl: str
    telegramUsername: Optional[str] = None
    createdAt: datetime.datetime = Field(alias="createdAt")
    updatedAt: datetime.datetime = Field(alias="updatedAt")
    userRoles: Optional[List[UserRole]] = None
    isVerified: Optional[bool] = None
    isEmailNotificationsEnable: Optional[bool] = None
    profiles: List[Profiles]
    subscriptions: Optional[list] = None


class CreatedUserResponse(BaseResponse):
    access_token: str
    user: UserResponse
