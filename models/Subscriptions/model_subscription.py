from pydantic import Field

from models.base_model import BaseResponse
from models.role_model import Role


class Subscription(BaseResponse):
    """
    Класс для валидации данных подписки приходящих от сервера
    """

    id: int = Field(..., description="ID подписки")
    name: str = Field(..., description="Название подписки")
    code: str = Field(..., description="Период оплаты")
    is_active: bool = Field(..., description="Активна ли подписка")
    price_per_month: int = Field(..., description="Цена в месяц")
    discount: int = Field(..., description="Скидка")
    month_period: int = Field(..., description="Период в месяцах")
    description: str | None = Field(default=None, description="Описание подписки")
    promo: str | None = Field(default=None, description="Промо к подписке")
    parent_id: int | None = Field(default=None, description="ID родителя")
    roles: list[Role] = Field(..., description="Роли подписки")
    final_price: int | None = Field(default=None, description="Финальная цена")