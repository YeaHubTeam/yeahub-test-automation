from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict, Field

from models.base_model import BaseResponse  # Твой базовый класс


class RoleModel(BaseResponse):
    """
    Вспомогательный класс для поля roles
    """

    id: int
    name: str
    permissions: List[str] = Field(default_factory=list)


class SubscriptionDetailModel(BaseResponse):
    """
    Вспомогательный класс для поля subscription
    """

    id: int
    name: str
    code: str
    is_active: bool = Field(..., alias="isActive")
    price_per_month: int = Field(..., alias="pricePerMonth")
    discount: int
    month_period: int = Field(..., alias="monthPeriod")
    description: Optional[str] = None
    promo: Optional[str] = None
    parent_id: Optional[int] = Field(None, alias="parentId")
    roles: List[RoleModel]


class UserSubscriptionResponse(BaseResponse):
    """
    Класс для валидации данных подписки пользователя
    """

    id: str
    create_date: datetime = Field(..., alias="createDate")
    end_date: Optional[datetime] = Field(None, alias="endDate")
    subscription_id: int = Field(..., alias="subscriptionId")
    user_id: str = Field(..., alias="userId")
    state: str
    payment_attempts_count: int = Field(..., alias="paymentAttemptsCount")
    payment_error: Optional[str] = Field(None, alias="paymentError")
    fixed_price: Optional[int] = Field(None, alias="fixedPrice")
    subscription: SubscriptionDetailModel


class ModelErrorResponse(BaseResponse):
    """
    Класс для валидации данных об ошибке
    """

    message: str = Field(..., description="Сообщение об ошибке")
    statusCode: int = Field(..., description="Статус код")
    description: str = Field(..., description="Описание ошибки")
