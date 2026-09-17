from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseResponse(BaseModel):
    """
    Базовая модель ответа API, к которому можно обращаться как с dict и как модель.

    Поля объявляются в snake_case; алиасы под camelCase JSON от бэкенда
    генерируются автоматически через alias_generator — ручные Field(alias=...)
    для стандартного camelCase больше не нужны.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        from_attributes=True,
        strict=False,
        alias_generator=to_camel,
    )

    # --- dict-like интерфейс ---

    def __getitem__(self, key):
        """data["field"] - получение значения по ключу"""
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(f"Key '{key}' not found")

    def __setitem__(self, key, value):
        """data["field"] = value - установка значения по ключу"""
        setattr(self, key, value)

    def __contains__(self, key):
        """'id' in data - проверка существования ключа (как в словаре)"""
        return hasattr(self, key) and getattr(self, key) is not None

    def get(self, key, default=None):
        """data.get("field")"""
        return getattr(self, key, default)

    def keys(self):
        return self.model_dump().keys()

    def values(self):
        return self.model_dump().values()

    def items(self):
        return self.model_dump().items()

    def to_dict(self):
        """Явное преобразование в словарь"""
        return self.model_dump()


class LenientResponse(BaseResponse):
    """
    Вариант BaseResponse для полей с непредсказуемой/частичной структурой от бэкенда
    (например вложенные объекты платёжных систем), где extra="forbid" будет
    постоянно ломаться на новых полях сервера.
    """

    model_config = BaseResponse.model_config | {"extra": "ignore"}