from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field

from models.base_model import BaseResponse


class DataPaymentModel(BaseResponse):
    """
    Класс для валидации данных на оплату
    """

    sessionId: str = Field(..., description="Уникальный ID для оплаты")
    status: StatusModel = Field(..., description="Статус заказа")
    merchant: MerchantModel = Field(..., description="Продавец")
    terminal: TerminalModel
    templateParams: TemplateParamsModel = Field(..., description="Данные получателя")
    amount: int = Field(..., description="Цена в копейках")
    currency: int = Field(..., description="код валюты")
    paymentsSettings: PaymentsSettingsModel
    order: OrderModel = Field(..., description="Описание заказа и id заказа")
    admToggle: List[AdmToggleItem]
    pfToggle: List[PfToggleItem]
    custom: CustomModel
    dco: DcoModel
    language: str
    customer: CustomerModel = Field(..., description="Данные заказчика")


class StatusModel(BaseResponse):
    timestamp: str
    value: str


class MerchantModel(BaseResponse):
    backUrl: str
    name: str


class TerminalModel(BaseResponse):
    key: str
    paymentTypes: List[str]


class OrderModel(BaseResponse):
    description: str
    id: str


class CustomerModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str
    key: str


class DcoModel(BaseResponse):
    type: str
    value: str


# 2. Сложные вложенные структуры
class CardSettings(BaseResponse):
    allowSaveCard: bool
    showFee: bool


class PaymentsSettingsModel(BaseResponse):
    card: CardSettings


class TemplateParamsModel(BaseResponse):
    companyAddress: str
    companyName: str
    merchantPhone: str


# 3. Элементы списков (Toggle)
class AdmToggleItem(BaseResponse):
    isOn: bool
    path: str
    type: str
    value: Any  # Используем Any, так как типы в value могут меняться


class PfToggleItem(BaseResponse):
    name: str
    type: str
    value: Any


class CustomModel(BaseResponse):
    files: Any = None
    params: Any = None
    rows: Any = None
