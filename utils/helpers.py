from pydantic import TypeAdapter
from models.Subscriptions.model_user_subsriptions import UserSubscriptionResponse
from typing import List

class DataUtils:

    @staticmethod
    def find_item(items, condition, transform=lambda x: x):
        """
        Метод который ищет нужную строку в подписке или
        подписку целиком из списка
        :param item: Объект который перебираем
        :param condition: Условия по которым мы ищем
        :param transform: Выерезает нужную часть из нужного объекта, по умалчанию возвращает весь объект
        """
        item = next((i for i in items if condition(i)), None)
        return transform(item) if item is not None else None

    @staticmethod
    def type_adapter(model ,response):
        """
        Валидирует и преобразует входные данные в указанную модель Pydantic.

        :param model: Класс модели или тип данных (напр. List[MyModel]), к которому нужно привести ответ.
        :param response: Данные для валидации (словарь, список или JSON-объект).
        :return: Объект или список объектов валидированной модели.
        """
        adapter = TypeAdapter(model)
        validate_response = adapter.validate_python(response)
        return validate_response
