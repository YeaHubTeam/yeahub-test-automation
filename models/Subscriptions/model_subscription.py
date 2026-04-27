from pydantic import Field

from models.base_model import BaseResponse


class ModelSubscriptionResponse(BaseResponse):
    """
    Класс для валидации данных подписки приходящих от сервера
    """

    id: int = Field(..., description="ID подписки")
    name: str = Field(..., description="Навзвание подписки")
    code: str = Field(..., description="Период оплаты")
    isActive: bool = Field(..., description="Активна ли подписка")
    pricePerMonth: int = Field(..., description="Цена в месяц")
    discount: int = Field(..., description="Скидка")
    monthPeriod: int = Field(..., description="Цена в месяц")
    description: str | None = Field(default=None, description="Описание подписки")
    promo: str | None = Field(default=None, description="промо к подписке")
    parentId: int | None = Field(default=None, description="ID Родителя")
    roles: list[RoleModel] = Field(..., description="Описание роли")
    finalPrice: int = Field(..., description="Финальная цена")


class RoleModel(BaseResponse):
    """
    Вспомогательный класс для поля role
    """

    id: int
    name: str
    permissions: list[dict]
