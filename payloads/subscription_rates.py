from models.base_model import BaseResponse
from models.Subscriptions.model_subscription import ModelSubscriptionResponse


class TarifList(BaseResponse):
    tarifs: list[ModelSubscriptionResponse]

    @staticmethod
    def base_tarif() -> TarifList:
        """
        содержит список тарифов доступных подписок
        """
        raw_data = {
            "tarifs": [
                {
                    "id": 1,
                    "name": "Кандидат",
                    "code": "free",
                    "isActive": True,
                    "pricePerMonth": 0,
                    "discount": 0,
                    "monthPeriod": 1,
                    "description": None,
                    "promo": None,
                    "parentId": None,
                    "roles": [{"id": 6, "name": "candidate-free", "permissions": []}],
                    "finalPrice": 0,
                },
                {
                    "id": 6,
                    "name": "Премиум на 3 месяца",
                    "code": "quarter",
                    "isActive": True,
                    "pricePerMonth": 400,
                    "discount": 10,
                    "monthPeriod": 3,
                    "description": None,
                    "promo": None,
                    "parentId": 3,
                    "roles": [{"id": 7, "name": "candidate-premium", "permissions": []}],
                    "finalPrice": 1080,
                },
                {
                    "id": 5,
                    "name": "Годовой премиум",
                    "code": "year",
                    "isActive": True,
                    "pricePerMonth": 400,
                    "discount": 26,
                    "monthPeriod": 12,
                    "description": None,
                    "promo": "Yeahub выгоднее с каждым годом",
                    "parentId": 3,
                    "roles": [{"id": 7, "name": "candidate-premium", "permissions": []}],
                    "finalPrice": 3552,
                },
                {
                    "id": 4,
                    "name": "Пробная",
                    "code": "trial",
                    "isActive": True,
                    "pricePerMonth": 0,
                    "discount": 0,
                    "monthPeriod": 1,
                    "description": None,
                    "promo": None,
                    "parentId": None,
                    "roles": [{"id": 7, "name": "candidate-premium", "permissions": []}],
                    "finalPrice": 0,
                },
                {
                    "id": 3,
                    "name": "Участник сообщества",
                    "code": "month",
                    "isActive": True,
                    "pricePerMonth": 800,
                    "discount": 50,
                    "monthPeriod": 1,
                    "description": None,
                    "promo": None,
                    "parentId": None,
                    "roles": [{"id": 7, "name": "candidate-premium", "permissions": []}],
                    "finalPrice": 400,
                },
            ]
        }
        return TarifList.model_validate(raw_data)
