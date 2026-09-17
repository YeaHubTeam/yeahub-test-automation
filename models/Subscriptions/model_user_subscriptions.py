from datetime import datetime

from pydantic import Field

from models.base_model import BaseResponse
from models.Subscriptions.model_subscription import Subscription


class UserSubscriptionResponse(BaseResponse):
    """
    Класс для валидации данных подписки пользователя
    """

    id: str
    create_date: datetime
    end_date: datetime | None = None
    subscription_id: int
    user_id: str
    state: str
    payment_attempts_count: int
    payment_error: str | None = None
    fixed_price: int | None = None
    subscription: Subscription
