import datetime
from typing import List, Optional

from models.base_model import BaseResponse


class Permission(BaseResponse):
    id: int
    name: str


class UserRole(BaseResponse):
    id: int
    name: str
    permissions: List[Permission]


class BaseRefreshTokenResponse(BaseResponse):
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    birthday: Optional[datetime.date] = None
    address: Optional[str] = None
    avatarUrl: Optional[str] = None
    telegramUsername: Optional[str] = None
    createdAt: datetime.datetime
    updatedAt: datetime.datetime
    userRoles: List[UserRole]
    isVerified: bool
    isEmailNotificationsEnable: bool


class RefreshTokenResponse(BaseResponse):
    access_token: str
    user: BaseRefreshTokenResponse
